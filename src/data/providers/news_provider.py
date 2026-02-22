"""
AI Trader US - News/Sentiment Provider

Abstract interface and implementations for news sentiment data.
Supports Finnhub (primary) and Polygon.io (secondary).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
import os
from loguru import logger


@dataclass
class NewsArticle:
    """Single news article"""
    headline: str
    source: str
    published: datetime
    summary: str = ""
    url: str = ""
    tickers: List[str] = field(default_factory=list)
    sentiment: float = 0.0  # -1.0 (bearish) to +1.0 (bullish)
    relevance: float = 0.0  # 0.0 to 1.0


@dataclass
class SentimentScore:
    """Aggregated sentiment for a symbol"""
    symbol: str
    bullish_pct: float = 0.5  # 0.0 to 1.0
    bearish_pct: float = 0.5
    news_score: float = 0.0   # overall score (0-1)
    buzz: float = 0.0         # articles volume vs average
    articles_count: int = 0
    sector_avg_bullish: float = 0.5

    @property
    def net_sentiment(self) -> float:
        """Net sentiment: -1.0 (very bearish) to +1.0 (very bullish)"""
        return self.bullish_pct - self.bearish_pct

    @property
    def sentiment_impact(self) -> float:
        """Impact score (0-100) combining sentiment and buzz"""
        sentiment_strength = abs(self.net_sentiment) * 50
        buzz_boost = min(30, self.buzz * 10)
        news_boost = self.news_score * 20
        return min(100, sentiment_strength + buzz_boost + news_boost)


# Keyword sentiment analysis for free-tier fallback
_BULLISH_WORDS = {
    'beat', 'beats', 'upgrade', 'upgraded', 'bullish', 'buy', 'outperform',
    'surges', 'surge', 'soars', 'soar', 'rally', 'rallies', 'gains', 'gain',
    'jumps', 'jump', 'rises', 'rise', 'strong', 'breakout', 'record', 'high',
    'boom', 'profit', 'profits', 'growth', 'growing', 'upside', 'positive',
    'optimistic', 'opportunity', 'momentum', 'beat expectations', 'surprise',
    'exceeds', 'exceeded', 'acceleration', 'innovative', 'breakthrough',
    'dividend', 'buyback', 'expansion', 'demand', 'revenue growth',
    'overweight', 'reiterate buy', 'price target raised', 'ai',
}

_BEARISH_WORDS = {
    'miss', 'misses', 'downgrade', 'downgraded', 'bearish', 'sell',
    'underperform', 'drops', 'drop', 'falls', 'fall', 'plunges', 'plunge',
    'declines', 'decline', 'crash', 'crashes', 'tumbles', 'tumble',
    'weak', 'warning', 'warns', 'risk', 'risks', 'loss', 'losses',
    'negative', 'pessimistic', 'concern', 'concerns', 'slowdown',
    'recession', 'layoffs', 'layoff', 'cut', 'cuts', 'tariff', 'tariffs',
    'investigation', 'lawsuit', 'fine', 'penalty', 'recall',
    'underweight', 'price target cut', 'downside', 'overvalued',
}


def _analyze_headline_sentiment(text: str) -> float:
    """Simple keyword-based sentiment: -1.0 to +1.0"""
    text_lower = text.lower()
    words = set(text_lower.split())

    bull_score = sum(1 for w in _BULLISH_WORDS if w in text_lower)
    bear_score = sum(1 for w in _BEARISH_WORDS if w in text_lower)

    total = bull_score + bear_score
    if total == 0:
        return 0.0

    return (bull_score - bear_score) / total


class NewsProvider(ABC):
    """Abstract news/sentiment provider"""

    @abstractmethod
    def get_news(self, symbol: str, days: int = 3) -> List[NewsArticle]:
        """Get recent news articles for a symbol"""
        pass

    @abstractmethod
    def get_sentiment(self, symbol: str) -> Optional[SentimentScore]:
        """Get aggregated sentiment score for a symbol"""
        pass


class FinnhubNewsProvider(NewsProvider):
    """Finnhub news + sentiment provider (60 calls/min free)"""

    def __init__(self, api_key: str = None):
        try:
            import finnhub
        except ImportError:
            raise ImportError("finnhub-python not installed: pip install finnhub-python")

        self._api_key = api_key or os.environ.get('FINNHUB_API_KEY', '')
        if not self._api_key:
            logger.warning("FINNHUB_API_KEY not set - news features disabled")
            self._client = None
            return

        self._client = finnhub.Client(api_key=self._api_key)
        self._sentiment_cache: Dict[str, tuple] = {}  # {symbol: (timestamp, SentimentScore)}
        self._cache_ttl = 300  # 5 min cache

    def get_news(self, symbol: str, days: int = 3) -> List[NewsArticle]:
        """Get company news from Finnhub"""
        if not self._client:
            return []

        try:
            end = date.today()
            start = end - timedelta(days=days)
            raw = self._client.company_news(
                symbol, _from=start.isoformat(), to=end.isoformat()
            )

            articles = []
            for item in raw[:20]:  # Limit to 20 articles
                articles.append(NewsArticle(
                    headline=item.get('headline', ''),
                    source=item.get('source', ''),
                    published=datetime.fromtimestamp(item.get('datetime', 0)),
                    summary=item.get('summary', ''),
                    url=item.get('url', ''),
                    tickers=[symbol],
                    relevance=1.0,
                ))

            return articles
        except Exception as e:
            logger.debug(f"Finnhub news error for {symbol}: {e}")
            return []

    def get_sentiment(self, symbol: str) -> Optional[SentimentScore]:
        """Get sentiment - try API first, fallback to keyword analysis"""
        if not self._client:
            return None

        # Check cache
        now = datetime.now().timestamp()
        if symbol in self._sentiment_cache:
            cached_time, cached_score = self._sentiment_cache[symbol]
            if now - cached_time < self._cache_ttl:
                return cached_score

        # Try paid API endpoint first
        try:
            raw = self._client.news_sentiment(symbol)
            if raw and 'sentiment' in raw:
                score = SentimentScore(
                    symbol=symbol,
                    bullish_pct=raw['sentiment'].get('bullishPercent', 0.5),
                    bearish_pct=raw['sentiment'].get('bearishPercent', 0.5),
                    news_score=raw.get('companyNewsScore', 0),
                    buzz=raw.get('buzz', {}).get('buzz', 0),
                    articles_count=raw.get('buzz', {}).get('articlesInLastWeek', 0),
                    sector_avg_bullish=raw.get('sectorAverageBullishPercent', 0.5),
                )
                self._sentiment_cache[symbol] = (now, score)
                return score
        except Exception:
            pass  # Fallback to keyword analysis

        # Fallback: analyze headlines with keyword sentiment
        return self._keyword_sentiment(symbol)

    def _keyword_sentiment(self, symbol: str) -> Optional[SentimentScore]:
        """Compute sentiment from news headlines using keyword analysis"""
        articles = self.get_news(symbol, days=7)
        if not articles:
            return None

        sentiments = []
        for article in articles:
            text = (article.headline + " " + article.summary).lower()
            sent = _analyze_headline_sentiment(text)
            sentiments.append(sent)

        if not sentiments:
            return None

        avg_sent = sum(sentiments) / len(sentiments)
        bullish_count = sum(1 for s in sentiments if s > 0.1)
        bearish_count = sum(1 for s in sentiments if s < -0.1)
        total = len(sentiments)

        bullish_pct = bullish_count / total if total > 0 else 0.5
        bearish_pct = bearish_count / total if total > 0 else 0.5
        neutral_pct = 1 - bullish_pct - bearish_pct

        score = SentimentScore(
            symbol=symbol,
            bullish_pct=bullish_pct,
            bearish_pct=bearish_pct,
            news_score=abs(avg_sent),
            buzz=total / 7.0,  # Articles per day
            articles_count=total,
        )

        now = datetime.now().timestamp()
        self._sentiment_cache[symbol] = (now, score)
        return score

    def get_bulk_sentiment(self, symbols: List[str]) -> Dict[str, SentimentScore]:
        """Get sentiment for multiple symbols"""
        results = {}
        for symbol in symbols:
            score = self.get_sentiment(symbol)
            if score:
                results[symbol] = score
        return results


class PolygonNewsProvider(NewsProvider):
    """Polygon.io news provider (5 calls/min free, per-article sentiment)"""

    def __init__(self, api_key: str = None):
        self._api_key = api_key or os.environ.get('POLYGON_API_KEY', '')
        if not self._api_key:
            logger.warning("POLYGON_API_KEY not set - Polygon news disabled")

    def get_news(self, symbol: str, days: int = 3) -> List[NewsArticle]:
        """Get news with per-article sentiment from Polygon"""
        if not self._api_key:
            return []

        try:
            import requests
            end = date.today()
            start = end - timedelta(days=days)

            url = "https://api.polygon.io/v2/reference/news"
            params = {
                'ticker': symbol,
                'published_utc.gte': start.isoformat(),
                'published_utc.lte': end.isoformat(),
                'limit': 20,
                'apiKey': self._api_key,
            }

            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            articles = []
            for item in data.get('results', []):
                # Extract sentiment from insights
                sentiment = 0.0
                for insight in item.get('insights', []):
                    if insight.get('ticker') == symbol:
                        sent = insight.get('sentiment', 'neutral')
                        if sent == 'positive':
                            sentiment = 0.5
                        elif sent == 'negative':
                            sentiment = -0.5

                articles.append(NewsArticle(
                    headline=item.get('title', ''),
                    source=item.get('publisher', {}).get('name', ''),
                    published=datetime.fromisoformat(
                        item.get('published_utc', '').replace('Z', '+00:00')
                    ) if item.get('published_utc') else datetime.now(),
                    summary=item.get('description', ''),
                    url=item.get('article_url', ''),
                    tickers=item.get('tickers', []),
                    sentiment=sentiment,
                    relevance=1.0,
                ))

            return articles
        except Exception as e:
            logger.debug(f"Polygon news error for {symbol}: {e}")
            return []

    def get_sentiment(self, symbol: str) -> Optional[SentimentScore]:
        """Aggregate sentiment from recent articles"""
        articles = self.get_news(symbol, days=7)
        if not articles:
            return None

        sentiments = [a.sentiment for a in articles if a.sentiment != 0]
        if not sentiments:
            return None

        avg_sent = sum(sentiments) / len(sentiments)
        bullish = sum(1 for s in sentiments if s > 0) / len(sentiments)

        return SentimentScore(
            symbol=symbol,
            bullish_pct=bullish,
            bearish_pct=1 - bullish,
            news_score=abs(avg_sent),
            articles_count=len(articles),
        )


class CompositeNewsProvider(NewsProvider):
    """Combines multiple news providers with fallback"""

    def __init__(self, providers: List[NewsProvider] = None):
        if providers:
            self._providers = providers
        else:
            # Auto-detect available providers
            self._providers = []
            try:
                fp = FinnhubNewsProvider()
                if fp._client:
                    self._providers.append(fp)
            except Exception:
                pass

            try:
                pp = PolygonNewsProvider()
                if pp._api_key:
                    self._providers.append(pp)
            except Exception:
                pass

        if not self._providers:
            logger.warning("No news providers configured")

    def get_news(self, symbol: str, days: int = 3) -> List[NewsArticle]:
        """Get news from all providers, deduplicated"""
        all_articles = []
        seen_headlines = set()

        for provider in self._providers:
            try:
                articles = provider.get_news(symbol, days)
                for article in articles:
                    key = article.headline[:80]
                    if key not in seen_headlines:
                        seen_headlines.add(key)
                        all_articles.append(article)
            except Exception as e:
                logger.debug(f"Provider error: {e}")

        all_articles.sort(key=lambda a: a.published, reverse=True)
        return all_articles

    def get_sentiment(self, symbol: str) -> Optional[SentimentScore]:
        """Get sentiment from first available provider"""
        for provider in self._providers:
            try:
                score = provider.get_sentiment(symbol)
                if score:
                    return score
            except Exception:
                continue
        return None
