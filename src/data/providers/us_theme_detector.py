"""
AI Trader US - US Theme Detector

미국 시장 테마 탐지기.
Finnhub 뉴스를 수집하여 키워드 매칭으로 활성 테마를 탐지한다.
LLM 없이 키워드 매칭만으로 동작 (예산 절약).
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional

from loguru import logger

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

_ET = ZoneInfo("America/New_York")


# 테마별 관련 종목 매핑
US_THEME_STOCKS = {
    "AI/Semiconductors": {
        "keywords": ["ai", "artificial intelligence", "semiconductor", "chip", "gpu", "nvidia", "amd",
                      "data center", "machine learning", "deep learning", "generative ai", "llm"],
        "stocks": ["NVDA", "AMD", "AVGO", "INTC", "QCOM", "MU", "TSM", "MRVL", "ARM", "SMCI"],
    },
    "Clean Energy": {
        "keywords": ["solar", "wind", "renewable", "clean energy", "green energy", "ev charging",
                      "hydrogen", "carbon", "climate"],
        "stocks": ["ENPH", "FSLR", "NEE", "PLUG", "BE", "RUN", "SEDG"],
    },
    "EV/Auto": {
        "keywords": ["electric vehicle", "ev", "tesla", "autonomous", "self-driving", "battery",
                      "lithium", "charging"],
        "stocks": ["TSLA", "RIVN", "LCID", "GM", "F", "NIO", "XPEV", "LI"],
    },
    "Biotech/Pharma": {
        "keywords": ["biotech", "pharma", "fda", "drug", "clinical trial", "vaccine",
                      "gene therapy", "obesity", "glp-1", "cancer treatment"],
        "stocks": ["LLY", "MRNA", "PFE", "AMGN", "GILD", "REGN", "VRTX", "BMY"],
    },
    "Financials": {
        "keywords": ["bank", "banking", "interest rate", "fed", "federal reserve", "yield",
                      "credit", "lending", "fintech"],
        "stocks": ["JPM", "BAC", "GS", "MS", "WFC", "C", "BLK", "SCHW"],
    },
    "Defense": {
        "keywords": ["defense", "military", "pentagon", "weapon", "missile", "drone",
                      "geopolitical", "war", "nato", "arms"],
        "stocks": ["LMT", "RTX", "NOC", "GD", "BA", "HII", "LHX"],
    },
    "Cloud/SaaS": {
        "keywords": ["cloud", "saas", "aws", "azure", "enterprise software", "subscription",
                      "digital transformation"],
        "stocks": ["MSFT", "AMZN", "GOOGL", "CRM", "SNOW", "NOW", "DDOG", "NET"],
    },
    "Cybersecurity": {
        "keywords": ["cybersecurity", "cyber", "security breach", "hack", "ransomware",
                      "zero trust", "firewall", "endpoint"],
        "stocks": ["CRWD", "PANW", "ZS", "FTNT", "S", "OKTA"],
    },
    "Crypto/Blockchain": {
        "keywords": ["crypto", "bitcoin", "ethereum", "blockchain", "defi", "nft",
                      "digital asset", "coinbase", "mining"],
        "stocks": ["COIN", "MSTR", "MARA", "RIOT", "SQ"],
    },
    "Nuclear/Uranium": {
        "keywords": ["nuclear", "uranium", "reactor", "small modular reactor", "smr",
                      "nuclear energy", "fusion"],
        "stocks": ["CCJ", "LEU", "SMR", "NNE", "OKLO"],
    },
    "Retail/Consumer": {
        "keywords": ["retail", "consumer", "spending", "e-commerce", "online shopping",
                      "holiday", "earnings beat"],
        "stocks": ["AMZN", "WMT", "COST", "TGT", "HD", "LOW", "NKE"],
    },
}

# 뉴스 수집 대상 대형주 (general_news 보충)
_TOP_TICKERS = ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN"]


@dataclass
class USThemeInfo:
    """탐지된 US 테마 정보"""
    name: str
    keywords: List[str] = field(default_factory=list)
    related_stocks: List[str] = field(default_factory=list)
    news_count: int = 0
    score: float = 0.0
    detected_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    news_headlines: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "keywords": self.keywords[:5],
            "related_stocks": self.related_stocks,
            "news_count": self.news_count,
            "score": round(self.score, 1),
            "detected_at": self.detected_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "news_headlines": self.news_headlines[:5],
        }


class USThemeDetector:
    """미국 시장 테마 탐지기 (키워드 매칭 기반)"""

    def __init__(self, finnhub_api_key: str):
        try:
            import finnhub
            self._client = finnhub.Client(api_key=finnhub_api_key)
        except ImportError:
            logger.warning("finnhub-python 미설치 — 테마 탐지 비활성")
            self._client = None
        except Exception as e:
            logger.warning(f"Finnhub 클라이언트 초기화 실패: {e}")
            self._client = None

        self._themes: Dict[str, USThemeInfo] = {}
        self._last_detect: Optional[datetime] = None
        self._detect_interval = 1800  # 30분

    async def detect_themes(self, force: bool = False) -> List[USThemeInfo]:
        """테마 탐지 실행 (30분 주기)"""
        if not self._client:
            return []

        now = datetime.now()
        if not force and self._last_detect:
            elapsed = (now - self._last_detect).total_seconds()
            if elapsed < self._detect_interval:
                return list(self._themes.values())

        try:
            articles = await self._collect_news()
            if not articles:
                logger.debug("[US테마] 수집된 뉴스 없음")
                return list(self._themes.values())

            self._keyword_theme_match(articles)
            self._last_detect = now

            active = [t for t in self._themes.values() if t.score > 0]
            logger.info(
                f"[US테마] 탐지 완료 — 뉴스 {len(articles)}건, "
                f"활성 테마 {len(active)}개"
            )
            return active

        except Exception as e:
            logger.error(f"[US테마] 탐지 오류: {e}")
            return list(self._themes.values())

    async def _collect_news(self) -> List[dict]:
        """Finnhub에서 뉴스 수집 (general + 대형주 company_news)"""
        articles = []

        # 1. 일반 뉴스 30건
        try:
            general = await asyncio.to_thread(
                self._client.general_news, "general", min_id=0
            )
            if general:
                articles.extend(general[:30])
        except Exception as e:
            logger.debug(f"[US테마] general_news 오류: {e}")

        await asyncio.sleep(0.5)  # rate limit

        # 2. 대형주 company_news 각 5건 (ET 기준 날짜)
        today_et = datetime.now(_ET).date()
        from_date = (today_et - timedelta(days=2)).isoformat()
        to_date = today_et.isoformat()

        for ticker in _TOP_TICKERS:
            try:
                news = await asyncio.to_thread(
                    self._client.company_news,
                    ticker, _from=from_date, to=to_date,
                )
                if news:
                    articles.extend(news[:5])
                await asyncio.sleep(0.5)  # rate limit
            except Exception as e:
                logger.debug(f"[US테마] {ticker} company_news 오류: {e}")

        return articles

    def _keyword_theme_match(self, articles: List[dict]):
        """헤드라인+요약에서 테마 키워드 매칭"""
        now = datetime.now()

        # 테마별 매칭 카운트 초기화
        theme_hits: Dict[str, List[str]] = {name: [] for name in US_THEME_STOCKS}

        for article in articles:
            headline = article.get("headline", "") or ""
            summary = article.get("summary", "") or ""
            text = (headline + " " + summary).lower()

            for theme_name, info in US_THEME_STOCKS.items():
                for keyword in info["keywords"]:
                    if keyword in text:
                        if headline and headline not in theme_hits[theme_name]:
                            theme_hits[theme_name].append(headline)
                        break  # 테마당 기사 1회 매칭

        # 테마 정보 갱신
        for theme_name, headlines in theme_hits.items():
            news_count = len(headlines)
            info = US_THEME_STOCKS[theme_name]

            if news_count >= 2:
                # 활성 테마
                score = min(100, news_count * 15 + 20)
                self._themes[theme_name] = USThemeInfo(
                    name=theme_name,
                    keywords=info["keywords"][:5],
                    related_stocks=info["stocks"],
                    news_count=news_count,
                    score=score,
                    detected_at=self._themes[theme_name].detected_at
                    if theme_name in self._themes else now,
                    last_updated=now,
                    news_headlines=headlines[:5],
                )
            elif theme_name in self._themes:
                # 기존 테마의 뉴스가 줄었으면 점수 감소
                existing = self._themes[theme_name]
                existing.score = max(0, existing.score - 10)
                existing.last_updated = now

        # 점수 0 이하 테마 일괄 삭제 (순회 중 삭제 방지)
        expired = [k for k, v in self._themes.items() if v.score <= 0]
        for k in expired:
            del self._themes[k]

    def to_dict_list(self) -> List[dict]:
        """API 응답용 직렬화 (score 내림차순)"""
        active = [t for t in self._themes.values() if t.score > 0]
        active.sort(key=lambda t: t.score, reverse=True)
        return [t.to_dict() for t in active]
