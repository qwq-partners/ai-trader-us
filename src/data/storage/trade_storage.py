"""
AI Trader US - PostgreSQL 거래 저장소

CSV TradeJournal 호환 + DB 영속화 + trade_events 이벤트 로그.
DB 연결 실패 시 CSV 전용 모드로 자동 폴백.

KR 엔진 trade_storage.py 기반, US 적응:
- 통화: USD (NUMERIC 12,4)
- 수수료: $0 (KIS 해외주식)
- 시간대: ET
- trade_id: {symbol}_{ET_timestamp}
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from loguru import logger

from ...utils.trade_journal import TradeJournal

_ET = ZoneInfo("America/New_York")


def _now_et() -> datetime:
    """현재 ET 시각 (timezone-naive, DB 호환)"""
    return datetime.now(_ET).replace(tzinfo=None)


def _today_et() -> date:
    """오늘 ET 기준 날짜"""
    return datetime.now(_ET).date()


# ── TradeRecord 데이터클래스 ─────────────────────────────


@dataclass
class TradeRecord:
    """US 거래 레코드 (인메모리 캐시 + DB 공용)"""
    id: str
    symbol: str
    name: str = ""
    exchange: str = ""
    entry_time: Optional[datetime] = None
    entry_price: float = 0
    entry_quantity: int = 0
    entry_reason: str = ""
    entry_strategy: str = ""
    entry_signal_score: float = 0
    exit_time: Optional[datetime] = None
    exit_price: float = 0
    exit_quantity: int = 0
    exit_reason: str = ""
    exit_type: str = ""
    pnl: float = 0
    pnl_pct: float = 0
    holding_minutes: int = 0
    market_context: Dict[str, Any] = field(default_factory=dict)
    indicators_at_entry: Dict[str, float] = field(default_factory=dict)
    indicators_at_exit: Dict[str, float] = field(default_factory=dict)
    review_notes: str = ""
    lesson_learned: str = ""
    improvement_suggestion: str = ""
    kis_order_no: str = ""
    created_at: datetime = field(default_factory=_now_et)
    updated_at: datetime = field(default_factory=_now_et)

    @property
    def is_win(self) -> bool:
        return self.pnl > 0

    @property
    def is_closed(self) -> bool:
        if self.exit_time is None:
            return False
        return self.entry_quantity > 0 and (self.exit_quantity or 0) >= self.entry_quantity


# ── SQL 스키마 (US 적응: NUMERIC 12,4) ─────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS trades (
    id              VARCHAR(80) PRIMARY KEY,
    symbol          VARCHAR(10)  NOT NULL,
    name            VARCHAR(100) DEFAULT '',
    exchange        VARCHAR(10)  DEFAULT '',
    entry_time      TIMESTAMP    NOT NULL,
    entry_price     NUMERIC(12,4) NOT NULL,
    entry_quantity  INTEGER      NOT NULL,
    entry_reason    TEXT         DEFAULT '',
    entry_strategy  VARCHAR(50)  DEFAULT '',
    entry_signal_score NUMERIC(6,2) DEFAULT 0,
    exit_time       TIMESTAMP    NULL,
    exit_price      NUMERIC(12,4) DEFAULT 0,
    exit_quantity   INTEGER      DEFAULT 0,
    exit_reason     TEXT         DEFAULT '',
    exit_type       VARCHAR(30)  DEFAULT '',
    pnl             NUMERIC(14,4) DEFAULT 0,
    pnl_pct         NUMERIC(8,4)  DEFAULT 0,
    holding_minutes INTEGER       DEFAULT 0,
    market_context       JSONB DEFAULT '{}',
    indicators_at_entry  JSONB DEFAULT '{}',
    indicators_at_exit   JSONB DEFAULT '{}',
    review_notes            TEXT DEFAULT '',
    lesson_learned          TEXT DEFAULT '',
    improvement_suggestion  TEXT DEFAULT '',
    kis_order_no VARCHAR(20) NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_us_trades_entry_time ON trades(entry_time DESC);
CREATE INDEX IF NOT EXISTS idx_us_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_us_trades_strategy ON trades(entry_strategy);
CREATE INDEX IF NOT EXISTS idx_us_trades_entry_date ON trades((entry_time::date));
CREATE INDEX IF NOT EXISTS idx_us_trades_open ON trades(exit_time) WHERE exit_time IS NULL;

CREATE TABLE IF NOT EXISTS trade_events (
    id              BIGSERIAL PRIMARY KEY,
    trade_id        VARCHAR(80) NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    symbol          VARCHAR(10) NOT NULL,
    name            VARCHAR(100) DEFAULT '',
    event_type      VARCHAR(10) NOT NULL,
    event_time      TIMESTAMP   NOT NULL,
    price           NUMERIC(12,4) NOT NULL,
    quantity        INTEGER     NOT NULL,
    exit_type       VARCHAR(30) NULL,
    exit_reason     TEXT        NULL,
    pnl             NUMERIC(14,4) NULL,
    pnl_pct         NUMERIC(8,4)  NULL,
    strategy        VARCHAR(50) DEFAULT '',
    signal_score    NUMERIC(6,2) DEFAULT 0,
    kis_order_no    VARCHAR(20) NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'holding',
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_us_te_event_time ON trade_events(event_time DESC);
CREATE INDEX IF NOT EXISTS idx_us_te_trade_id ON trade_events(trade_id);
CREATE INDEX IF NOT EXISTS idx_us_te_type ON trade_events(event_type);
CREATE INDEX IF NOT EXISTS idx_us_te_date ON trade_events((event_time::date));
"""


class USTradeStorage:
    """
    US 거래 저장소 — PostgreSQL + CSV 듀얼 라이트.

    - CSV TradeJournal과 동일한 동기 인터페이스 제공 (인메모리 캐시)
    - DB 쓰기는 asyncio.Queue → 백그라운드 writer 코루틴으로 비동기 처리
    - CSV 백업은 내부 TradeJournal 인스턴스에 위임
    """

    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv("DATABASE_URL_US", "")
        self.pool = None  # asyncpg.Pool
        self._db_available = False

        # CSV 백업 전담
        self._journal = TradeJournal()

        # 인메모리 캐시: trade_id → TradeRecord
        self._trades: Dict[str, TradeRecord] = {}
        self._today_trades: List[str] = []

        # DB 비동기 쓰기 큐
        self._write_queue: Optional[asyncio.Queue] = None
        self._writer_task: Optional[asyncio.Task] = None

    # ── 라이프사이클 ────────────────────────────────────

    async def connect(self):
        """DB 연결 + 스키마 생성 + writer 시작"""
        if not self.db_url:
            logger.warning("[TradeStorage] DATABASE_URL_US 미설정, CSV 전용 모드")
            return

        try:
            import asyncpg
            self.pool = await asyncpg.create_pool(
                self.db_url, min_size=1, max_size=5, command_timeout=30
            )
            await self._ensure_tables()
            self._db_available = True

            # writer 코루틴 시작
            self._write_queue = asyncio.Queue()
            self._writer_task = asyncio.create_task(self._db_writer())

            logger.info("[TradeStorage] DB 연결 완료, 듀얼 라이트 모드")
        except Exception as e:
            logger.error(f"[TradeStorage] DB 연결 실패, CSV 폴백: {e}")
            self._db_available = False

    async def disconnect(self):
        """큐 drain + DB 연결 종료"""
        if self._writer_task and not self._writer_task.done():
            if self._write_queue:
                await self._write_queue.put(None)  # sentinel
                try:
                    await asyncio.wait_for(self._writer_task, timeout=10)
                except asyncio.TimeoutError:
                    self._writer_task.cancel()
                    logger.warning("[TradeStorage] writer 타임아웃, 강제 종료")

        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("[TradeStorage] DB 연결 종료")

    async def _ensure_tables(self):
        """테이블 + 인덱스 생성"""
        async with self.pool.acquire() as conn:
            await conn.execute(SCHEMA_SQL)
        logger.info("[TradeStorage] 테이블 확인/생성 완료")

    @staticmethod
    def _refine_exit_type(exit_type: str, exit_reason: str) -> str:
        """exit_reason에 구체적 정보가 있으면 exit_type 세분화"""
        if not exit_reason:
            return exit_type
        r = exit_reason.lower()
        # take_profit → first/second/third 세분화
        if exit_type in ("take_profit", "unknown", ""):
            if "1차 익절" in r or "1차익절" in r or "first" in r:
                return "first_take_profit"
            if "2차 익절" in r or "2차익절" in r or "second" in r:
                return "second_take_profit"
            if "3차 익절" in r or "3차익절" in r or "third" in r:
                return "third_take_profit"
        # reason에서 추론 가능한데 exit_type이 unknown인 경우
        if exit_type == "unknown":
            if "손절" in r or "stop" in r:
                return "stop_loss"
            if "트레일링" in r or "trailing" in r:
                return "trailing"
            if "본전" in r or "breakeven" in r:
                return "breakeven"
            if "익절" in r or "profit" in r:
                return "take_profit"
        return exit_type

    # ── DB 비동기 Writer ───────────────────────────────

    async def _db_writer(self):
        """큐에서 (sql, params) 꺼내 순차 실행"""
        while True:
            item = await self._write_queue.get()
            if item is None:  # shutdown sentinel
                self._write_queue.task_done()
                break

            sql, params, retries_left = item
            try:
                async with self.pool.acquire() as conn:
                    await conn.execute(sql, *params)
            except Exception as e:
                sql_preview = sql.strip()[:50]
                if retries_left > 0:
                    await asyncio.sleep(1 * (4 - retries_left))
                    await self._write_queue.put((sql, params, retries_left - 1))
                    logger.warning(
                        f"[TradeStorage] DB 쓰기 재시도 ({retries_left}): "
                        f"{sql_preview}... → {e}"
                    )
                else:
                    logger.error(
                        f"[TradeStorage] DB 쓰기 최종 실패: {sql_preview}... → {e}"
                    )
            finally:
                self._write_queue.task_done()

    def _enqueue(self, sql: str, params: tuple):
        """DB 쓰기 큐에 추가 (동기 호출 가능)"""
        if not self._db_available or not self._write_queue:
            return
        try:
            self._write_queue.put_nowait((sql, params, 3))
        except Exception as e:
            logger.warning(f"[TradeStorage] 큐 추가 실패: {e}")

    # ── 거래 기록 (동기 인터페이스) ────────────────────

    def record_entry(
        self,
        trade_id: str,
        symbol: str,
        name: str,
        entry_price: float,
        entry_quantity: int,
        entry_reason: str,
        entry_strategy: str,
        signal_score: float = 0,
        exchange: str = "",
        kis_order_no: str = None,
        indicators: Dict[str, float] = None,
        market_context: Dict[str, Any] = None,
    ) -> TradeRecord:
        """진입 기록: 캐시 + CSV + DB큐"""
        now = _now_et()
        trade = TradeRecord(
            id=trade_id,
            symbol=symbol,
            name=name,
            exchange=exchange,
            entry_time=now,
            entry_price=entry_price,
            entry_quantity=entry_quantity,
            entry_reason=entry_reason,
            entry_strategy=entry_strategy,
            entry_signal_score=signal_score,
            kis_order_no=kis_order_no or "",
            indicators_at_entry=indicators or {},
            market_context=market_context or {},
            created_at=now,
            updated_at=now,
        )

        # 1) 인메모리 캐시
        self._trades[trade_id] = trade
        if trade_id not in self._today_trades:
            self._today_trades.append(trade_id)

        logger.info(
            f"[TradeStorage] 진입 기록: {symbol} {entry_quantity}주 "
            f"@ ${entry_price:.2f} (전략: {entry_strategy})"
        )

        # 2) DB 큐 — trades INSERT
        self._enqueue(
            """INSERT INTO trades
               (id, symbol, name, exchange, entry_time, entry_price, entry_quantity,
                entry_reason, entry_strategy, entry_signal_score,
                kis_order_no, market_context, indicators_at_entry,
                created_at, updated_at)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
               ON CONFLICT (id) DO NOTHING""",
            (
                trade.id, trade.symbol, trade.name, trade.exchange,
                trade.entry_time, trade.entry_price, trade.entry_quantity,
                trade.entry_reason, trade.entry_strategy, trade.entry_signal_score,
                trade.kis_order_no,
                json.dumps(trade.market_context, default=str, ensure_ascii=False),
                json.dumps(trade.indicators_at_entry, default=str, ensure_ascii=False),
                trade.created_at, trade.updated_at,
            ),
        )

        # 3) DB 큐 — trade_events BUY INSERT
        self._enqueue(
            """INSERT INTO trade_events
               (trade_id, symbol, name, event_type, event_time, price, quantity,
                strategy, signal_score, kis_order_no, status)
               VALUES ($1,$2,$3,'BUY',$4,$5,$6,$7,$8,$9,'holding')""",
            (
                trade.id, trade.symbol, trade.name,
                trade.entry_time, trade.entry_price, trade.entry_quantity,
                trade.entry_strategy, trade.entry_signal_score,
                trade.kis_order_no or "",
            ),
        )

        return trade

    def record_exit(
        self,
        trade_id: str,
        exit_price: float,
        exit_quantity: int,
        exit_reason: str,
        exit_type: str,
        indicators: Dict[str, float] = None,
        exit_time: datetime = None,
        avg_entry_price: float = None,
        kis_order_no: str = None,
    ) -> Optional[TradeRecord]:
        """청산 기록: 캐시 + DB큐"""
        # exit_type 세분화
        exit_type = self._refine_exit_type(exit_type, exit_reason)

        trade = self._trades.get(trade_id)
        if not trade:
            logger.warning(f"[TradeStorage] 캐시 미보유 trade_id: {trade_id}")
            return None

        now = exit_time or _now_et()

        # 누적 PnL 캡처 (이번 매도분 계산용)
        prev_pnl = trade.pnl

        # PnL 계산 (US: 수수료 $0, 단순 계산)
        entry_price = avg_entry_price or trade.entry_price
        # 이번 매도분 PnL
        this_sell_pnl = (exit_price - entry_price) * exit_quantity
        this_sell_pnl_pct = (
            (exit_price - entry_price) / entry_price * 100
            if entry_price > 0 else 0.0
        )

        # 누적 업데이트
        trade.exit_time = now
        trade.exit_price = exit_price
        trade.exit_quantity = (trade.exit_quantity or 0) + exit_quantity
        trade.exit_reason = exit_reason
        trade.exit_type = exit_type
        trade.pnl = prev_pnl + this_sell_pnl
        total_invested = trade.entry_price * trade.entry_quantity
        trade.pnl_pct = (
            trade.pnl / total_invested * 100
            if total_invested > 0 else 0.0
        )
        trade.holding_minutes = int((now - trade.entry_time).total_seconds() / 60) if trade.entry_time else 0
        trade.indicators_at_exit = indicators or {}
        trade.updated_at = now

        # 상태 결정
        is_fully_closed = trade.exit_quantity >= trade.entry_quantity
        status = exit_type if is_fully_closed else "partial"

        logger.info(
            f"[TradeStorage] 청산 기록: {trade.symbol} {exit_quantity}주 "
            f"@ ${exit_price:.2f} (PnL: ${this_sell_pnl:.2f}, {this_sell_pnl_pct:+.2f}%)"
        )

        # DB 큐 — trades UPSERT (부모 레코드 보장 + UPDATE)
        self._enqueue(
            """INSERT INTO trades
               (id, symbol, name, exchange, entry_time, entry_price, entry_quantity,
                entry_reason, entry_strategy, entry_signal_score,
                market_context, indicators_at_entry,
                created_at, updated_at)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
               ON CONFLICT (id) DO NOTHING""",
            (
                trade.id, trade.symbol, trade.name, trade.exchange,
                trade.entry_time, trade.entry_price, trade.entry_quantity,
                trade.entry_reason, trade.entry_strategy, trade.entry_signal_score,
                json.dumps(trade.market_context, default=str, ensure_ascii=False),
                json.dumps(trade.indicators_at_entry, default=str, ensure_ascii=False),
                trade.created_at, trade.updated_at,
            ),
        )
        self._enqueue(
            """UPDATE trades SET
               exit_time=$1, exit_price=$2, exit_quantity=$3,
               exit_reason=$4, exit_type=$5, pnl=$6, pnl_pct=$7,
               holding_minutes=$8, indicators_at_exit=$9, updated_at=$10
               WHERE id=$11""",
            (
                trade.exit_time, trade.exit_price, trade.exit_quantity,
                trade.exit_reason, trade.exit_type,
                round(trade.pnl, 4), round(trade.pnl_pct, 4),
                trade.holding_minutes,
                json.dumps(trade.indicators_at_exit, default=str, ensure_ascii=False),
                trade.updated_at, trade.id,
            ),
        )

        # DB 큐 — trade_events SELL INSERT
        self._enqueue(
            """INSERT INTO trade_events
               (trade_id, symbol, name, event_type, event_time, price, quantity,
                exit_type, exit_reason, pnl, pnl_pct, strategy, signal_score,
                kis_order_no, status)
               VALUES ($1,$2,$3,'SELL',$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
            (
                trade.id, trade.symbol, trade.name,
                trade.exit_time, exit_price, exit_quantity,
                exit_type, exit_reason,
                round(this_sell_pnl, 4), round(this_sell_pnl_pct, 4),
                trade.entry_strategy, trade.entry_signal_score,
                kis_order_no or "",
                status,
            ),
        )

        # 전량 청산 시 BUY 이벤트 상태 업데이트
        if is_fully_closed:
            self._enqueue(
                """UPDATE trade_events SET status=$1
                   WHERE trade_id=$2 AND event_type='BUY'""",
                (status, trade.id),
            )

        return trade

    # ── 조회 (캐시 우선, 동기) ─────────────────────────

    def get_trade(self, trade_id: str) -> Optional[TradeRecord]:
        return self._trades.get(trade_id)

    def get_today_trades(self) -> List[TradeRecord]:
        return [
            self._trades[tid] for tid in self._today_trades
            if tid in self._trades
        ]

    def get_open_trades(self) -> List[TradeRecord]:
        return [t for t in self._trades.values() if not t.is_closed]

    def get_closed_trades(self, days: int = 30) -> List[TradeRecord]:
        cutoff = _now_et() - timedelta(days=days)
        return [
            t for t in self._trades.values()
            if t.is_closed and t.entry_time and t.entry_time >= cutoff
        ]

    def get_recent_trades(self, days: int = 7) -> List[TradeRecord]:
        cutoff = _now_et() - timedelta(days=days)
        return [
            t for t in self._trades.values()
            if t.entry_time and t.entry_time >= cutoff
        ]

    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """캐시 기반 통계"""
        closed = self.get_closed_trades(days)
        if not closed:
            return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0, "total_pnl": 0}

        wins = [t for t in closed if t.pnl > 0]
        total_pnl = sum(t.pnl for t in closed)

        return {
            "total": len(closed),
            "wins": len(wins),
            "losses": len(closed) - len(wins),
            "win_rate": len(wins) / len(closed) * 100 if closed else 0,
            "total_pnl": round(total_pnl, 2),
        }

    # ── DB 전용 쿼리 (비동기) ─────────────────────────

    async def get_statistics_from_db(self, days: int = 30) -> Dict[str, Any]:
        """DB 기반 거래 통계 (캐시 폴백)"""
        if not self._db_available or not self.pool:
            return self.get_statistics(days)

        cutoff = _now_et() - timedelta(days=days)
        try:
            async with self.pool.acquire() as conn:
                # 기본 통계
                row = await conn.fetchrow("""
                    SELECT COUNT(*) as total,
                           COUNT(*) FILTER (WHERE pnl > 0) as wins,
                           COUNT(*) FILTER (WHERE pnl <= 0) as losses,
                           COALESCE(SUM(pnl), 0) as total_pnl,
                           COALESCE(AVG(pnl_pct), 0) as avg_pnl_pct,
                           COALESCE(AVG(holding_minutes), 0) as avg_holding
                    FROM trades
                    WHERE exit_time IS NOT NULL
                      AND entry_time >= $1
                """, cutoff)

                total = row['total']
                if total == 0:
                    return {
                        "total_trades": 0, "win_rate": 0, "avg_pnl_pct": 0,
                        "total_pnl": 0, "avg_holding_minutes": 0,
                        "best_trade": None, "worst_trade": None,
                        "by_strategy": {}, "by_exit_type": {},
                    }

                # 전략별
                strat_rows = await conn.fetch("""
                    SELECT entry_strategy, COUNT(*) as trades,
                           COUNT(*) FILTER (WHERE pnl > 0) as wins,
                           COALESCE(SUM(pnl), 0) as total_pnl,
                           COALESCE(AVG(pnl_pct), 0) as avg_pnl_pct
                    FROM trades
                    WHERE exit_time IS NOT NULL AND entry_time >= $1
                    GROUP BY entry_strategy
                """, cutoff)

                # 청산유형별
                exit_rows = await conn.fetch("""
                    SELECT exit_type, COUNT(*) as trades,
                           COUNT(*) FILTER (WHERE pnl > 0) as wins,
                           COALESCE(AVG(pnl_pct), 0) as avg_pnl_pct
                    FROM trades
                    WHERE exit_time IS NOT NULL AND entry_time >= $1
                    GROUP BY exit_type
                """, cutoff)

                # best/worst
                best = await conn.fetchrow("""
                    SELECT symbol, name, pnl_pct FROM trades
                    WHERE exit_time IS NOT NULL AND entry_time >= $1
                    ORDER BY pnl_pct DESC LIMIT 1
                """, cutoff)
                worst = await conn.fetchrow("""
                    SELECT symbol, name, pnl_pct FROM trades
                    WHERE exit_time IS NOT NULL AND entry_time >= $1
                    ORDER BY pnl_pct ASC LIMIT 1
                """, cutoff)

            by_strategy = {}
            for sr in strat_rows:
                key = sr['entry_strategy'] or 'unknown'
                trades_cnt = sr['trades']
                by_strategy[key] = {
                    "trades": trades_cnt,
                    "wins": sr['wins'],
                    "total_pnl": float(sr['total_pnl']),
                    "avg_pnl_pct": float(sr['avg_pnl_pct']),
                    "win_rate": sr['wins'] / trades_cnt * 100 if trades_cnt > 0 else 0,
                }

            by_exit_type = {}
            for er in exit_rows:
                key = er['exit_type'] or 'unknown'
                by_exit_type[key] = {
                    "trades": er['trades'],
                    "wins": er['wins'],
                    "avg_pnl_pct": float(er['avg_pnl_pct']),
                }

            best_dict = None
            if best:
                best_dict = {"symbol": best['symbol'], "name": best['name'],
                             "pnl_pct": float(best['pnl_pct'])}
            worst_dict = None
            if worst:
                worst_dict = {"symbol": worst['symbol'], "name": worst['name'],
                              "pnl_pct": float(worst['pnl_pct'])}

            return {
                "total_trades": total,
                "wins": row['wins'],
                "losses": row['losses'],
                "win_rate": row['wins'] / total * 100 if total > 0 else 0,
                "avg_pnl_pct": float(row['avg_pnl_pct']),
                "total_pnl": float(row['total_pnl']),
                "avg_holding_minutes": float(row['avg_holding']),
                "best_trade": best_dict,
                "worst_trade": worst_dict,
                "by_strategy": by_strategy,
                "by_exit_type": by_exit_type,
            }

        except Exception as e:
            logger.warning(f"[TradeStorage] DB 통계 조회 실패, 캐시 폴백: {e}")
            return self.get_statistics(days)

    async def get_trade_events(
        self,
        target_date: date = None,
        event_type: str = "all",
        limit: int = 200,
    ) -> List[Dict]:
        """trade_events 테이블에서 이벤트 로그 조회"""
        if not self._db_available:
            return self._get_events_from_cache(target_date, event_type)

        if target_date is None:
            target_date = _today_et()

        try:
            sql = """
                SELECT te.*, t.entry_price, t.entry_quantity
                FROM trade_events te
                JOIN trades t ON te.trade_id = t.id
                WHERE te.event_time::date = $1
            """
            params: list = [target_date]

            if event_type and event_type != "all":
                sql += " AND te.event_type = $2"
                params.append(event_type.upper())

            sql += " ORDER BY te.event_time DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)

            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, *params)

            return [self._row_to_event_dict(row) for row in rows]
        except Exception as e:
            logger.warning(f"[TradeStorage] trade_events 쿼리 실패, 캐시 폴백: {e}")
            return self._get_events_from_cache(target_date, event_type)

    def _row_to_event_dict(self, row) -> Dict:
        """asyncpg Row → dict 변환"""
        d = dict(row)
        for k, v in d.items():
            if isinstance(v, Decimal):
                d[k] = float(v)
            elif isinstance(v, datetime):
                d[k] = v.isoformat()
        return d

    def _get_events_from_cache(
        self, target_date: date = None, event_type: str = "all"
    ) -> List[Dict]:
        """DB 미사용 시 캐시 기반 이벤트 목록 구성"""
        if target_date is None:
            target_date = _today_et()

        events = []
        for trade in self._trades.values():
            if not trade.entry_time:
                continue

            # 진입 이벤트
            if trade.entry_time.date() == target_date:
                if event_type in ("all", "buy"):
                    exit_qty = trade.exit_quantity or 0
                    is_closed = exit_qty >= trade.entry_quantity
                    status = trade.exit_type if is_closed else "holding"
                    events.append({
                        "trade_id": trade.id,
                        "symbol": trade.symbol,
                        "name": trade.name,
                        "event_type": "BUY",
                        "event_time": trade.entry_time.isoformat(),
                        "price": trade.entry_price,
                        "quantity": trade.entry_quantity,
                        "strategy": trade.entry_strategy,
                        "signal_score": trade.entry_signal_score,
                        "status": status,
                    })

            # 청산 이벤트
            if trade.exit_time and trade.exit_time.date() == target_date:
                if event_type in ("all", "sell"):
                    events.append({
                        "trade_id": trade.id,
                        "symbol": trade.symbol,
                        "name": trade.name,
                        "event_type": "SELL",
                        "event_time": trade.exit_time.isoformat(),
                        "price": trade.exit_price,
                        "quantity": trade.exit_quantity or 0,
                        "exit_type": trade.exit_type,
                        "exit_reason": trade.exit_reason,
                        "pnl": trade.pnl,
                        "pnl_pct": trade.pnl_pct,
                        "strategy": trade.entry_strategy,
                        "signal_score": trade.entry_signal_score,
                        "status": trade.exit_type or "closed",
                    })

        events.sort(key=lambda e: e["event_time"], reverse=True)
        return events

    # ── KIS 동기화 ─────────────────────────────────────

    async def sync_from_kis(self, broker, engine=None):
        """KIS 당일 체결 내역과 캐시/DB 동기화

        봇 재시작 시 당일 체결 내역을 복구하여 캐시 일관성 유지.
        """
        try:
            today = _today_et()

            # KIS 당일 체결 내역 조회 (YYYYMMDD 문자열 전달)
            today_str = today.strftime("%Y%m%d")
            fills = await broker.get_order_history(today_str)
            if not fills:
                logger.info("[TradeStorage] KIS 당일 체결 없음")
                return

            # 종목별 매수/매도 분류
            buys: Dict[str, list] = {}
            sells: Dict[str, list] = {}
            for fill in fills:
                symbol = fill.get("symbol", "")
                if not symbol:
                    continue
                side = fill.get("side", "").lower()
                if side == "buy":
                    buys.setdefault(symbol, []).append(fill)
                elif side == "sell":
                    sells.setdefault(symbol, []).append(fill)

            # 캐시에 없는 매수 복구
            synced = 0
            for symbol, buy_fills in buys.items():
                # 이미 캐시에 있는지 확인
                has_cache = any(
                    t.symbol == symbol and t.entry_time and t.entry_time.date() == today
                    for t in self._trades.values()
                )
                if has_cache:
                    continue

                # 총 매수 수량/평균가
                total_qty = sum(f.get("qty", 0) for f in buy_fills)
                total_cost = sum(f.get("qty", 0) * f.get("price", 0) for f in buy_fills)
                if total_qty <= 0:
                    continue
                avg_price = total_cost / total_qty

                # 전략 복원
                strategy = ""
                if engine and hasattr(engine, '_symbol_strategy'):
                    strategy = engine._symbol_strategy.get(symbol, "")
                if not strategy and engine and hasattr(engine, 'portfolio'):
                    pos = engine.portfolio.positions.get(symbol)
                    if pos and pos.strategy:
                        strategy = pos.strategy

                trade_id = f"KIS_SYNC_{symbol}_{today.strftime('%Y%m%d')}"
                self.record_entry(
                    trade_id=trade_id,
                    symbol=symbol,
                    name=buy_fills[0].get("name", ""),
                    entry_price=avg_price,
                    entry_quantity=total_qty,
                    entry_reason="KIS 동기화 복원",
                    entry_strategy=strategy or "unknown",
                    exchange=buy_fills[0].get("exchange", "NASD"),
                )
                synced += 1

            # 캐시에 없는 매도 복구
            for symbol, sell_fills in sells.items():
                kis_sell_qty = sum(f.get("qty", 0) for f in sell_fills)
                # 캐시에서 이 종목의 매도 수량 합산
                cache_sell_qty = sum(
                    t.exit_quantity or 0
                    for t in self._trades.values()
                    if t.symbol == symbol and t.exit_time
                    and t.exit_time.date() == today
                )
                missing_qty = kis_sell_qty - cache_sell_qty
                if missing_qty <= 0:
                    continue

                # 복구 대상 찾기 (오늘 진입 미청산 우선)
                target = None
                for t in self._trades.values():
                    if t.symbol == symbol and not t.is_closed:
                        target = t
                        break

                if not target:
                    continue

                # 매도 평균가 계산
                total_sell_cost = sum(
                    f.get("qty", 0) * f.get("price", 0) for f in sell_fills
                )
                avg_sell_price = total_sell_cost / kis_sell_qty if kis_sell_qty > 0 else 0

                clamped_qty = min(missing_qty, target.entry_quantity - (target.exit_quantity or 0))
                if clamped_qty > 0:
                    self.record_exit(
                        trade_id=target.id,
                        exit_price=avg_sell_price,
                        exit_quantity=clamped_qty,
                        exit_reason="KIS 동기화 복원",
                        exit_type="kis_sync",
                    )
                    synced += 1

            if synced > 0:
                logger.info(f"[TradeStorage] KIS 동기화: {synced}건 복구 완료")

        except Exception as e:
            logger.warning(f"[TradeStorage] KIS 동기화 실패: {e}")

    # ── 복기 ──────────────────────────────────────────

    def update_review(
        self,
        trade_id: str,
        review_notes: str = "",
        lesson_learned: str = "",
        improvement_suggestion: str = "",
    ):
        """복기 노트 저장 (캐시 + DB)"""
        trade = self._trades.get(trade_id)
        if trade:
            trade.review_notes = review_notes
            trade.lesson_learned = lesson_learned
            trade.improvement_suggestion = improvement_suggestion
            trade.updated_at = _now_et()

        self._enqueue(
            """UPDATE trades SET review_notes=$1, lesson_learned=$2,
               improvement_suggestion=$3, updated_at=$4 WHERE id=$5""",
            (review_notes, lesson_learned, improvement_suggestion,
             _now_et(), trade_id),
        )
