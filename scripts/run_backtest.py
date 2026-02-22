"""
Run backtest for US trading strategies.
Usage: python scripts/run_backtest.py [--strategy momentum] [--symbols AAPL,MSFT]
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


def main():
    parser = argparse.ArgumentParser(description="Run backtest")
    parser.add_argument('--strategy', type=str, default='momentum',
                        choices=list(STRATEGIES.keys()),
                        help='Strategy to test')
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
    strategy_config = app_config.get('strategies', args.strategy) or {}

    # Create strategy
    strategy_cls = STRATEGIES[args.strategy]
    strategy = strategy_cls(config=strategy_config)

    logger.info(f"Strategy: {strategy.name} | Capital: ${args.capital:,.0f}")

    # Load data
    provider = YFinanceProvider()
    store = DataStore()

    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    else:
        # Default: top 50 most liquid S&P 500 stocks
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

    data = {}
    for symbol in symbols:
        # Try cache first
        df = store.load(symbol, 'daily')
        if df is None or df.empty:
            df = provider.get_daily_bars(symbol, start, end)
            if not df.empty:
                store.save(symbol, df, 'daily')

        if df is not None and not df.empty:
            # Filter date range
            df = df[(df.index >= str(start)) & (df.index <= str(end))]
            if len(df) >= 50:  # Need minimum history
                data[symbol] = df

    logger.info(f"Loaded {len(data)}/{len(symbols)} symbols with sufficient data")

    if not data:
        logger.error("No data loaded. Run download_data.py first.")
        return

    # Run backtest
    engine = BacktestEngine(config=app_config.trading)
    result = engine.run(
        strategy=strategy,
        data=data,
        initial_capital=args.capital,
        start_date=start,
        end_date=end,
    )

    # Print results
    print("\n" + "=" * 60)
    print(f"BACKTEST RESULTS: {strategy.name}")
    print("=" * 60)
    print(f"Period:          {start} ~ {end}")
    print(f"Symbols:         {len(data)}")
    print(f"Initial Capital: ${args.capital:,.0f}")
    print(f"Final Equity:    ${float(result.portfolio.total_equity):,.0f}")
    print(f"Total Return:    {result.total_return_pct:+.1f}%")
    print(f"Max Drawdown:    {result.max_drawdown_pct:.1f}%")
    print(f"Sharpe Ratio:    {result.sharpe_ratio:.2f}")
    print(f"Total Trades:    {result.total_trades}")
    print(f"Win Rate:        {result.win_rate:.0f}%")
    print(f"Profit Factor:   {result.profit_factor:.2f}")
    print(f"Avg Trade PnL:   {result.avg_trade_pnl_pct:+.2f}%")
    print("=" * 60)

    # Top trades
    if result.trades:
        winners = sorted(result.trades, key=lambda t: t.pnl_pct, reverse=True)[:5]
        losers = sorted(result.trades, key=lambda t: t.pnl_pct)[:5]

        print("\nTop 5 Winners:")
        for t in winners:
            print(f"  {t.symbol:6s} {t.pnl_pct:+6.1f}% | ${float(t.pnl):+8,.0f} | {t.reason}")

        print("\nTop 5 Losers:")
        for t in losers:
            print(f"  {t.symbol:6s} {t.pnl_pct:+6.1f}% | ${float(t.pnl):+8,.0f} | {t.reason}")

    # Generate HTML report
    if args.report:
        from src.backtest.metrics import PerformanceMetrics as PM
        metrics = PM.compute(result.trades, result.equity_curve,
                            result.daily_returns, args.capital)
        report_path = BacktestReport.generate(
            result.equity_curve, result.trades, metrics,
            title=f"{strategy.name} Backtest"
        )
        logger.info(f"Report saved: {report_path}")


if __name__ == "__main__":
    main()
