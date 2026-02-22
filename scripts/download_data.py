"""
Download historical data for backtesting.
Usage: python scripts/download_data.py [--symbols AAPL,MSFT] [--years 3]
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.providers.yfinance_provider import YFinanceProvider
from src.data.store import DataStore
from src.utils.logger import setup_logger
from loguru import logger


def main():
    parser = argparse.ArgumentParser(description="Download price data")
    parser.add_argument('--symbols', type=str, default=None,
                        help='Comma-separated symbols (default: S&P 500)')
    parser.add_argument('--years', type=int, default=3,
                        help='Years of history (default: 3)')
    parser.add_argument('--interval', type=str, default='daily',
                        choices=['daily', '5m'],
                        help='Data interval')
    args = parser.parse_args()

    setup_logger("INFO")

    provider = YFinanceProvider()
    store = DataStore()

    # Get symbols
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    else:
        logger.info("Loading S&P 500 universe...")
        symbols = provider.get_universe("sp500")

    end = date.today()
    start = end - timedelta(days=args.years * 365)

    logger.info(f"Downloading {len(symbols)} symbols | {start} ~ {end} | {args.interval}")

    success = 0
    failed = 0

    for i, symbol in enumerate(symbols):
        try:
            if args.interval == 'daily':
                # Check existing data for incremental download
                last_date = store.get_last_date(symbol, 'daily')
                dl_start = last_date + timedelta(days=1) if last_date else start

                if dl_start >= end:
                    success += 1
                    continue

                df = provider.get_daily_bars(symbol, dl_start, end)
                if not df.empty:
                    store.update(symbol, df, 'daily')
                    success += 1
                else:
                    failed += 1
            else:
                df = provider.get_intraday_bars(symbol, interval=args.interval)
                if not df.empty:
                    store.save(symbol, df, args.interval)
                    success += 1
                else:
                    failed += 1

            if (i + 1) % 50 == 0:
                logger.info(f"Progress: {i + 1}/{len(symbols)} (success={success}, failed={failed})")

        except Exception as e:
            logger.warning(f"Failed {symbol}: {e}")
            failed += 1

    logger.info(f"Done: {success} success, {failed} failed out of {len(symbols)}")


if __name__ == "__main__":
    main()
