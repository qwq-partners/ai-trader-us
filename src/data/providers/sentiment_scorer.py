"""
AI Trader US - Sentiment Scoring

Converts news sentiment into trading signal adjustments.
Used by strategies to boost or penalize scores based on news.
"""

from typing import Dict, Optional
from dataclasses import dataclass
from loguru import logger

from .news_provider import SentimentScore, CompositeNewsProvider


@dataclass
class SentimentAdjustment:
    """Score adjustment based on sentiment"""
    bonus: float = 0.0        # Points to add to strategy score (can be negative)
    confidence: float = 0.0   # 0-1 confidence in the adjustment
    reason: str = ""


class SentimentScorer:
    """Computes strategy score adjustments from news sentiment"""

    def __init__(self, news_provider: CompositeNewsProvider = None):
        self._provider = news_provider or CompositeNewsProvider()
        self._cache: Dict[str, SentimentAdjustment] = {}

    def get_adjustment(self, symbol: str) -> SentimentAdjustment:
        """Get score adjustment for a symbol based on news sentiment"""
        if symbol in self._cache:
            return self._cache[symbol]

        sentiment = self._provider.get_sentiment(symbol)
        if not sentiment:
            return SentimentAdjustment()

        adjustment = self._compute_adjustment(sentiment)
        self._cache[symbol] = adjustment
        return adjustment

    def clear_cache(self):
        """Clear cached adjustments (call at start of each day)"""
        self._cache.clear()

    def _compute_adjustment(self, sentiment: SentimentScore) -> SentimentAdjustment:
        """Compute score adjustment from sentiment data"""
        net = sentiment.net_sentiment  # -1 to +1
        buzz = sentiment.buzz
        news_score = sentiment.news_score

        # Base adjustment: net sentiment * weight
        # Strong bullish (>0.3) → up to +15 points
        # Strong bearish (<-0.3) → up to -15 points
        # Neutral → 0
        if abs(net) < 0.1:
            bonus = 0.0
            reason = "neutral"
        elif net > 0:
            bonus = min(15, net * 20)
            reason = f"bullish {sentiment.bullish_pct:.0%}"
        else:
            bonus = max(-15, net * 20)
            reason = f"bearish {sentiment.bearish_pct:.0%}"

        # Buzz multiplier: high coverage amplifies signal
        if buzz > 1.5:
            bonus *= min(1.5, buzz / 2 + 0.5)
            reason += f" buzz {buzz:.1f}x"

        # Sector comparison: above sector avg is extra bullish
        if sentiment.sector_avg_bullish > 0:
            sector_diff = sentiment.bullish_pct - sentiment.sector_avg_bullish
            if sector_diff > 0.1:
                bonus += min(5, sector_diff * 20)
                reason += f" +sector"

        # Confidence based on article count
        if sentiment.articles_count >= 10:
            confidence = 0.9
        elif sentiment.articles_count >= 5:
            confidence = 0.7
        elif sentiment.articles_count >= 2:
            confidence = 0.5
        else:
            confidence = 0.3
            bonus *= 0.5  # Low confidence → reduce impact

        return SentimentAdjustment(
            bonus=round(bonus, 1),
            confidence=confidence,
            reason=f"news: {reason} ({sentiment.articles_count} articles)",
        )
