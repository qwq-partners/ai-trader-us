"""
AI Trader US - Live Trading Engine

KIS 해외주식 API 기반 라이브 트레이딩 엔진.
6개 백그라운드 태스크로 스크리닝/주문/청산/동기화 수행.

태스크:
1. _screening_loop (30분) — 유니버스 스캔 → 전략 시그널 → 주문
2. _exit_check_loop (60초) — 보유 포지션 청산 체크
3. _portfolio_sync_loop (30초) — KIS 잔고 ↔ 로컬 Portfolio 동기화
4. _order_check_loop (10초) — 미체결 주문 상태 폴링
5. _eod_close_loop (30초) — 마감 15분 전 DAY 포지션 청산
6. _heartbeat_loop (5분) — 상태 로깅
"""

from __future__ import annotations

import asyncio
import signal
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Set

from loguru import logger

from .config import AppConfig
from .types import (
    Portfolio, Position, Signal, TradeResult, OrderSide,
    StrategyType, TimeHorizon, PositionSide,
)
from ..data.providers.yfinance_provider import YFinanceProvider
from ..data.store import DataStore
from ..data.universe import UniverseManager
from ..execution.broker.kis_us_broker import EXCHANGE_MAP
from ..indicators.technical import compute_indicators
from ..risk.manager import RiskManager
from ..strategies.base import BaseStrategy
from ..strategies.exit_manager import ExitManager
from ..strategies.momentum import MomentumBreakoutStrategy
from ..strategies.orb import ORBStrategy
from ..strategies.vwap_bounce import VWAPBounceStrategy
from ..strategies.sepa import SEPATrendStrategy
from ..strategies.earnings_drift import EarningsDriftStrategy
from ..utils.session import USSession
from ..utils.trade_journal import TradeJournal


# 전략 타입 → 클래스 매핑
STRATEGY_CLASSES = {
    "momentum": MomentumBreakoutStrategy,
    "orb": ORBStrategy,
    "vwap_bounce": VWAPBounceStrategy,
    "sepa": SEPATrendStrategy,
    "earnings_drift": EarningsDriftStrategy,
}


class LiveEngine:
    """라이브 트레이딩 엔진"""

    def __init__(self, config: AppConfig):
        self.config = config
        self._live_cfg = config.raw.get("live", {})

        # 핵심 컴포넌트
        self.portfolio = Portfolio(
            cash=config.trading.initial_capital,
            initial_capital=config.trading.initial_capital,
        )
        self.broker = self._create_broker()
        self.risk_manager = RiskManager(config.trading.risk)
        self.exit_manager = ExitManager(config.raw.get("exit_manager", {}))
        self.session = USSession()
        self.data_provider = YFinanceProvider()
        self.data_store = DataStore()
        self.universe_mgr = UniverseManager(
            provider=self.data_provider,
            config=config.raw.get("universe", {}),
        )
        self.journal = TradeJournal()
        self.strategies: List[BaseStrategy] = []

        # 상태
        self._pending_orders: Dict[str, dict] = {}  # order_no -> order_info
        self._pending_symbols: Set[str] = set()
        self._signal_cooldown: Dict[str, datetime] = {}  # symbol -> last_signal_time
        self._exchange_cache: Dict[str, str] = {}  # symbol -> exchange_code
        self._indicator_cache: Dict[str, dict] = {}  # symbol -> indicators (스크리닝 사이클마다 갱신)
        self._universe: List[str] = []
        self._tasks: List[asyncio.Task] = []
        self._running = False

        # 설정값
        self._screening_interval = self._live_cfg.get("screening_interval_min", 30) * 60
        self._max_screen_symbols = self._live_cfg.get("max_screen_symbols", 100)
        self._max_signals_per_cycle = self._live_cfg.get("max_signals_per_cycle", 3)
        self._signal_cooldown_sec = self._live_cfg.get("signal_cooldown_sec", 300)
        self._position_sync_sec = self._live_cfg.get("position_sync_sec", 30)
        self._exit_check_sec = self._live_cfg.get("exit_check_sec", 60)
        self._order_check_sec = self._live_cfg.get("order_check_sec", 10)
        self._heartbeat_sec = self._live_cfg.get("heartbeat_sec", 300)
        self._default_exchange = self._live_cfg.get("default_exchange", "NASD")

    # ============================================================
    # 초기화 / 종료
    # ============================================================

    async def initialize(self):
        """엔진 초기화"""
        logger.info("=" * 60)
        logger.info("AI Trader US - Live Engine 시작")
        logger.info("=" * 60)

        # 1. 브로커 연결
        broker_type = self._live_cfg.get("broker", "kis")
        if not await self.broker.connect():
            raise RuntimeError(f"{broker_type} 브로커 연결 실패")
        logger.info(f"브로커: {broker_type}")

        # 2. 전략 로드
        self._load_strategies()
        logger.info(f"전략 로드: {[s.name for s in self.strategies]}")

        # 3. 유니버스 로드
        pools = self.config.raw.get("universe", {}).get("pools", ["sp500"])
        self._universe = self.universe_mgr.get_universe(pools)
        logger.info(f"유니버스: {len(self._universe)} 종목")

        # 4. 포트폴리오 동기화
        await self._sync_portfolio()
        logger.info(
            f"포트폴리오: cash=${self.portfolio.cash:.2f}, "
            f"positions={len(self.portfolio.positions)}, "
            f"equity=${self.portfolio.total_equity:.2f}"
        )

    def _create_broker(self):
        """설정 기반 브로커 생성 팩토리"""
        broker_type = self._live_cfg.get("broker", "kis")
        if broker_type == "alpaca_paper":
            from ..execution.broker.alpaca_async_broker import AsyncAlpacaBroker
            return AsyncAlpacaBroker(paper=True)
        elif broker_type == "kis":
            from ..execution.broker.kis_us_broker import KISUSBroker
            return KISUSBroker()
        else:
            raise ValueError(f"Unknown broker: {broker_type}")

    def _load_strategies(self):
        """설정에서 활성 전략 로드"""
        strategies_cfg = self.config.raw.get("strategies", {})

        for name, cls in STRATEGY_CLASSES.items():
            cfg = strategies_cfg.get(name, {})
            if cfg.get("enabled", True):
                strategy = cls(config=cfg)
                self.strategies.append(strategy)

    async def run(self):
        """메인 루프 — 6개 백그라운드 태스크 실행"""
        self._running = True

        # SIGINT/SIGTERM 핸들러
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

        # 태스크 시작
        self._tasks = [
            asyncio.create_task(self._screening_loop(), name="screening"),
            asyncio.create_task(self._exit_check_loop(), name="exit_check"),
            asyncio.create_task(self._portfolio_sync_loop(), name="portfolio_sync"),
            asyncio.create_task(self._order_check_loop(), name="order_check"),
            asyncio.create_task(self._eod_close_loop(), name="eod_close"),
            asyncio.create_task(self._heartbeat_loop(), name="heartbeat"),
        ]

        logger.info(f"라이브 엔진 시작 — {len(self._tasks)}개 태스크 실행")

        try:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        except asyncio.CancelledError:
            logger.info("태스크 취소됨")

    async def shutdown(self):
        """graceful 종료"""
        logger.info("라이브 엔진 종료 시작...")
        self._running = False

        # 태스크 취소
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # 브로커 연결 해제
        await self.broker.disconnect()

        logger.info("라이브 엔진 종료 완료")

    # ============================================================
    # 태스크 1: 스크리닝 루프
    # ============================================================

    async def _screening_loop(self):
        """유니버스 스캔 → 전략 시그널 → 주문"""
        await asyncio.sleep(5)  # 초기 대기

        while self._running:
            try:
                if not self.session.is_market_open():
                    logger.debug("[스크리닝] 장 마감 — skip")
                    await asyncio.sleep(60)
                    continue

                await self._run_screening()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"[스크리닝] 오류: {e}")

            await asyncio.sleep(self._screening_interval)

    async def _run_screening(self):
        """한 사이클의 스크리닝 + 시그널 처리"""
        logger.info(f"[스크리닝] 시작 — {len(self._universe)} 종목 중 "
                    f"최대 {self._max_screen_symbols}개 스캔")

        # 사이클마다 인디케이터 캐시 리셋
        self._indicator_cache.clear()

        # 쿨다운 만료 항목 정리
        now = datetime.now()
        expired = [s for s, t in self._signal_cooldown.items()
                   if (now - t).total_seconds() > self._signal_cooldown_sec]
        for s in expired:
            del self._signal_cooldown[s]

        # 보유 종목 제외, 신규 매수 대상만 스캔
        held = set(self.portfolio.positions.keys())
        candidates = [s for s in self._universe if s not in held]
        candidates = candidates[:self._max_screen_symbols]

        signals: List[Signal] = []
        processed = 0

        for symbol in candidates:
            if not self._running:
                break

            # 쿨다운 체크
            if self._is_in_cooldown(symbol):
                continue

            # 이미 주문 중이면 스킵
            if symbol in self._pending_symbols:
                continue

            try:
                # 히스토리 로드 (캐시 + yfinance)
                history = await self._get_history(symbol)
                if history is None or len(history) < 50:
                    continue

                # 인디케이터 사전 계산 → 캐시 (exit_check_loop에서 재사용)
                try:
                    self._indicator_cache[symbol] = compute_indicators(history)
                except Exception:
                    pass

                # 전략별 평가
                for strategy in self.strategies:
                    signal = strategy.evaluate(symbol, history, self.portfolio)
                    if signal:
                        signals.append(signal)
                        break  # 한 종목당 하나의 시그널

                processed += 1
            except Exception as e:
                logger.debug(f"[스크리닝] {symbol} 평가 실패: {e}")

        # 시그널 스코어 순 정렬 → 상위 N개 주문
        signals.sort(key=lambda s: s.score, reverse=True)
        submitted = 0

        for sig in signals[:self._max_signals_per_cycle]:
            success = await self._process_signal(sig)
            if success:
                submitted += 1

        logger.info(
            f"[스크리닝] 완료 — 스캔: {processed}, 시그널: {len(signals)}, "
            f"주문: {submitted}"
        )

    async def _process_signal(self, signal: Signal) -> bool:
        """시그널을 주문으로 변환"""
        symbol = signal.symbol

        # 리스크 체크
        if not self.risk_manager.can_open_position(self.portfolio, signal):
            logger.info(f"[시그널] {symbol} — 리스크 체크 실패")
            return False

        # 현재가 조회
        exchange = await self._get_exchange(symbol)
        quote = await self.broker.get_quote(symbol, exchange)
        price = quote.get("price", 0)
        if price <= 0:
            logger.warning(f"[시그널] {symbol} — 현재가 조회 실패")
            return False

        # 포지션 사이징
        qty = self.risk_manager.calculate_position_size(
            self.portfolio, Decimal(str(price))
        )
        if qty <= 0:
            logger.info(f"[시그널] {symbol} — 사이징 0주 (자금 부족)")
            return False

        # 매수 주문 제출
        result = await self.broker.submit_buy_order(symbol, exchange, qty, price=0)

        if result.get("success"):
            order_no = result.get("order_no", "")
            self._pending_orders[order_no] = {
                "symbol": symbol,
                "side": "buy",
                "qty": qty,
                "price": price,
                "strategy": signal.strategy.value,
                "signal_score": signal.score,
                "exchange": exchange,
                "submitted_at": datetime.now(),
            }
            self._pending_symbols.add(symbol)
            self._signal_cooldown[symbol] = datetime.now()

            # 주문 기록
            self.journal.record_order({
                "symbol": symbol,
                "side": "buy",
                "qty": qty,
                "price": price,
                "order_type": "market",
                "order_no": order_no,
                "strategy": signal.strategy.value,
                "status": "submitted",
                "message": signal.reason,
            })

            logger.info(
                f"[매수 주문] {symbol} {qty}주 @ ${price:.2f} "
                f"({signal.strategy.value}, score={signal.score:.0f})"
            )
            return True
        else:
            logger.warning(f"[매수 주문] {symbol} 실패: {result.get('message')}")
            return False

    # ============================================================
    # 태스크 2: 청산 체크 루프
    # ============================================================

    async def _exit_check_loop(self):
        """보유 포지션 → ExitManager → 매도"""
        while self._running:
            try:
                if not self.session.is_market_open():
                    await asyncio.sleep(30)
                    continue

                await self._check_exits()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"[청산 체크] 오류: {e}")

            await asyncio.sleep(self._exit_check_sec)

    async def _check_exits(self):
        """보유 포지션 순회 → 청산 시그널 체크"""
        for symbol, position in list(self.portfolio.positions.items()):
            if symbol in self._pending_symbols:
                continue

            try:
                # 현재가 갱신
                exchange = await self._get_exchange(symbol)
                quote = await self.broker.get_quote(symbol, exchange)
                price = quote.get("price", 0)
                if price <= 0:
                    continue

                position.current_price = Decimal(str(price))

                # 최고가 갱신
                if position.highest_price is None or position.current_price > position.highest_price:
                    position.highest_price = position.current_price

                # ATR 계산
                atr_val = await self._get_atr(symbol)

                # ExitManager 체크
                exit_signal = self.exit_manager.check_exit(position, price, atr_val)
                if exit_signal:
                    await self._execute_exit(symbol, position, exit_signal, exchange)

            except Exception as e:
                logger.debug(f"[청산 체크] {symbol} 오류: {e}")

    async def _execute_exit(self, symbol: str, position: Position,
                            exit_signal: dict, exchange: str):
        """매도 주문 실행"""
        action = exit_signal.get("action", "close")
        ratio = exit_signal.get("ratio", 1.0)
        reason = exit_signal.get("reason", "")

        sell_qty = int(position.quantity * ratio)
        if sell_qty <= 0:
            sell_qty = position.quantity

        result = await self.broker.submit_sell_order(symbol, exchange, sell_qty, price=0)

        if result.get("success"):
            order_no = result.get("order_no", "")
            self._pending_orders[order_no] = {
                "symbol": symbol,
                "side": "sell",
                "qty": sell_qty,
                "price": float(position.current_price),
                "strategy": position.strategy or "",
                "reason": reason,
                "exchange": exchange,
                "submitted_at": datetime.now(),
            }
            self._pending_symbols.add(symbol)

            self.journal.record_order({
                "symbol": symbol,
                "side": "sell",
                "qty": sell_qty,
                "price": float(position.current_price),
                "order_type": "market",
                "order_no": order_no,
                "strategy": position.strategy or "",
                "status": "submitted",
                "message": reason,
            })

            logger.info(
                f"[매도 주문] {symbol} {sell_qty}/{position.quantity}주 — {reason}"
            )
        else:
            logger.warning(f"[매도 주문] {symbol} 실패: {result.get('message')}")

    # ============================================================
    # 태스크 3: 포트폴리오 동기화
    # ============================================================

    async def _portfolio_sync_loop(self):
        """KIS 잔고 ↔ 로컬 Portfolio 동기화"""
        while self._running:
            try:
                await self._sync_portfolio()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"[동기화] 오류: {e}")

            await asyncio.sleep(self._position_sync_sec)

    async def _sync_portfolio(self):
        """KIS 잔고와 로컬 포트폴리오 동기화 (단일 API 호출)"""
        # get_balance()로 포지션 + 계좌 정보를 한번에 조회
        balance = await self.broker.get_balance()
        if not balance:
            return

        # 계좌 정보 동기화
        account_info = balance.get("account", {})
        if account_info:
            self.portfolio.cash = Decimal(str(account_info.get("available_cash", 0)))

        # 포지션
        kis_positions = balance.get("positions", [])
        kis_symbols = set()

        for kp in kis_positions:
            symbol = kp["symbol"]
            kis_symbols.add(symbol)

            if symbol in self.portfolio.positions:
                # 기존 포지션 업데이트
                pos = self.portfolio.positions[symbol]
                pos.quantity = kp["qty"]
                pos.avg_price = Decimal(str(kp["avg_price"]))
                pos.current_price = Decimal(str(kp["current_price"]))
            else:
                # 새 포지션 (외부 진입 또는 체결 반영)
                self.portfolio.positions[symbol] = Position(
                    symbol=symbol,
                    name=kp.get("name", ""),
                    side=PositionSide.LONG,
                    quantity=kp["qty"],
                    avg_price=Decimal(str(kp["avg_price"])),
                    current_price=Decimal(str(kp["current_price"])),
                    entry_time=datetime.now(),
                )
                # 거래소 캐시
                self._exchange_cache[symbol] = kp.get("exchange", self._default_exchange)

        # KIS에 없는 포지션 → 청산 처리
        for symbol in list(self.portfolio.positions.keys()):
            if symbol not in kis_symbols:
                pos = self.portfolio.positions.pop(symbol)
                self.exit_manager.on_position_closed(symbol)
                self._pending_symbols.discard(symbol)
                logger.info(f"[동기화] {symbol} 포지션 청산 확인 (KIS에서 제거됨)")

                # 거래 기록
                self.journal.record_trade(TradeResult(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    entry_price=pos.avg_price,
                    exit_price=pos.current_price,
                    quantity=pos.quantity,
                    entry_time=pos.entry_time or datetime.now(),
                    exit_time=datetime.now(),
                    strategy=pos.strategy or "unknown",
                    reason="sync_closed",
                ))

    # ============================================================
    # 태스크 4: 주문 상태 체크
    # ============================================================

    async def _order_check_loop(self):
        """미체결 주문 상태 폴링"""
        while self._running:
            try:
                if self._pending_orders:
                    await self._check_orders()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"[주문 체크] 오류: {e}")

            await asyncio.sleep(self._order_check_sec)

    async def _check_orders(self):
        """체결 내역 조회 → 체결 처리"""
        history = await self.broker.get_order_history()
        if not history:
            return

        # order_no → 체결 정보 매핑
        filled_map = {h["order_no"]: h for h in history}

        for order_no in list(self._pending_orders.keys()):
            info = filled_map.get(order_no)
            if not info:
                # 오래된 주문 타임아웃 (5분)
                pending = self._pending_orders[order_no]
                elapsed = (datetime.now() - pending["submitted_at"]).total_seconds()
                if elapsed > 300:
                    logger.warning(f"[주문 체크] {order_no} 타임아웃 (5분) — 제거")
                    self._pending_symbols.discard(pending["symbol"])
                    del self._pending_orders[order_no]
                continue

            if info["status"] == "filled":
                await self._on_order_filled(order_no, info)
            elif info["status"] == "partial":
                logger.debug(
                    f"[주문 체크] {order_no} 부분체결 "
                    f"({info['filled_qty']}/{info['qty']})"
                )

    async def _on_order_filled(self, order_no: str, fill_info: dict):
        """주문 체결 처리"""
        pending = self._pending_orders.pop(order_no, None)
        if not pending:
            return

        symbol = pending["symbol"]
        side = pending["side"]
        filled_price = fill_info.get("filled_price", 0)
        filled_qty = fill_info.get("filled_qty", 0)

        self._pending_symbols.discard(symbol)

        if side == "buy":
            logger.info(
                f"[체결] 매수 {symbol} {filled_qty}주 @ ${filled_price:.2f} "
                f"(전략: {pending.get('strategy', '')})"
            )
            # 포지션에 전략/시간지평 세팅 (sync에서 생성되면 strategy=None이므로)
            pos = self.portfolio.positions.get(symbol)
            if pos:
                pos.strategy = pending.get("strategy", "")
                # 전략의 time_horizon 찾기
                for strat in self.strategies:
                    if strat.strategy_type.value == pos.strategy:
                        pos.time_horizon = strat.time_horizon
                        break
        else:
            logger.info(
                f"[체결] 매도 {symbol} {filled_qty}주 @ ${filled_price:.2f} "
                f"(사유: {pending.get('reason', '')})"
            )

            # 거래 기록
            pos = self.portfolio.positions.get(symbol)
            if pos:
                trade = TradeResult(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    entry_price=pos.avg_price,
                    exit_price=Decimal(str(filled_price)),
                    quantity=filled_qty,
                    entry_time=pos.entry_time or datetime.now(),
                    exit_time=datetime.now(),
                    strategy=pos.strategy or pending.get("strategy", ""),
                    reason=pending.get("reason", ""),
                )
                self.journal.record_trade(trade)
                self.risk_manager.record_trade_result(trade.is_win)

                # 전량 매도 시 포지션 정리
                if filled_qty >= pos.quantity:
                    self.exit_manager.on_position_closed(symbol)

    # ============================================================
    # 태스크 5: EOD 청산
    # ============================================================

    async def _eod_close_loop(self):
        """마감 15분 전 DAY 포지션 청산"""
        while self._running:
            try:
                if self.session.is_market_open():
                    minutes_left = self.session.minutes_to_close()
                    if 0 < minutes_left <= 15:
                        await self._eod_close()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"[EOD] 오류: {e}")

            await asyncio.sleep(30)

    async def _eod_close(self):
        """DAY 타임호라이즌 포지션 전량 청산"""
        # DAY 전략 목록 (time_horizon=day인 전략의 strategy_type.value)
        day_strategies = {s.strategy_type.value for s in self.strategies
                         if s.time_horizon == TimeHorizon.DAY}

        for symbol, pos in list(self.portfolio.positions.items()):
            if symbol in self._pending_symbols:
                continue

            # DAY 전략 포지션만 청산
            if pos.strategy in day_strategies or pos.time_horizon == TimeHorizon.DAY:
                exchange = await self._get_exchange(symbol)
                logger.info(f"[EOD] {symbol} DAY 포지션 청산")
                await self._execute_exit(
                    symbol, pos,
                    {"action": "close", "ratio": 1.0, "reason": "eod_close"},
                    exchange,
                )

    # ============================================================
    # 태스크 6: Heartbeat
    # ============================================================

    async def _heartbeat_loop(self):
        """상태 로깅"""
        while self._running:
            try:
                session_status = self.session.get_session()
                metrics = self.risk_manager.get_risk_metrics(self.portfolio)

                logger.info(
                    f"[Heartbeat] session={session_status.value} | "
                    f"equity=${self.portfolio.total_equity:.2f} | "
                    f"cash=${self.portfolio.cash:.2f} | "
                    f"positions={len(self.portfolio.positions)} | "
                    f"pending={len(self._pending_orders)} | "
                    f"daily_pnl=${metrics.daily_loss:.2f} ({metrics.daily_loss_pct:.1f}%)"
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Heartbeat] 오류: {e}")

            await asyncio.sleep(self._heartbeat_sec)

    # ============================================================
    # 헬퍼
    # ============================================================

    async def _get_history(self, symbol: str) -> Optional['pd.DataFrame']:
        """종목 히스토리 로드 (캐시 → yfinance, 동기 IO는 to_thread로 래핑)"""
        # 캐시 확인
        cached = self.data_store.load(symbol)
        today = date.today()

        if cached is not None and not cached.empty:
            last_date = cached.index[-1]
            if hasattr(last_date, 'date'):
                last_date = last_date.date()

            # 오늘 이미 최신이면 캐시 사용
            if last_date >= today - timedelta(days=1):
                return cached

            # 증분 다운로드 (yfinance는 동기 HTTP → to_thread)
            try:
                new_data = await asyncio.to_thread(
                    self.data_provider.get_daily_bars,
                    symbol,
                    last_date + timedelta(days=1),
                    today,
                )
                if not new_data.empty:
                    self.data_store.update(symbol, new_data)
                    return self.data_store.load(symbol)
            except Exception:
                pass

            return cached

        # 전체 다운로드 (1년)
        try:
            start = today - timedelta(days=365)
            df = await asyncio.to_thread(
                self.data_provider.get_daily_bars, symbol, start, today,
            )
            if not df.empty:
                self.data_store.save(symbol, df)
                return df
        except Exception as e:
            logger.debug(f"[히스토리] {symbol} 다운로드 실패: {e}")

        return None

    async def _get_atr(self, symbol: str) -> Optional[float]:
        """ATR 조회 (캐시된 히스토리 + 인디케이터 캐시)"""
        # 인디케이터 캐시 먼저 확인
        if symbol in self._indicator_cache:
            return self._indicator_cache[symbol].get("atr")

        history = self.data_store.load(symbol)
        if history is None or len(history) < 20:
            return None

        try:
            indicators = compute_indicators(history)
            self._indicator_cache[symbol] = indicators
            return indicators.get("atr")
        except Exception:
            return None

    async def _get_exchange(self, symbol: str) -> str:
        """종목의 거래소 코드 조회 (캐시, yfinance 동기 IO → to_thread)"""
        if symbol in self._exchange_cache:
            return self._exchange_cache[symbol]

        try:
            info = await asyncio.to_thread(self.data_provider.get_info, symbol)
            raw_exchange = info.get("exchange", "") or ""
            exchange = EXCHANGE_MAP.get(raw_exchange.upper(), self._default_exchange)
        except Exception:
            exchange = self._default_exchange

        self._exchange_cache[symbol] = exchange
        return exchange

    def _is_in_cooldown(self, symbol: str) -> bool:
        """시그널 쿨다운 체크"""
        last = self._signal_cooldown.get(symbol)
        if last is None:
            return False
        elapsed = (datetime.now() - last).total_seconds()
        return elapsed < self._signal_cooldown_sec
