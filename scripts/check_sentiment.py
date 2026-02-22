"""
Check news sentiment for symbols.
Usage: python scripts/check_sentiment.py AAPL NVDA TSLA
       python scripts/check_sentiment.py --top 10  (top 10 S&P 500 by buzz)

Requires FINNHUB_API_KEY environment variable.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from src.data.providers.news_provider import FinnhubNewsProvider, SentimentScore
from src.data.providers.sentiment_scorer import SentimentScorer
from src.utils.logger import setup_logger
from loguru import logger


def print_sentiment(symbol: str, score: SentimentScore, adjustment=None):
    """Pretty print sentiment data"""
    net = score.net_sentiment
    bar_len = 20
    bull_bars = int(score.bullish_pct * bar_len)
    bear_bars = bar_len - bull_bars

    sentiment_bar = f"[{'#' * bear_bars}|{'#' * bull_bars}]"
    direction = "BULL" if net > 0.1 else "BEAR" if net < -0.1 else "NEUT"

    print(f"  {symbol:6s} {direction:4s} {sentiment_bar} "
          f"bull={score.bullish_pct:.0%} bear={score.bearish_pct:.0%} "
          f"buzz={score.buzz:.1f}x articles={score.articles_count:3d} "
          f"score={score.news_score:.2f}", end="")

    if adjustment and adjustment.bonus != 0:
        print(f" | adj={adjustment.bonus:+.0f}pts", end="")

    print()


def main():
    parser = argparse.ArgumentParser(description="Check news sentiment")
    parser.add_argument('symbols', nargs='*', default=[],
                        help='Symbols to check')
    parser.add_argument('--top', type=int, default=0,
                        help='Check top N S&P 500 stocks')
    parser.add_argument('--news', action='store_true',
                        help='Show recent headlines')
    args = parser.parse_args()

    setup_logger("WARNING")

    provider = FinnhubNewsProvider()
    if not provider._client:
        print("Error: Set FINNHUB_API_KEY environment variable")
        print("  export FINNHUB_API_KEY=your_api_key_here")
        print("  Get free API key at: https://finnhub.io/register")
        return

    scorer = SentimentScorer(provider)

    symbols = args.symbols
    if args.top > 0:
        symbols = [
            'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'TSLA',
            'AVGO', 'JPM', 'V', 'UNH', 'MA', 'HD', 'CRM', 'NFLX',
            'AMD', 'COST', 'ABBV', 'MRK', 'PEP',
        ][:args.top]

    if not symbols:
        print("Usage: python scripts/check_sentiment.py AAPL NVDA TSLA")
        return

    print(f"\nNews Sentiment Report ({len(symbols)} symbols)")
    print("=" * 80)

    for symbol in symbols:
        score = provider.get_sentiment(symbol)
        if score:
            adj = scorer.get_adjustment(symbol)
            print_sentiment(symbol, score, adj)
        else:
            print(f"  {symbol:6s} -- No sentiment data available")

        if args.news:
            articles = provider.get_news(symbol, days=2)
            for a in articles[:3]:
                print(f"         {a.published:%m/%d %H:%M} | {a.source:15s} | {a.headline[:60]}")
            if articles:
                print()

        time.sleep(0.5)  # Rate limit respect

    print("=" * 80)


if __name__ == "__main__":
    main()
