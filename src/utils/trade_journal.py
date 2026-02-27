"""
AI Trader US - Trade Journal

CSV 기반 거래/주문 기록.

파일:
    data/journal/trades.csv  — 완료된 거래 (PnL)
    data/journal/orders.csv  — 주문 제출 기록
"""

from __future__ import annotations

import csv
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional

from loguru import logger

from ..core.types import TradeResult


TRADE_FIELDS = [
    "timestamp", "symbol", "side", "entry_price", "exit_price",
    "quantity", "pnl", "pnl_pct", "strategy", "reason",
    "entry_time", "exit_time", "holding_minutes", "commission",
]

ORDER_FIELDS = [
    "timestamp", "symbol", "side", "qty", "price", "order_type",
    "order_no", "strategy", "status", "message",
]


class TradeJournal:
    """CSV 거래 기록기"""

    def __init__(self, journal_dir: str = None):
        if journal_dir is None:
            journal_dir = Path(__file__).parent.parent.parent / "data" / "journal"
        self._dir = Path(journal_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

        self._trades_path = self._dir / "trades.csv"
        self._orders_path = self._dir / "orders.csv"

        self._ensure_headers()

    def _ensure_headers(self):
        """CSV 헤더가 없으면 생성"""
        if not self._trades_path.exists():
            self._write_header(self._trades_path, TRADE_FIELDS)
        if not self._orders_path.exists():
            self._write_header(self._orders_path, ORDER_FIELDS)

    @staticmethod
    def _write_header(path: Path, fields: list):
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(fields)

    def record_trade(self, trade: TradeResult):
        """완료된 거래 기록"""
        try:
            row = {
                "timestamp": datetime.now().isoformat(),
                "symbol": trade.symbol,
                "side": trade.side.value,
                "entry_price": f"{trade.entry_price:.4f}",
                "exit_price": f"{trade.exit_price:.4f}",
                "quantity": trade.quantity,
                "pnl": f"{trade.pnl:.2f}",
                "pnl_pct": f"{trade.pnl_pct:.2f}",
                "strategy": trade.strategy,
                "reason": trade.reason,
                "entry_time": trade.entry_time.isoformat() if trade.entry_time else "",
                "exit_time": trade.exit_time.isoformat() if trade.exit_time else "",
                "holding_minutes": f"{trade.holding_minutes:.0f}",
                "commission": f"{trade.commission:.4f}",
            }
            self._append_row(self._trades_path, TRADE_FIELDS, row)
            logger.debug(f"[Journal] Trade recorded: {trade.symbol} PnL={trade.pnl:.2f}")
        except Exception as e:
            logger.error(f"[Journal] Trade 기록 실패: {e}")

    def record_order(self, order_info: dict):
        """주문 제출 기록"""
        try:
            row = {
                "timestamp": datetime.now().isoformat(),
                "symbol": order_info.get("symbol", ""),
                "side": order_info.get("side", ""),
                "qty": order_info.get("qty", 0),
                "price": order_info.get("price", 0),
                "order_type": order_info.get("order_type", "market"),
                "order_no": order_info.get("order_no", ""),
                "strategy": order_info.get("strategy", ""),
                "status": order_info.get("status", ""),
                "message": order_info.get("message", ""),
            }
            self._append_row(self._orders_path, ORDER_FIELDS, row)
        except Exception as e:
            logger.error(f"[Journal] Order 기록 실패: {e}")

    @staticmethod
    def _append_row(path: Path, fields: list, row: dict):
        with open(path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writerow(row)

    def get_todays_trades(self) -> List[dict]:
        """오늘 거래 조회"""
        today_str = date.today().isoformat()
        return self._read_trades(lambda r: r.get("timestamp", "").startswith(today_str))

    def get_summary(self) -> dict:
        """전체 거래 요약"""
        trades = self._read_trades()
        if not trades:
            return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0, "total_pnl": 0}

        wins = [t for t in trades if float(t.get("pnl", 0)) > 0]
        total_pnl = sum(float(t.get("pnl", 0)) for t in trades)

        return {
            "total": len(trades),
            "wins": len(wins),
            "losses": len(trades) - len(wins),
            "win_rate": len(wins) / len(trades) * 100 if trades else 0,
            "total_pnl": round(total_pnl, 2),
        }

    def _read_trades(self, filter_fn=None) -> List[dict]:
        """CSV에서 거래 읽기"""
        if not self._trades_path.exists():
            return []
        try:
            with open(self._trades_path, 'r') as f:
                reader = csv.DictReader(f)
                trades = list(reader)
            if filter_fn:
                trades = [t for t in trades if filter_fn(t)]
            return trades
        except Exception as e:
            logger.error(f"[Journal] CSV 읽기 실패: {e}")
            return []
