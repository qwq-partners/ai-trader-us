"""
AI Trader US - Finviz Elite Data Provider

Finviz Elite API로 기관 수급 / 펀더멘털 / 센티멘트 데이터 수집.
StockScreener 점수에 최대 +45pt 보너스를 부여해 순수 기술지표 한계를 보완.

수집 데이터:
  - Institutional Transactions (기관 순매수 변화%)   → 최대 +20pt
  - Insider Transactions (내부자 순매수%)            → 최대 +10pt
  - EPS Growth QQ (분기 실적 성장률)                → 최대 +10pt
  - Analyst Recommendation (애널리스트 컨센서스)     → 최대 +5pt
  - Short Float (공매도 비율%)                       → 메타데이터
  - 기타: Inst Own%, ROE, ROA, Sales QQ 등

API: https://elite.finviz.com/export.ashx
캐시: ~/.cache/ai_trader_us/finviz_YYYY-MM-DD.json (1일 TTL)
"""

import asyncio
import csv
import io
import json
import os
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from loguru import logger


CACHE_DIR = Path.home() / ".cache" / "ai_trader_us"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Finviz Elite API 컬럼 ID
# 1=Ticker, 22=EPS_QQ, 23=Sales_QQ, 27=InsiderTrans, 28=InstOwn, 29=InstTrans,
# 30=ShortFloat, 31=ShortRatio, 32=ROA, 33=ROE, 34=ROIC, 57=RSI,
# 60=AnalystRecom, 61=AvgVol
COLUMNS = "1,22,23,27,28,29,30,31,32,33,34,57,60,61"

ELITE_URL = "https://elite.finviz.com/export.ashx"
BATCH_SIZE = 50  # t= 파라미터 티커 배치 크기


def _parse_pct(value: str) -> float:
    """'3.45%' → 3.45, '-1.2%' → -1.2, '' → 0.0"""
    if not value:
        return 0.0
    try:
        return float(value.replace("%", "").strip())
    except ValueError:
        return 0.0


def _parse_float(value: str) -> float:
    """'1.31' → 1.31, '' → 0.0"""
    if not value:
        return 0.0
    try:
        return float(value.strip())
    except ValueError:
        return 0.0


class FinvizProvider:
    """
    Finviz Elite 데이터 프로바이더.

    사용 패턴:
        provider = FinvizProvider(api_token)
        await provider.refresh(universe_symbols)   # 하루 1회
        bonus = provider.get_bonus_score("AAPL")   # 스크리너에서 호출
        meta  = provider.get_meta("AAPL")          # 메타데이터 조회
    """

    def __init__(self, api_token: str = ""):
        self._token = api_token or os.getenv("FINVIZ_API_TOKEN", "")
        self._cache: Dict[str, dict] = {}          # symbol → raw dict
        self._cache_date: Optional[date] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._timeout = aiohttp.ClientTimeout(total=20)

        if not self._token:
            logger.warning("[Finviz] API 토큰 없음 — 스크리너 보너스 비활성화")

    # ── 세션 ──────────────────────────────────────────────────────────────────

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout,
                headers={"User-Agent": "Mozilla/5.0"},
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # ── 캐시 ──────────────────────────────────────────────────────────────────

    def _cache_path(self, d: date) -> Path:
        return CACHE_DIR / f"finviz_{d.isoformat()}.json"

    def _load_cache(self, d: date) -> Optional[Dict[str, dict]]:
        path = self._cache_path(d)
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                pass
        return None

    def _save_cache(self, d: date, data: Dict[str, dict]):
        try:
            self._cache_path(d).write_text(json.dumps(data))
        except Exception as e:
            logger.debug(f"[Finviz] 캐시 저장 실패: {e}")

    @property
    def is_ready(self) -> bool:
        return bool(self._cache) and bool(self._token)

    # ── API 호출 ──────────────────────────────────────────────────────────────

    async def _fetch_by_filter(self, filter_str: str) -> List[dict]:
        """
        Finviz 인덱스 필터로 일괄 조회 (예: idx_sp500).
        Returns: [{Ticker: ..., EPS..., ...}, ...]
        """
        if not self._token:
            return []
        session = await self._get_session()
        params = {
            "v": "152",
            "c": COLUMNS,
            "auth": self._token,
            "f": filter_str,
        }
        try:
            async with session.get(ELITE_URL, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"[Finviz] HTTP {resp.status} (filter={filter_str})")
                    return []
                content = await resp.text()
                reader = csv.DictReader(io.StringIO(content))
                return list(reader)
        except Exception as e:
            logger.error(f"[Finviz] 필터 조회 실패 ({filter_str}): {e}")
            return []

    async def _fetch_by_tickers(self, tickers: List[str]) -> List[dict]:
        """
        티커 목록으로 직접 조회 (t= 파라미터, 배치 50개).
        Returns: [{Ticker: ..., ...}, ...]
        """
        if not self._token or not tickers:
            return []
        session = await self._get_session()
        params = {
            "v": "152",
            "c": COLUMNS,
            "auth": self._token,
            "t": ",".join(tickers),
        }
        try:
            async with session.get(ELITE_URL, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"[Finviz] HTTP {resp.status} (batch {len(tickers)}종목)")
                    return []
                content = await resp.text()
                reader = csv.DictReader(io.StringIO(content))
                return list(reader)
        except Exception as e:
            logger.error(f"[Finviz] 배치 조회 실패: {e}")
            return []

    # ── 갱신 ──────────────────────────────────────────────────────────────────

    async def refresh(self, symbols: List[str], today: date = None) -> bool:
        """
        유니버스 전체 데이터 갱신 (하루 1회 권장).

        S&P500 (503종목): f=idx_sp500 단 1회 호출
        나머지 (S&P400 등): t=batch 50종목씩 배치 호출

        Returns:
            True if refreshed, False if using cached data
        """
        if today is None:
            today = date.today()

        if not self._token:
            return False

        # 오늘 캐시 있으면 로드 후 완료
        if self._cache_date == today and self._cache:
            return False  # 이미 최신

        cached = self._load_cache(today)
        if cached:
            self._cache = cached
            self._cache_date = today
            logger.info(f"[Finviz] 캐시 로드: {len(self._cache)}종목 ({today})")
            return False

        # ── 신규 API 조회 ──────────────────────────────────────────────────
        logger.info(f"[Finviz] 데이터 갱신 시작 ({len(symbols)}종목)...")
        new_data: Dict[str, dict] = {}

        # Step 1: S&P500 전체 (인덱스 필터 — 1회 API 호출)
        sp500_rows = await self._fetch_by_filter("idx_sp500")
        sp500_symbols = set()
        for row in sp500_rows:
            sym = row.get("Ticker", "").strip()
            if sym:
                new_data[sym] = row
                sp500_symbols.add(sym)
        logger.info(f"[Finviz] S&P500 로드: {len(sp500_symbols)}종목")

        # Step 2: 나머지 종목 (S&P400 등) 배치 조회
        remaining = [s for s in symbols if s not in sp500_symbols]
        if remaining:
            batches = [remaining[i:i + BATCH_SIZE]
                       for i in range(0, len(remaining), BATCH_SIZE)]
            for i, batch in enumerate(batches):
                rows = await self._fetch_by_tickers(batch)
                for row in rows:
                    sym = row.get("Ticker", "").strip()
                    if sym:
                        new_data[sym] = row
                await asyncio.sleep(0.3)  # 레이트 리밋 방지
            logger.info(
                f"[Finviz] S&P400 로드: {len(remaining)}종목 "
                f"({len(batches)}배치)"
            )

        if new_data:
            self._cache = new_data
            self._cache_date = today
            self._save_cache(today, new_data)
            logger.info(f"[Finviz] 전체 갱신 완료: {len(new_data)}종목 → 캐시 저장")
            return True
        else:
            logger.warning("[Finviz] 데이터 없음 — 갱신 실패")
            return False

    # ── 점수 계산 ─────────────────────────────────────────────────────────────

    def get_bonus_score(self, symbol: str) -> float:
        """
        StockScreener 기본 점수에 더할 Finviz 보너스 계산.

        최대 +45pt (기관 수급 +20 / 내부자 +10 / 실적 +10 / 애널리스트 +5)
        페널티 최대 -15pt (기관 이탈 -10 / 애널리스트 매도 -5)

        Returns:
            float: 보너스 점수 (음수 가능)
        """
        data = self._cache.get(symbol)
        if not data:
            return 0.0

        bonus = 0.0

        # ① 기관 순매수 변화 (가장 중요)
        inst_trans = _parse_pct(data.get("Institutional Transactions", ""))
        if inst_trans >= 5:
            bonus += 20   # 기관 대규모 매집
        elif inst_trans >= 2:
            bonus += 12   # 기관 꾸준한 매수
        elif inst_trans >= 0.5:
            bonus += 6    # 소폭 매집
        elif inst_trans <= -5:
            bonus -= 10   # 기관 대규모 이탈
        elif inst_trans <= -2:
            bonus -= 5    # 기관 이탈 중

        # ② 내부자 순매수 (경영진 자사주 매수 = 강한 신호)
        insider_trans = _parse_pct(data.get("Insider Transactions", ""))
        if insider_trans >= 5:
            bonus += 10   # 내부자 대량 매수
        elif insider_trans >= 1:
            bonus += 5    # 내부자 매수
        # 내부자 매도는 유동성 목적이 많아 페널티 없음

        # ③ 분기 EPS 성장률 (실적 모멘텀)
        eps_qq = _parse_pct(data.get("EPS Growth Quarter Over Quarter", ""))
        if eps_qq >= 50:
            bonus += 10   # 폭발적 실적 성장
        elif eps_qq >= 20:
            bonus += 7    # 강한 성장
        elif eps_qq >= 0:
            bonus += 3    # 성장 중

        # ④ 애널리스트 컨센서스 (1=Strong Buy ~ 5=Strong Sell)
        recom = _parse_float(data.get("Analyst Recom", ""))
        if 0 < recom <= 1.5:
            bonus += 5    # 강력 매수 의견
        elif recom <= 2.5:
            bonus += 2    # 매수 의견
        elif recom >= 4.0:
            bonus -= 5    # 매도 의견

        return bonus

    def get_meta(self, symbol: str) -> dict:
        """
        스크리닝 결과에 첨부할 메타데이터 반환.

        Returns:
            {
              inst_own: 기관 보유 비율%,
              inst_trans: 기관 순매수 변화%,
              insider_trans: 내부자 순매수%,
              short_float: 공매도 비율%,
              eps_qq: 분기 EPS 성장%,
              roe: ROE%,
              analyst_recom: 애널리스트 점수,
              bonus: 추가 점수
            }
        """
        data = self._cache.get(symbol, {})
        if not data:
            return {}

        return {
            "inst_own":      _parse_pct(data.get("Institutional Ownership", "")),
            "inst_trans":    _parse_pct(data.get("Institutional Transactions", "")),
            "insider_trans": _parse_pct(data.get("Insider Transactions", "")),
            "short_float":   _parse_pct(data.get("Short Float", "")),
            "short_ratio":   _parse_float(data.get("Short Ratio", "")),
            "eps_qq":        _parse_pct(data.get("EPS Growth Quarter Over Quarter", "")),
            "sales_qq":      _parse_pct(data.get("Sales Growth Quarter Over Quarter", "")),
            "roe":           _parse_pct(data.get("Return on Equity", "")),
            "roa":           _parse_pct(data.get("Return on Assets", "")),
            "analyst_recom": _parse_float(data.get("Analyst Recom", "")),
            "bonus":         self.get_bonus_score(symbol),
        }

    def coverage(self) -> int:
        """현재 캐시 종목 수"""
        return len(self._cache)
