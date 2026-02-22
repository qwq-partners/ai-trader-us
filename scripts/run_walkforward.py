"""
Run Walk-Forward analysis for strategy robustness testing.
Usage: python scripts/run_walkforward.py --strategy sepa --years 3
       python scripts/run_walkforward.py --strategy all --train 6 --test 3
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import AppConfig
from src.data.providers.yfinance_provider import YFinanceProvider
from src.data.store import DataStore
from src.backtest.walk_forward import WalkForwardAnalyzer
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
    parser = argparse.ArgumentParser(description="Walk-Forward Analysis")
    parser.add_argument('--strategy', type=str, default='sepa',
                        choices=list(STRATEGIES.keys()) + ['all'],
                        help='Strategy to analyze')
    parser.add_argument('--symbols', type=str, default=None,
                        help='Comma-separated symbols')
    parser.add_argument('--years', type=int, default=3,
                        help='Years of data')
    parser.add_argument('--train', type=int, default=6,
                        help='Training window (months)')
    parser.add_argument('--test', type=int, default=3,
                        help='Testing window (months)')
    parser.add_argument('--step', type=int, default=2,
                        help='Step size (months)')
    parser.add_argument('--capital', type=float, default=100_000,
                        help='Initial capital ($)')
    parser.add_argument('--config', type=str, default=None,
                        help='Config YAML path')
    args = parser.parse_args()

    setup_logger("INFO")

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

    # Load data
    logger.info(f"Loading data for {len(symbols)} symbols ({start} ~ {end})...")
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

    logger.info(f"Loaded {len(data)}/{len(symbols)} symbols")

    if not data:
        logger.error("No data loaded")
        return

    # Create strategy/strategies
    analyzer = WalkForwardAnalyzer(config=app_config.trading)

    if args.strategy == 'all':
        strategy_list = []
        for sname, cls in STRATEGIES.items():
            cfg = app_config.get('strategies', sname) or {}
            strategy_list.append(cls(config=cfg))

        result = analyzer.analyze(
            strategy=None,
            strategies=strategy_list,
            data=data,
            train_months=args.train,
            test_months=args.test,
            step_months=args.step,
            initial_capital=args.capital,
        )
    else:
        cfg = app_config.get('strategies', args.strategy) or {}
        strategy = STRATEGIES[args.strategy](config=cfg)

        result = analyzer.analyze(
            strategy=strategy,
            data=data,
            train_months=args.train,
            test_months=args.test,
            step_months=args.step,
            initial_capital=args.capital,
        )


if __name__ == "__main__":
    main()
