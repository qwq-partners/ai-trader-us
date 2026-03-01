"""
AI Trader US - HTTP API Server

aiohttp 기반 API 서버.
LiveEngine 상태를 JSON으로 노출하여 대시보드에서 조회할 수 있게 함.
"""

from __future__ import annotations

import asyncio
import csv
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from aiohttp import web
from loguru import logger

if TYPE_CHECKING:
    from ..core.live_engine import LiveEngine

VERSION = "1.0.0"


@web.middleware
async def cors_middleware(request: web.Request, handler):
    """CORS 헤더 추가 미들웨어"""
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        response = await handler(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


class APIServer:
    """LiveEngine 상태를 노출하는 HTTP API 서버"""

    def __init__(self, engine: LiveEngine, port: int = 8081):
        self.engine = engine
        self.port = port
        self._runner: web.AppRunner | None = None

    def _build_app(self) -> web.Application:
        app = web.Application(middlewares=[cors_middleware])
        app.router.add_get("/health", self._handle_health)
        app.router.add_get("/api/us/status", self._handle_status)
        app.router.add_get("/api/us/portfolio", self._handle_portfolio)
        app.router.add_get("/api/us/positions", self._handle_positions)
        app.router.add_get("/api/us/signals", self._handle_signals)
        app.router.add_get("/api/us/orders", self._handle_orders)
        app.router.add_get("/api/us/trades", self._handle_trades)
        app.router.add_get("/api/us/themes", self._handle_themes)
        app.router.add_get("/api/us/screening", self._handle_screening)
        return app

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def run(self):
        """API 서버 시작 (asyncio.gather에서 사용)"""
        app = self._build_app()
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, "0.0.0.0", self.port)
        await site.start()
        logger.info(f"API 서버 시작 — http://0.0.0.0:{self.port}")

        # engine이 살아있는 동안 대기
        try:
            while getattr(self.engine, "_running", False):
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    async def stop(self):
        """API 서버 종료"""
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
            logger.info("API 서버 종료")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    async def _handle_health(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def _handle_status(self, request: web.Request) -> web.Response:
        engine = self.engine
        session = getattr(engine, "session", None)
        session_value = "closed"
        if session:
            try:
                session_value = session.get_session().value
            except Exception:
                pass

        # 브로커 및 운영 환경 정보 (대시보드 TEST 배지 표시용)
        live_cfg = getattr(engine, "_live_cfg", {}) or {}
        broker_name = live_cfg.get("broker", "kis")
        env = live_cfg.get("env", "prod")
        is_paper = broker_name == "alpaca_paper" or env == "dev"

        return web.json_response({
            "running": getattr(engine, "_running", False),
            "session": session_value,
            "timestamp": datetime.now().isoformat(),
            "version": VERSION,
            "broker": broker_name,
            "env": env,
            "paper_trading": is_paper,   # True → 대시보드에서 TEST 배지 표시
        })

    async def _handle_portfolio(self, request: web.Request) -> web.Response:
        portfolio = self.engine.portfolio
        total_value = float(portfolio.total_equity)
        positions_value = float(portfolio.total_position_value)
        daily_pnl = float(portfolio.effective_daily_pnl)
        initial = float(portfolio.initial_capital)
        daily_pnl_pct = (daily_pnl / initial * 100) if initial else 0.0

        return web.json_response({
            "cash": float(portfolio.cash),
            "total_value": total_value,
            "positions_value": positions_value,
            "daily_pnl": daily_pnl,
            "daily_pnl_pct": round(daily_pnl_pct, 2),
            "positions_count": len(portfolio.positions),
        })

    async def _handle_positions(self, request: web.Request) -> web.Response:
        positions = []
        for symbol, pos in self.engine.portfolio.positions.items():
            positions.append({
                "symbol": symbol,
                "name": getattr(pos, "name", ""),
                "quantity": pos.quantity,
                "avg_price": float(pos.avg_price),
                "current_price": float(pos.current_price),
                "pnl": float(pos.unrealized_pnl),
                "pnl_pct": round(pos.unrealized_pnl_pct, 2),
                "strategy": pos.strategy or "",
                "stage": getattr(pos, "stage", ""),
                "market_value": float(pos.market_value),
            })
        return web.json_response(positions)

    async def _handle_signals(self, request: web.Request) -> web.Response:
        signals = list(getattr(self.engine, "recent_signals", []))
        return web.json_response(signals)

    async def _handle_orders(self, request: web.Request) -> web.Response:
        orders = []
        for order_no, info in dict(getattr(self.engine, "_pending_orders", {})).items():
            orders.append({
                "order_no": order_no,
                "symbol": info.get("symbol", ""),
                "side": info.get("side", ""),
                "quantity": info.get("qty", 0),
                "price": float(info.get("price", 0)),
                "status": "pending",
                "timestamp": info.get("submitted_at", datetime.now()).isoformat(),
            })
        return web.json_response(orders)

    async def _handle_trades(self, request: web.Request) -> web.Response:
        """TradeJournal CSV에서 거래 내역 반환"""
        date_str = request.rel_url.query.get("date", "")
        journal_path = Path(__file__).parent.parent.parent / "data" / "journal" / "trades.csv"
        trades: list[dict] = []
        if journal_path.exists():
            with open(journal_path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if date_str and not row.get("timestamp", "").startswith(date_str):
                        continue
                    trades.append({
                        "timestamp": row.get("timestamp", ""),
                        "symbol": row.get("symbol", ""),
                        "side": row.get("side", ""),
                        "entry_price": float(row.get("entry_price", 0) or 0),
                        "exit_price": float(row.get("exit_price", 0) or 0),
                        "quantity": float(row.get("quantity", 0) or 0),
                        "pnl": float(row.get("pnl", 0) or 0),
                        "pnl_pct": float(row.get("pnl_pct", 0) or 0),
                        "strategy": row.get("strategy", ""),
                        "reason": row.get("reason", ""),
                        "holding_minutes": float(row.get("holding_minutes", 0) or 0),
                        "market": "US",
                    })
        return web.json_response(list(reversed(trades[-200:])))

    async def _handle_themes(self, request: web.Request) -> web.Response:
        """US 테마 목록 반환"""
        detector = getattr(self.engine, "theme_detector", None)
        if not detector:
            return web.json_response([])
        return web.json_response(detector.to_dict_list())

    async def _handle_screening(self, request: web.Request) -> web.Response:
        """스크리너 결과 반환 (상위 50개)"""
        result = getattr(self.engine, "_last_screen_result", None)
        if not result:
            return web.json_response([])

        def _safe_round(val, digits=2):
            return round(val, digits) if val is not None else 0

        items = []
        for r in result.results[:50]:
            items.append({
                "symbol": r.symbol,
                "price": r.close if r.close is not None else 0,
                "change_pct": _safe_round(r.change_1d),
                "change_5d": _safe_round(r.change_5d),
                "volume": r.volume if r.volume is not None else 0,
                "avg_volume": r.avg_volume if r.avg_volume is not None else 0,
                "vol_ratio": _safe_round(r.vol_ratio),
                "rsi": _safe_round(r.rsi, 1),
                "pct_from_52w_high": _safe_round(r.pct_from_52w_high, 1),
                "atr_pct": _safe_round(r.atr_pct),
                "score": _safe_round(r.score, 1),
                "total_score": _safe_round(r.total_score, 1),
                "finviz_bonus": _safe_round(r.finviz_bonus, 1),
                "finviz_meta": r.finviz_meta if r.finviz_meta else {},
                "flags": r.flags if r.flags is not None else [],
            })
        return web.json_response(items)
