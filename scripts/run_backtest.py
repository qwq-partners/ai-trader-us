"""
Run backtest for US trading strategies.
Usage: python scripts/run_backtest.py [--strategy momentum] [--symbols AAPL,MSFT]
       python scripts/run_backtest.py --strategy all  (multi-strategy)
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import AppConfig
from src.data.providers.yfinance_provider import YFinanceProvider
from src.data.store import DataStore
from src.backtest.engine import BacktestEngine
from src.backtest.metrics import PerformanceMetrics
from src.backtest.report import BacktestReport
from src.strategies.momentum import MomentumBreakoutStrategy
from src.strategies.orb import ORBStrategy
from src.strategies.vwap_bounce import VWAPBounceStrategy
from src.strategies.sepa import SEPATrendStrategy
from src.strategies.earnings_drift import EarningsDriftStrategy
from src.utils.logger import setup_logger
from loguru import logger

STRATEGIES = {
    'momentum': MomentumBreakoutStrategy,
    'orb': ORBStrategy,
    'vwap_bounce': VWAPBounceStrategy,
    'sepa': SEPATrendStrategy,
    'earnings_drift': EarningsDriftStrategy,
}


def load_data(symbols, start, end):
    """Load price data with caching"""
    provider = YFinanceProvider()
    store = DataStore()

    data = {}
    for symbol in symbols:
        df = store.load(symbol, 'daily')
        if df is None or df.empty:
            df = provider.get_daily_bars(symbol, start, end)
            if not df.empty:
                store.save(symbol, df, 'daily')

        if df is not None and not df.empty:
            df = df[(df.index >= str(start)) & (df.index <= str(end))]
            if len(df) >= 50:
                data[symbol] = df

    return data


def print_results(result, title, start, end, n_symbols, capital):
    """Print backtest results"""
    print("\n" + "=" * 70)
    print(f"BACKTEST RESULTS: {title}")
    print("=" * 70)
    print(f"Period:          {start} ~ {end}")
    print(f"Symbols:         {n_symbols}")
    print(f"Initial Capital: ${capital:,.0f}")
    print(f"Final Equity:    ${float(result.portfolio.total_equity):,.0f}")
    print(f"Total Return:    {result.total_return_pct:+.1f}%")
    print(f"Max Drawdown:    {result.max_drawdown_pct:.1f}%")
    print(f"Sharpe Ratio:    {result.sharpe_ratio:.2f}")
    print(f"Total Trades:    {result.total_trades}")
    print(f"Win Rate:        {result.win_rate:.0f}%")
    print(f"Profit Factor:   {result.profit_factor:.2f}")
    print(f"Avg Trade PnL:   {result.avg_trade_pnl_pct:+.2f}%")
    print("=" * 70)

    if result.trades:
        # Strategy breakdown
        strat_trades = {}
        for t in result.trades:
            s = t.strategy or 'unknown'
            if s not in strat_trades:
                strat_trades[s] = []
            strat_trades[s].append(t)

        if len(strat_trades) > 1:
            print("\nStrategy Breakdown:")
            print(f"  {'Strategy':<20s} {'Trades':>6s} {'Win%':>6s} {'PF':>6s} {'Avg PnL':>8s} {'Total $':>10s}")
            print("  " + "-" * 58)
            for sname, trades in sorted(strat_trades.items()):
                wins = sum(1 for t in trades if t.is_win)
                wr = wins / len(trades) * 100 if trades else 0
                total_win = sum(float(t.pnl) for t in trades if t.is_win)
                total_loss = abs(sum(float(t.pnl) for t in trades if not t.is_win))
                pf = total_win / total_loss if total_loss > 0 else float('inf')
                avg_pnl = sum(t.pnl_pct for t in trades) / len(trades)
                total_pnl = sum(float(t.pnl) for t in trades)
                print(f"  {sname:<20s} {len(trades):>6d} {wr:>5.0f}% {pf:>6.2f} {avg_pnl:>+7.2f}% ${total_pnl:>+9,.0f}")

        # Top trades
        winners = sorted(result.trades, key=lambda t: t.pnl_pct, reverse=True)[:5]
        losers = sorted(result.trades, key=lambda t: t.pnl_pct)[:5]

        print("\nTop 5 Winners:")
        for t in winners:
            print(f"  {t.symbol:6s} {t.pnl_pct:+6.1f}% | ${float(t.pnl):+8,.0f} | {t.strategy:<15s} | {t.reason}")

        print("\nTop 5 Losers:")
        for t in losers:
            print(f"  {t.symbol:6s} {t.pnl_pct:+6.1f}% | ${float(t.pnl):+8,.0f} | {t.strategy:<15s} | {t.reason}")


def main():
    parser = argparse.ArgumentParser(description="Run backtest")
    parser.add_argument('--strategy', type=str, default='momentum',
                        choices=list(STRATEGIES.keys()) + ['all'],
                        help='Strategy to test (use "all" for multi-strategy)')
    parser.add_argument('--symbols', type=str, default=None,
                        help='Comma-separated symbols (default: top 50 S&P 500)')
    parser.add_argument('--years', type=int, default=3,
                        help='Years of history')
    parser.add_argument('--capital', type=float, default=100_000,
                        help='Initial capital ($)')
    parser.add_argument('--config', type=str, default=None,
                        help='Config YAML path')
    parser.add_argument('--report', action='store_true',
                        help='Generate HTML report')
    args = parser.parse_args()

    setup_logger("INFO")

    # Load config
    app_config = AppConfig.load(args.config)

    # Symbols
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    else:
        symbols = [
            'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'TSLA',
            'AVGO', 'JPM', 'V', 'UNH', 'MA', 'HD', 'CRM', 'NFLX',
            'AMD', 'COST', 'ABBV', 'MRK', 'PEP', 'KO', 'TMO', 'WMT',
            'BAC', 'CVX', 'LLY', 'PG', 'XOM', 'ORCL', 'ADBE',
            'NOW', 'QCOM', 'CSCO', 'TXN', 'ISRG', 'AMAT', 'INTU',
            'PANW', 'BKNG', 'ADP', 'LRCX', 'SYK', 'KLAC', 'MELI',
            'SNPS', 'CDNS', 'REGN', 'MDLZ', 'VRTX', 'MU',
        ]

    end = date.today()
    start = end - timedelta(days=args.years * 365)

    logger.info(f"Loading data for {len(symbols)} symbols ({start} ~ {end})...")
    data = load_data(symbols, start, end)
    logger.info(f"Loaded {len(data)}/{len(symbols)} symbols with sufficient data")

    if not data:
        logger.error("No data loaded. Run download_data.py first.")
        return

    engine = BacktestEngine(config=app_config.trading)

    if args.strategy == 'all':
        # Multi-strategy mode
        strategy_list = []
        for sname, cls in STRATEGIES.items():
            cfg = app_config.get('strategies', sname) or {}
            strategy_list.append(cls(config=cfg))

        logger.info(f"Multi-strategy: {', '.join(s.name for s in strategy_list)}")

        result = engine.run(
            strategies=strategy_list,
            data=data,
            initial_capital=args.capital,
            start_date=start,
            end_date=end,
        )

        title = "ALL STRATEGIES (Combined)"
        print_results(result, title, start, end, len(data), args.capital)
    else:
        # Single strategy mode
        strategy_config = app_config.get('strategies', args.strategy) or {}
        strategy_cls = STRATEGIES[args.strategy]
        strategy = strategy_cls(config=strategy_config)

        result = engine.run(
            strategy=strategy,
            data=data,
            initial_capital=args.capital,
            start_date=start,
            end_date=end,
        )

        title = strategy.name
        print_results(result, title, start, end, len(data), args.capital)

    # Generate HTML report
    if args.report:
        metrics = PerformanceMetrics.compute(
            result.trades, result.equity_curve,
            result.daily_returns, args.capital
        )
        report_path = BacktestReport.generate(
            result.equity_curve, result.trades, metrics,
            title=f"{title} Backtest"
        )
        logger.info(f"Report saved: {report_path}")


if __name__ == "__main__":
    main()
