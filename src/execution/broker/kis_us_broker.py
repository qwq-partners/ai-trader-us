"""
AI Trader US - KIS 해외주식 브로커

KIS Open API를 사용하여 미국 주식 주문을 실행합니다.
v2 kis_broker.py의 HTTP 패턴 기반.

지원 기능:
- 시장가/지정가 매수/매도
- 주문 취소
- 잔고 조회
- 현재가 조회
- 체결 내역 조회

거래소 코드: NASD (NASDAQ), NYSE, AMEX
"""

from __future__ import annotations

import asyncio
import collections
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any

import aiohttp
from loguru import logger

from ...utils.kis_auth import get_token_manager


# 거래소 코드 매핑
EXCHANGE_MAP = {
    "NASDAQ": "NASD",
    "NMS": "NASD",
    "NGM": "NASD",
    "NASD": "NASD",
    "NYSE": "NYSE",
    "NYQ": "NYSE",
    "AMEX": "AMEX",
    "ASE": "AMEX",
    "PCX": "AMEX",  # NYSE Arca
}


@dataclass
class KISUSConfig:
    """KIS 해외주식 API 설정"""
    app_key: str = ""
    app_secret: str = ""
    account_no: str = ""
    account_product_cd: str = "01"
    env: str = "prod"
    base_url: str = field(default="")
    timeout_seconds: int = 15

    def __post_init__(self):
        if not self.base_url:
            if self.env == "prod":
                self.base_url = "https://openapi.koreainvestment.com:9443"
            else:
                self.base_url = "https://openapivts.koreainvestment.com:29443"

    @classmethod
    def from_env(cls) -> "KISUSConfig":
        return cls(
            app_key=os.getenv("KIS_APPKEY", "") or os.getenv("KIS_APP_KEY", ""),
            app_secret=os.getenv("KIS_APPSECRET", "") or os.getenv("KIS_SECRET_KEY", ""),
            account_no=os.getenv("KIS_CANO", ""),
            account_product_cd=os.getenv("KIS_ACNT_PRDT_CD", "01"),
            env=os.getenv("KIS_ENV", "prod"),
        )


class KISUSBroker:
    """
    KIS 해외주식 브로커

    미국 주식(NASDAQ, NYSE, AMEX) 주문 실행.
    """

    def __init__(self, config: Optional[KISUSConfig] = None):
        self.config = config or KISUSConfig.from_env()
        self._session: Optional[aiohttp.ClientSession] = None
        self._token: Optional[str] = None
        self._token_manager = get_token_manager()

        # Rate limiter (초당 18건)
        self._rate_limit_lock = asyncio.Lock()
        self._api_call_times: collections.deque = collections.deque(maxlen=20)
        self._max_rps = 18

        # 검증
        if not self.config.app_key or not self.config.app_secret:
            raise ValueError("KIS_APPKEY와 KIS_APPSECRET이 설정되지 않았습니다.")
        if not self.config.account_no:
            raise ValueError("KIS_CANO(계좌번호)가 설정되지 않았습니다.")

        logger.info(
            f"KISUSBroker 초기화: env={self.config.env}, "
            f"account=****{self.config.account_no[-4:]}"
        )

    # ============================================================
    # TR ID (실전/모의 분기)
    # ============================================================

    def _tr(self, prod_id: str, dev_id: str) -> str:
        return prod_id if self.config.env == "prod" else dev_id

    @property
    def _tr_buy(self) -> str:
        return self._tr("TTTT1002U", "VTTT1002U")

    @property
    def _tr_sell(self) -> str:
        return self._tr("TTTT1006U", "VTTT1006U")

    @property
    def _tr_cancel(self) -> str:
        return self._tr("TTTT1004U", "VTTT1004U")

    @property
    def _tr_balance(self) -> str:
        return self._tr("CTRP6504R", "VTRP6504R")

    @property
    def _tr_quote(self) -> str:
        return "HHDFS00000300"

    @property
    def _tr_ccld(self) -> str:
        return self._tr("TTTS3035R", "VTTS3035R")

    # ============================================================
    # 연결 관리
    # ============================================================

    async def connect(self) -> bool:
        try:
            if not self._session or self._session.closed:
                timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
                self._session = aiohttp.ClientSession(timeout=timeout)

            if not await self._ensure_token():
                logger.error("KIS 토큰 발급 실패")
                return False

            logger.info("KIS US 브로커 연결 완료")
            return True
        except Exception as e:
            logger.exception(f"KIS US 브로커 연결 실패: {e}")
            return False

    async def disconnect(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        logger.info("KIS US 브로커 연결 해제")

    @property
    def is_connected(self) -> bool:
        if self._session is None or self._session.closed:
            return False
        return self._token is not None and self._token_manager._is_token_valid()

    # ============================================================
    # 주문
    # ============================================================

    async def submit_buy_order(self, symbol: str, exchange: str = "NASD",
                               qty: int = 0, price: float = 0) -> dict:
        """
        매수 주문.

        Args:
            symbol: 티커 (e.g., AAPL)
            exchange: NASD, NYSE, AMEX
            qty: 수량
            price: 가격 (0이면 시장가)
        """
        return await self._submit_order(symbol, exchange, qty, price, self._tr_buy, "매수")

    async def submit_sell_order(self, symbol: str, exchange: str = "NASD",
                                qty: int = 0, price: float = 0) -> dict:
        """매도 주문."""
        return await self._submit_order(symbol, exchange, qty, price, self._tr_sell, "매도")

    async def _submit_order(self, symbol: str, exchange: str, qty: int,
                            price: float, tr_id: str, side_name: str) -> dict:
        if qty <= 0:
            return {"success": False, "message": "수량은 1 이상이어야 합니다"}

        # KIS 해외주식 주문 구분:
        # ORD_DVSN="00" (지정가), OVRS_ORD_UNPR="0"이면 시장가로 처리됨
        ord_dvsn = "00"
        ord_price = f"{price:.2f}" if price > 0 else "0"

        body = {
            "CANO": self.config.account_no,
            "ACNT_PRDT_CD": self.config.account_product_cd,
            "OVRS_EXCG_CD": exchange,
            "PDNO": symbol,
            "ORD_QTY": str(qty),
            "OVRS_ORD_UNPR": ord_price,
            "ORD_SVR_DVSN_CD": "0",
            "ORD_DVSN": ord_dvsn,
        }

        hashkey = await self._get_hashkey(body)
        extra_headers = {"hashkey": hashkey} if hashkey else {}

        url = f"{self.config.base_url}/uapi/overseas-stock/v1/trading/order"
        data = await self._api_post(url, tr_id, body, extra_headers)

        rt_cd = data.get("rt_cd", "-1")
        if rt_cd == "0":
            output = data.get("output", {})
            order_no = output.get("ODNO", "")
            logger.info(f"[{side_name}] {symbol} {qty}주 주문 성공 (주문번호: {order_no})")
            return {
                "success": True,
                "order_no": order_no,
                "symbol": symbol,
                "qty": qty,
                "price": price,
                "message": data.get("msg1", ""),
            }
        else:
            msg = data.get("msg1", "알 수 없는 오류")
            logger.error(f"[{side_name}] {symbol} {qty}주 주문 실패: {msg}")
            return {"success": False, "message": msg}

    async def cancel_order(self, order_no: str, exchange: str = "NASD",
                           symbol: str = "", qty: int = 0) -> dict:
        """주문 취소"""
        body = {
            "CANO": self.config.account_no,
            "ACNT_PRDT_CD": self.config.account_product_cd,
            "OVRS_EXCG_CD": exchange,
            "PDNO": symbol,
            "ORGN_ODNO": order_no,
            "RVSE_CNCL_DVSN_CD": "02",  # 02=취소
            "ORD_QTY": str(qty),
            "OVRS_ORD_UNPR": "0",
            "ORD_SVR_DVSN_CD": "0",
        }

        hashkey = await self._get_hashkey(body)
        extra_headers = {"hashkey": hashkey} if hashkey else {}

        url = f"{self.config.base_url}/uapi/overseas-stock/v1/trading/order-rvsecncl"
        data = await self._api_post(url, self._tr_cancel, body, extra_headers)

        rt_cd = data.get("rt_cd", "-1")
        if rt_cd == "0":
            logger.info(f"[취소] 주문 {order_no} 취소 성공")
            return {"success": True, "order_no": order_no}
        else:
            msg = data.get("msg1", "알 수 없는 오류")
            logger.error(f"[취소] 주문 {order_no} 취소 실패: {msg}")
            return {"success": False, "message": msg}

    # ============================================================
    # 조회
    # ============================================================

    async def get_positions(self) -> List[dict]:
        """
        해외주식 잔고 조회.

        Returns:
            [{symbol, qty, avg_price, current_price, pnl, pnl_pct, exchange, name}]
        """
        url = f"{self.config.base_url}/uapi/overseas-stock/v1/trading/inquire-present-balance"
        params = {
            "CANO": self.config.account_no,
            "ACNT_PRDT_CD": self.config.account_product_cd,
            "WCRC_FRCR_DVSN_CD": "02",  # 02=원화
            "NATN_CD": "840",            # 미국
            "TR_MKET_CD": "00",          # 전체
            "INQR_DVSN_CD": "00",        # 전체
        }

        data = await self._api_get(url, self._tr_balance, params)
        if data.get("rt_cd") != "0":
            logger.error(f"잔고 조회 실패: {data.get('msg1', '')}")
            return []

        positions = []
        for item in data.get("output1", []):
            qty = int(item.get("CBLC_QTY", "0") or "0")
            if qty <= 0:
                continue

            avg_price = float(item.get("PCH_AMT", "0") or "0")
            current_price = float(item.get("OVRS_NOW_PRIC1", "0") or "0")
            pnl = float(item.get("FRCR_EVLU_PFLS_AMT", "0") or "0")
            pnl_pct = float(item.get("EVLU_PFLS_RT1", "0") or "0")

            positions.append({
                "symbol": item.get("OVRS_PDNO", "").strip(),
                "name": item.get("OVRS_ITEM_NAME", "").strip(),
                "qty": qty,
                "avg_price": avg_price,
                "current_price": current_price,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "exchange": item.get("OVRS_EXCG_CD", "NASD"),
            })

        return positions

    async def get_balance(self) -> dict:
        """
        잔고 + 계좌 정보를 한번에 조회 (API 1회 호출).

        Returns:
            {positions: [...], account: {total_equity, available_cash, ...}}
        """
        url = f"{self.config.base_url}/uapi/overseas-stock/v1/trading/inquire-present-balance"
        params = {
            "CANO": self.config.account_no,
            "ACNT_PRDT_CD": self.config.account_product_cd,
            "WCRC_FRCR_DVSN_CD": "02",
            "NATN_CD": "840",
            "TR_MKET_CD": "00",
            "INQR_DVSN_CD": "00",
        }

        data = await self._api_get(url, self._tr_balance, params)
        if data.get("rt_cd") != "0":
            logger.error(f"잔고 조회 실패: {data.get('msg1', '')}")
            return {}

        # 포지션 파싱
        positions = []
        for item in data.get("output1", []):
            qty = int(item.get("CBLC_QTY", "0") or "0")
            if qty <= 0:
                continue
            positions.append({
                "symbol": item.get("OVRS_PDNO", "").strip(),
                "name": item.get("OVRS_ITEM_NAME", "").strip(),
                "qty": qty,
                "avg_price": float(item.get("PCH_AMT", "0") or "0"),
                "current_price": float(item.get("OVRS_NOW_PRIC1", "0") or "0"),
                "pnl": float(item.get("FRCR_EVLU_PFLS_AMT", "0") or "0"),
                "pnl_pct": float(item.get("EVLU_PFLS_RT1", "0") or "0"),
                "exchange": item.get("OVRS_EXCG_CD", "NASD"),
            })

        # 계좌 요약 파싱
        output3 = data.get("output3", {})
        if isinstance(output3, list):
            output3 = output3[0] if output3 else {}

        account = {
            "total_equity": float(output3.get("FRCR_DNCL_AMT_2", "0") or "0"),
            "available_cash": float(output3.get("FRCR_DRWG_PSBL_AMT_1", "0") or "0"),
            "total_pnl": float(output3.get("OVRS_TOT_PFLS", "0") or "0"),
            "total_pnl_pct": float(output3.get("TOT_EVLU_PFLS_RT", "0") or "0"),
        }

        return {"positions": positions, "account": account}

    async def get_account(self) -> dict:
        """
        계좌 요약 조회.

        Returns:
            {total_equity, available_cash, total_pnl, total_pnl_pct}
        """
        url = f"{self.config.base_url}/uapi/overseas-stock/v1/trading/inquire-present-balance"
        params = {
            "CANO": self.config.account_no,
            "ACNT_PRDT_CD": self.config.account_product_cd,
            "WCRC_FRCR_DVSN_CD": "02",
            "NATN_CD": "840",
            "TR_MKET_CD": "00",
            "INQR_DVSN_CD": "00",
        }

        data = await self._api_get(url, self._tr_balance, params)
        if data.get("rt_cd") != "0":
            logger.error(f"계좌 조회 실패: {data.get('msg1', '')}")
            return {}

        # output3: 계좌 전체 요약
        output3 = data.get("output3", {})
        if isinstance(output3, list):
            output3 = output3[0] if output3 else {}

        return {
            "total_equity": float(output3.get("FRCR_DNCL_AMT_2", "0") or "0"),
            "available_cash": float(output3.get("FRCR_DRWG_PSBL_AMT_1", "0") or "0"),
            "total_pnl": float(output3.get("OVRS_TOT_PFLS", "0") or "0"),
            "total_pnl_pct": float(output3.get("TOT_EVLU_PFLS_RT", "0") or "0"),
        }

    async def get_quote(self, symbol: str, exchange: str = "NASD") -> dict:
        """
        해외주식 현재가 조회.

        Returns:
            {price, change, change_pct, volume, high, low, open}
        """
        url = f"{self.config.base_url}/uapi/overseas-price/v1/quotations/price"
        params = {
            "AUTH": "",
            "EXCD": exchange,
            "SYMB": symbol,
        }

        data = await self._api_get(url, self._tr_quote, params)
        if data.get("rt_cd") != "0":
            logger.error(f"현재가 조회 실패 ({symbol}): {data.get('msg1', '')}")
            return {"symbol": symbol, "price": 0}

        output = data.get("output", {})
        return {
            "symbol": symbol,
            "price": float(output.get("last", "0") or "0"),
            "change": float(output.get("diff", "0") or "0"),
            "change_pct": float(output.get("rate", "0") or "0"),
            "volume": int(output.get("tvol", "0") or "0"),
            "high": float(output.get("high", "0") or "0"),
            "low": float(output.get("low", "0") or "0"),
            "open": float(output.get("open", "0") or "0"),
        }

    async def get_order_history(self, start_date: str = None,
                                end_date: str = None) -> List[dict]:
        """
        체결 내역 조회.

        Args:
            start_date: YYYYMMDD (기본: 오늘)
            end_date: YYYYMMDD (기본: 오늘)

        Returns:
            [{order_no, symbol, side, qty, price, filled_qty, filled_price, status, time}]
        """
        today = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = today
        if not end_date:
            end_date = today

        url = f"{self.config.base_url}/uapi/overseas-stock/v1/trading/inquire-daily-ccld"
        params = {
            "CANO": self.config.account_no,
            "ACNT_PRDT_CD": self.config.account_product_cd,
            "PDNO": "",
            "ORD_STRT_DT": start_date,
            "ORD_END_DT": end_date,
            "SLL_BUY_DVSN": "00",   # 00=전체
            "CCLD_NCCS_DVSN": "00",  # 00=전체
            "OVRS_EXCG_CD": "",       # 빈값=전체 거래소
            "SORT_SQN": "DS",       # 내림차순
            "ORD_DT": "",
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "CTX_AREA_NK200": "",
            "CTX_AREA_FK200": "",
        }

        data = await self._api_get(url, self._tr_ccld, params)
        if data.get("rt_cd") != "0":
            logger.error(f"체결 내역 조회 실패: {data.get('msg1', '')}")
            return []

        orders = []
        for item in data.get("output1", []):
            order_no = item.get("ODNO", "").strip()
            if not order_no:
                continue

            filled_qty = int(item.get("FT_CCLD_QTY", "0") or "0")
            ord_qty = int(item.get("FT_ORD_QTY", "0") or "0")

            # 상태 판정
            if filled_qty >= ord_qty and ord_qty > 0:
                status = "filled"
            elif filled_qty > 0:
                status = "partial"
            else:
                status = "pending"

            sll_buy = item.get("SLL_BUY_DVSN_CD", "")
            side = "sell" if sll_buy == "01" else "buy"

            orders.append({
                "order_no": order_no,
                "symbol": item.get("OVRS_PDNO", "").strip(),
                "side": side,
                "qty": ord_qty,
                "price": float(item.get("FT_ORD_UNPR3", "0") or "0"),
                "filled_qty": filled_qty,
                "filled_price": float(item.get("FT_CCLD_UNPR3", "0") or "0"),
                "status": status,
                "time": item.get("ORD_TMD", ""),
                "exchange": item.get("OVRS_EXCG_CD", ""),
            })

        return orders

    # ============================================================
    # Rate Limiter
    # ============================================================

    async def _rate_limit(self):
        while True:
            async with self._rate_limit_lock:
                now = time.monotonic()
                while self._api_call_times and now - self._api_call_times[0] > 1.0:
                    self._api_call_times.popleft()
                if len(self._api_call_times) < self._max_rps:
                    self._api_call_times.append(time.monotonic())
                    return
                wait_time = 1.0 - (now - self._api_call_times[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)

    # ============================================================
    # HTTP 헬퍼
    # ============================================================

    def _get_headers(self, tr_id: str) -> Dict[str, str]:
        return {
            "Content-Type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self._token}",
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
            "tr_id": tr_id,
        }

    def _is_token_error(self, data: dict) -> bool:
        msg_cd = str(data.get("msg_cd", ""))
        return msg_cd in ("EGW00123", "EGW00121")

    async def _ensure_token(self) -> bool:
        for attempt in range(3):
            self._token = await self._token_manager.get_access_token()
            if self._token is not None:
                return True
            delay = 2 ** attempt
            logger.warning(f"[토큰] 발급 실패 (시도 {attempt + 1}/3), {delay}초 후 재시도")
            await asyncio.sleep(delay)
        logger.error("[토큰] 3회 재시도 후에도 토큰 발급 실패")
        return False

    async def _api_get(self, url: str, tr_id: str, params: dict) -> dict:
        if not self._session or self._session.closed:
            if not await self.connect():
                return {"rt_cd": "-1", "msg1": "세션 연결 실패"}
        if self._token is None:
            if not await self._ensure_token():
                return {"rt_cd": "-1", "msg1": "토큰 발급 실패"}

        for attempt in range(3):
            try:
                await self._rate_limit()
                headers = self._get_headers(tr_id)
                async with self._session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 401 and attempt < 2:
                        logger.warning("[토큰] 401 응답, 토큰 갱신 시도")
                        await self._ensure_token()
                        continue
                    if resp.status in (429, 500, 502, 503) and attempt < 2:
                        wait = 2 ** attempt
                        logger.warning(f"[API] HTTP {resp.status}, {attempt+1}회 재시도 ({wait}초 대기)")
                        await asyncio.sleep(wait)
                        continue
                    try:
                        data = await resp.json()
                    except Exception:
                        return {"rt_cd": "-1", "msg1": f"JSON 파싱 실패 (HTTP {resp.status})"}
                    if self._is_token_error(data) and attempt < 2:
                        await self._ensure_token()
                        continue
                    return data
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < 2:
                    wait = 2 ** attempt
                    logger.warning(f"[API] 네트워크 오류, {attempt+1}회 재시도: {e}")
                    await asyncio.sleep(wait)
                    continue
                logger.error(f"[API] GET 실패 (3회 시도): {e}")
                return {"rt_cd": "-1", "msg1": f"네트워크 오류: {e}"}
        return {"rt_cd": "-1", "msg1": "API 호출 실패 (최대 재시도 초과)"}

    async def _api_post(self, url: str, tr_id: str, json_data: dict,
                        extra_headers: Optional[dict] = None) -> dict:
        if not self._session or self._session.closed:
            if not await self.connect():
                return {"rt_cd": "-1", "msg1": "세션 연결 실패"}
        if self._token is None:
            if not await self._ensure_token():
                return {"rt_cd": "-1", "msg1": "토큰 발급 실패"}

        for attempt in range(3):
            try:
                await self._rate_limit()
                headers = self._get_headers(tr_id)
                if extra_headers:
                    headers.update(extra_headers)
                async with self._session.post(url, headers=headers, json=json_data) as resp:
                    if resp.status == 401 and attempt < 2:
                        await self._ensure_token()
                        continue
                    if resp.status in (429, 500, 502, 503) and attempt < 2:
                        wait = 2 ** attempt
                        logger.warning(f"[API] HTTP {resp.status}, {attempt+1}회 재시도 ({wait}초 대기)")
                        await asyncio.sleep(wait)
                        continue
                    try:
                        data = await resp.json()
                    except Exception:
                        return {"rt_cd": "-1", "msg1": f"JSON 파싱 실패 (HTTP {resp.status})"}
                    if self._is_token_error(data) and attempt < 2:
                        await self._ensure_token()
                        continue
                    return data
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < 2:
                    wait = 2 ** attempt
                    logger.warning(f"[API] 네트워크 오류, {attempt+1}회 재시도: {e}")
                    await asyncio.sleep(wait)
                    continue
                logger.error(f"[API] POST 실패 (3회 시도): {e}")
                return {"rt_cd": "-1", "msg1": f"네트워크 오류: {e}"}
        return {"rt_cd": "-1", "msg1": "API 호출 실패 (최대 재시도 초과)"}

    async def _get_hashkey(self, body: dict) -> Optional[str]:
        url = f"{self.config.base_url}/uapi/hashkey"
        headers = {
            "Content-Type": "application/json",
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
        }
        for attempt in range(3):
            try:
                await self._rate_limit()
                async with self._session.post(url, headers=headers, json=body) as resp:
                    if resp.status != 200:
                        if attempt < 2:
                            await asyncio.sleep(0.5 * (attempt + 1))
                            continue
                        return None
                    data = await resp.json()
                    return data.get("HASH")
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(0.5 * (attempt + 1))
                else:
                    logger.error(f"Hashkey 발급 실패: {e}")
        return None
