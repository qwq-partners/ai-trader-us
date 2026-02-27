"""
AI Trader US - Async Alpaca Broker

기존 동기 AlpacaBroker를 asyncio.to_thread()로 래핑.
LiveEngine이 호출하는 KISUSBroker와 동일한 async 인터페이스 제공.

지원: Alpaca Paper Trading (paper=True)
현재가 조회: Alpaca → yfinance fallback
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger


class AsyncAlpacaBroker:
    """
    Alpaca 비동기 브로커 — KISUSBroker와 동일한 인터페이스.

    내부적으로 동기 AlpacaBroker를 to_thread()로 호출.
    """

    def __init__(
        self,
        api_key: str = None,
        secret_key: str = None,
        paper: bool = True,
    ):
        self._api_key = api_key or os.environ.get("ALPACA_API_KEY", "")
        self._secret_key = secret_key or os.environ.get("ALPACA_SECRET_KEY", "")
        self._paper = paper
        self._broker = None  # lazy init (connect에서 생성)

    # ============================================================
    # 연결 관리
    # ============================================================

    async def connect(self) -> bool:
        """Alpaca 클라이언트 초기화 + 연결 확인"""
        try:
            from .alpaca_broker import AlpacaBroker

            self._broker = await asyncio.to_thread(
                AlpacaBroker,
                api_key=self._api_key,
                secret_key=self._secret_key,
                paper=self._paper,
            )
            mode = "PAPER" if self._paper else "LIVE"
            logger.info(f"AsyncAlpacaBroker [{mode}] 연결 완료")
            return True
        except Exception as e:
            logger.exception(f"AsyncAlpacaBroker 연결 실패: {e}")
            return False

    async def disconnect(self):
        """Alpaca는 persistent connection이 없으므로 정리만"""
        self._broker = None
        logger.info("AsyncAlpacaBroker 연결 해제")

    @property
    def is_connected(self) -> bool:
        return self._broker is not None

    # ============================================================
    # 현재가 조회
    # ============================================================

    async def get_quote(self, symbol: str, exchange: str = "NASD") -> dict:
        """
        현재가 조회 — yfinance 사용 (Alpaca paper는 실시간 시세 제한).

        Returns:
            {symbol, price, change_pct, volume, exchange}
        """
        try:
            import yfinance as yf

            ticker = await asyncio.to_thread(lambda: yf.Ticker(symbol))
            info = await asyncio.to_thread(lambda: ticker.fast_info)

            price = float(getattr(info, "last_price", 0) or 0)
            prev_close = float(getattr(info, "previous_close", 0) or 0)
            change_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0

            if price > 0:
                return {
                    "symbol": symbol,
                    "price": price,
                    "change_pct": round(change_pct, 2),
                    "volume": int(getattr(info, "last_volume", 0) or 0),
                    "exchange": exchange,
                }
        except Exception as e:
            logger.debug(f"[Quote] yfinance 조회 실패 ({symbol}): {e}")

        # fallback: 가격 0 반환
        return {"symbol": symbol, "price": 0, "change_pct": 0, "volume": 0, "exchange": exchange}

    # ============================================================
    # 주문
    # ============================================================

    async def submit_buy_order(
        self, symbol: str, exchange: str = "NASD", qty: int = 0, price: float = 0
    ) -> dict:
        """
        매수 주문.

        price=0이면 시장가, price>0이면 지정가.
        """
        if not self._broker:
            return {"success": False, "message": "브로커 미연결"}
        if qty <= 0:
            return {"success": False, "message": "수량은 1 이상이어야 합니다"}

        try:
            if price > 0:
                result = await asyncio.to_thread(
                    self._broker.submit_limit_order, symbol, qty, price, "buy"
                )
            else:
                result = await asyncio.to_thread(
                    self._broker.submit_market_order, symbol, qty, "buy"
                )
            return {
                "success": True,
                "order_no": result.get("id", ""),
                "symbol": symbol,
                "qty": qty,
                "price": price,
                "status": result.get("status", ""),
                "message": "",
            }
        except Exception as e:
            logger.error(f"[매수] {symbol} {qty}주 실패: {e}")
            return {"success": False, "message": str(e)}

    async def submit_sell_order(
        self, symbol: str, exchange: str = "NASD", qty: int = 0, price: float = 0
    ) -> dict:
        """
        매도 주문.

        price=0이면 시장가, price>0이면 지정가.
        """
        if not self._broker:
            return {"success": False, "message": "브로커 미연결"}
        if qty <= 0:
            return {"success": False, "message": "수량은 1 이상이어야 합니다"}

        try:
            if price > 0:
                result = await asyncio.to_thread(
                    self._broker.submit_limit_order, symbol, qty, price, "sell"
                )
            else:
                result = await asyncio.to_thread(
                    self._broker.submit_market_order, symbol, qty, "sell"
                )
            return {
                "success": True,
                "order_no": result.get("id", ""),
                "symbol": symbol,
                "qty": qty,
                "price": price,
                "status": result.get("status", ""),
                "message": "",
            }
        except Exception as e:
            logger.error(f"[매도] {symbol} {qty}주 실패: {e}")
            return {"success": False, "message": str(e)}

    # ============================================================
    # 잔고 / 포지션 조회
    # ============================================================

    async def get_balance(self) -> dict:
        """
        계좌 + 포지션 조회 (KISUSBroker.get_balance와 동일 형식).

        Returns:
            {positions: [...], account: {total_equity, available_cash, ...}}
        """
        if not self._broker:
            return {}

        try:
            account = await asyncio.to_thread(self._broker.get_account)
            raw_positions = await asyncio.to_thread(self._broker.get_positions)

            positions = []
            for p in raw_positions:
                positions.append({
                    "symbol": p["symbol"],
                    "name": p["symbol"],
                    "qty": p["qty"],
                    "avg_price": p["avg_entry_price"],
                    "current_price": p["current_price"],
                    "pnl": p["unrealized_pnl"],
                    "pnl_pct": p["unrealized_pnl_pct"],
                    "exchange": "NASD",
                })

            return {
                "positions": positions,
                "account": {
                    "total_equity": account["equity"],
                    "available_cash": account["buying_power"],
                    "total_pnl": account["unrealized_pnl"],
                    "total_pnl_pct": 0,
                },
            }
        except Exception as e:
            logger.error(f"[잔고] 조회 실패: {e}")
            return {}

    async def get_positions(self) -> list:
        """포지션 목록 조회"""
        if not self._broker:
            return []
        try:
            return await asyncio.to_thread(self._broker.get_positions)
        except Exception as e:
            logger.error(f"[포지션] 조회 실패: {e}")
            return []

    async def get_order_history(
        self, start_date: str = None, end_date: str = None
    ) -> list:
        """
        체결 내역 조회 (KISUSBroker 형식).

        Returns:
            [{order_no, symbol, side, qty, filled_qty, filled_price, status, time}]
        """
        if not self._broker:
            return []

        try:
            closed_orders = await asyncio.to_thread(
                self._broker.get_orders, "closed"
            )

            result = []
            for o in closed_orders:
                status = "filled" if o["filled_qty"] >= o["qty"] and o["qty"] > 0 else "partial"
                result.append({
                    "order_no": o["id"],
                    "symbol": o["symbol"],
                    "side": o["side"].replace("OrderSide.", "").lower(),
                    "qty": o["qty"],
                    "price": o.get("limit_price") or o.get("filled_avg_price", 0),
                    "filled_qty": o["filled_qty"],
                    "filled_price": o["filled_avg_price"],
                    "status": status,
                    "time": o.get("filled_at", ""),
                    "exchange": "NASD",
                })
            return result
        except Exception as e:
            logger.error(f"[체결내역] 조회 실패: {e}")
            return []
