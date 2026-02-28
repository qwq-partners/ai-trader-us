"""
AI Trader US - 일일 리포트

장 마감 후 텍스트 리포트 생성 + 텔레그램 전송.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from ..core.live_engine import LiveEngine


async def generate_daily_report(engine: LiveEngine) -> str:
    """일일 리포트 텍스트 생성"""
    portfolio = engine.portfolio
    metrics = engine.risk_manager.get_risk_metrics(portfolio)

    # 오늘 거래 내역
    todays_trades = engine.journal.get_todays_trades()
    wins = [t for t in todays_trades if float(t.get("pnl", 0)) > 0]
    losses = [t for t in todays_trades if float(t.get("pnl", 0)) < 0]
    total_pnl = sum(float(t.get("pnl", 0)) for t in todays_trades)

    lines = [
        f"[US] 일일 리포트 — {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "━━ 포트폴리오 요약 ━━",
        f"총자산: ${portfolio.total_equity:.2f}",
        f"현금: ${portfolio.cash:.2f}",
        f"포지션: {len(portfolio.positions)}개",
        f"일일 PnL: ${metrics.daily_loss:.2f} ({metrics.daily_loss_pct:+.1f}%)",
        "",
    ]

    # 거래 내역
    if todays_trades:
        lines.append(f"━━ 오늘 거래 ({len(todays_trades)}건) ━━")
        lines.append(f"승: {len(wins)} / 패: {len(losses)} / 실현 PnL: ${total_pnl:+.2f}")
        for t in todays_trades[:10]:  # 최대 10건
            symbol = t.get("symbol", "?")
            pnl = float(t.get("pnl", 0))
            reason = t.get("reason", "")
            lines.append(f"  {symbol}: ${pnl:+.2f} ({reason})")
        lines.append("")
    else:
        lines.append("━━ 오늘 거래 없음 ━━")
        lines.append("")

    # 보유 포지션
    if portfolio.positions:
        lines.append(f"━━ 보유 포지션 ({len(portfolio.positions)}개) ━━")
        for symbol, pos in sorted(portfolio.positions.items()):
            avg = float(pos.avg_price) if pos.avg_price else 0
            cur = float(pos.current_price) if pos.current_price else 0
            pnl_pct = ((cur - avg) / avg * 100) if avg > 0 else 0
            value = cur * pos.quantity
            lines.append(
                f"  {symbol}: {pos.quantity}주 @ ${avg:.2f} → ${cur:.2f} "
                f"({pnl_pct:+.1f}%) = ${value:.2f}"
            )
    else:
        lines.append("━━ 보유 포지션 없음 ━━")

    return "\n".join(lines)


async def send_daily_report(engine: LiveEngine) -> bool:
    """일일 리포트 생성 후 텔레그램 발송"""
    try:
        report = await generate_daily_report(engine)
        logger.info(f"[DailyReport] 리포트 생성 완료 ({len(report)}자)")

        from ..utils.telegram import get_notifier
        return await get_notifier().send_message(report, parse_mode="")
    except Exception as e:
        logger.error(f"[DailyReport] 리포트 발송 실패: {e}")
        return False
