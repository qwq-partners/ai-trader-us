"""
Run stock screener to find trading opportunities.

Usage:
  python scripts/run_screener.py                     # Top momentum (S&P 500)
  python scripts/run_screener.py --mode volume        # Volume surge stocks
  python scripts/run_screener.py --mode highs         # Near 52-week highs
  python scripts/run_screener.py --mode breakout      # 20-day breakouts
  python scripts/run_screener.py --mode all           # All results
  python scripts/run_screener.py --universe sp400     # S&P 400 midcap
  python scripts/run_screener.py --symbols AAPL,MSFT  # Custom symbols
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.screener import StockScreener, print_screen_results
from src.data.universe import UniverseManager
from src.utils.logger import setup_logger
from loguru import logger


def main():
    parser = argparse.ArgumentParser(description="Stock screener")
    parser.add_argument('--mode', type=str, default='momentum',
                        choices=['momentum', 'volume', 'highs', 'breakout', 'all'],
                        help='Screening mode')
    parser.add_argument('--universe', type=str, default='sp500',
                        choices=['sp500', 'sp400', 'full'],
                        help='Stock universe to scan')
    parser.add_argument('--symbols', type=str, default=None,
                        help='Custom comma-separated symbols')
    parser.add_argument('--limit', type=int, default=30,
                        help='Max results to display')
    parser.add_argument('--min-price', type=float, default=5.0,
                        help='Minimum stock price')
    parser.add_argument('--min-volume', type=int, default=500_000,
                        help='Minimum 20-day avg volume')
    args = parser.parse_args()

    setup_logger("WARNING")

    # Get symbols
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    else:
        universe = UniverseManager()
        if args.universe == 'full':
            symbols = universe.get_full_universe()
        elif args.universe == 'sp400':
            symbols = universe.get_universe(['sp400'])
        else:
            symbols = universe.get_sp500()

    print(f"Scanning {len(symbols)} stocks (mode: {args.mode})...")

    screener = StockScreener()
    result = screener.scan(
        symbols=symbols,
        min_price=args.min_price,
        min_avg_volume=args.min_volume,
    )

    print_screen_results(result, mode=args.mode, limit=args.limit)

    # Print summary stats
    if result.results:
        vol_surges = len(result.volume_surge)
        new_highs = len(result.new_highs)
        breakouts = len(result.breakouts)
        print(f"\nSummary: {vol_surges} vol surges | {new_highs} near 52w high | "
              f"{breakouts} breakouts")


if __name__ == "__main__":
    main()
