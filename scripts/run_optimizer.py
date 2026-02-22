"""
Run parameter optimization for trading strategies.

Usage:
  python scripts/run_optimizer.py --strategy momentum
  python scripts/run_optimizer.py --strategy momentum --no-validate
  python scripts/run_optimizer.py --strategy sepa --years 5
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import AppConfig
from src.data.providers.yfinance_provider import YFinanceProvider
from src.data.store import DataStore
from src.backtest.optimizer import ParameterOptimizer
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

# Parameter grids for each strategy
PARAM_GRIDS = {
    'momentum': {
        'min_breakout_pct': [0.1, 0.3, 0.5, 0.8, 1.0],
        'volume_surge_ratio': [1.2, 1.5, 2.0, 2.5],
        'stop_loss_pct': [2.0, 3.0, 4.0, 5.0],
        'take_profit_pct': [6.0, 8.0, 10.0, 15.0],
        'min_score': [50, 55, 60, 65],
    },
    'orb': {
        'min_or_range_pct': [0.3, 0.5, 0.8, 1.0],
        'max_or_range_pct': [2.0, 3.0, 4.0],
        'volume_confirm_ratio': [1.2, 1.5, 2.0],
        'stop_loss_pct': [1.0, 1.5, 2.0],
        'min_score': [55, 60, 65],
    },
    'vwap_bounce': {
        'min_volume_ratio': [1.2, 1.5, 2.0],
        'stop_loss_atr_mult': [0.3, 0.5, 0.8],
        'take_profit_atr_mult': [1.0, 1.5, 2.0],
        'min_score': [55, 60, 65],
    },
    'sepa': {
        'min_score': [50, 60, 70],
        'stop_loss_pct': [3.0, 5.0, 7.0],
        'take_profit_pct': [10.0, 15.0, 20.0],
        'max_holding_days': [15, 20, 30],
    },
    'earnings_drift': {
        'min_gap_pct': [3.0, 5.0, 7.0],
        'min_eps_surprise_pct': [5, 10, 15],
        'stop_loss_pct': [5.0, 8.0, 10.0],
        'max_holding_days': [10, 15, 20],
        'min_score': [60, 65, 70],
    },
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


def main():
    parser = argparse.ArgumentParser(description="Optimize strategy parameters")
    parser.add_argument('--strategy', type=str, required=True,
                        choices=list(STRATEGIES.keys()),
                        help='Strategy to optimize')
    parser.add_argument('--symbols', type=str, default=None,
                        help='Comma-separated symbols (default: top 20)')
    parser.add_argument('--years', type=int, default=3,
                        help='Years of history')
    parser.add_argument('--capital', type=float, default=100_000,
                        help='Initial capital ($)')
    parser.add_argument('--no-validate', action='store_true',
                        help='Skip walk-forward validation')
    parser.add_argument('--quick', action='store_true',
                        help='Quick mode: reduced grid (fewer combos)')
    parser.add_argument('--sort', type=str, default='composite',
                        choices=['return', 'sharpe', 'composite'],
                        help='Sort results by')
    parser.add_argument('--workers', type=int, default=None,
                        help='Number of parallel workers (default: auto)')
    args = parser.parse_args()

    setup_logger("WARNING")

    # Symbols
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    else:
        symbols = [
            'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'TSLA',
            'AVGO', 'JPM', 'V', 'UNH', 'MA', 'HD', 'CRM', 'NFLX',
            'AMD', 'COST', 'ABBV', 'MRK', 'PEP',
        ]

    end = date.today()
    start = end - timedelta(days=args.years * 365)

    logger.info(f"Loading data for {len(symbols)} symbols...")
    data = load_data(symbols, start, end)
    logger.info(f"Loaded {len(data)} symbols")

    if not data:
        print("Error: No data loaded")
        return

    # Get parameter grid
    param_grid = PARAM_GRIDS.get(args.strategy, {})
    if args.quick:
        # Reduce grid: take every other value
        param_grid = {k: v[::2] if len(v) > 2 else v for k, v in param_grid.items()}

    # Count combinations
    from itertools import product
    n_combos = 1
    for v in param_grid.values():
        n_combos *= len(v)
    print(f"\nStrategy: {args.strategy}")
    print(f"Parameter grid: {n_combos} combinations")
    print(f"Symbols: {len(data)}, Period: {start} ~ {end}")

    # Load config
    app_config = AppConfig.load()
    optimizer = ParameterOptimizer(config=app_config.trading)

    result = optimizer.optimize(
        strategy_cls=STRATEGIES[args.strategy],
        data=data,
        param_grid=param_grid,
        initial_capital=args.capital,
        start_date=start,
        end_date=end,
        validate=not args.no_validate,
        sort_by=args.sort,
        n_workers=args.workers,
    )

    # Print best config for copy-paste
    best = result.best_by_composite
    if best:
        print(f"\nBest config for config/default.yml:")
        print(f"  strategies:")
        print(f"    {args.strategy}:")
        for k, v in best.params.items():
            print(f"      {k}: {v}")


if __name__ == "__main__":
    main()
