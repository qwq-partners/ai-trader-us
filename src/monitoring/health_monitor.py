"""
AI Trader US - 헬스 모니터링

장중에만 실행되는 3개 헬스 체크:
1. 하트비트 스톨 (10분 미응답)
2. 일일 손실 근접 (한도의 80%)
3. 브로커 연결 (타임아웃 10초)
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import TYPE_CHECKING, Dict, Optional

from loguru import logger

if TYPE_CHECKING:
    from ..core.live_engine import LiveEngine


# 알림 쿨다운: 동일 체크 반복 방지 (5분)
_ALERT_COOLDOWN_SEC = 300


class HealthMonitor:
    """US 봇 헬스 모니터"""

    def __init__(self, engine: LiveEngine):
        self._engine = engine
        self._last_heartbeat = time.time()
        self._alert_cooldown: Dict[str, float] = {}  # check_name -> last_alert_ts

    def touch_heartbeat(self):
        """하트비트 갱신 (heartbeat_loop에서 호출)"""
        self._last_heartbeat = time.time()

    async def check_all(self) -> list[str]:
        """모든 헬스 체크 실행. 이상 항목 리스트 반환."""
        issues: list[str] = []

        # 장중에만 실행
        if not self._engine.session.is_market_open():
            return issues

        # 1. 하트비트 스톨 (10분)
        elapsed = time.time() - self._last_heartbeat
        if elapsed > 600:
            msg = f"하트비트 스톨: {elapsed:.0f}초 미응답"
            issues.append(msg)
            await self._alert("heartbeat_stall", msg)

        # 2. 일일 손실 근접 (한도의 80%)
        try:
            metrics = self._engine.risk_manager.get_risk_metrics(self._engine.portfolio)
            # RiskConfig에서 daily_loss_limit_pct 가져오기 (기본값 3%)
            limit_pct = getattr(self._engine.risk_manager._config, 'daily_max_loss_pct', 3.0)
            threshold = limit_pct * 0.8  # 80%
            if metrics.daily_loss_pct <= -threshold:
                msg = f"일일 손실 한도 근접: {metrics.daily_loss_pct:.1f}% (한도: -{limit_pct}%)"
                issues.append(msg)
                await self._alert("daily_loss_near", msg)
        except Exception as e:
            logger.debug(f"[HealthMonitor] 손실 체크 실패: {e}")

        # 3. 브로커 연결
        try:
            balance = await self._engine.broker.get_balance()
            if not balance:
                msg = "브로커 연결 실패: get_balance() 응답 없음"
                issues.append(msg)
                await self._alert("broker_conn", msg)
        except Exception as e:
            msg = f"브로커 연결 실패: {e}"
            issues.append(msg)
            await self._alert("broker_conn", msg)

        return issues

    async def _alert(self, check_name: str, message: str):
        """알림 발송 (쿨다운 적용)"""
        now = time.time()
        last = self._alert_cooldown.get(check_name, 0)
        if now - last < _ALERT_COOLDOWN_SEC:
            return

        self._alert_cooldown[check_name] = now

        try:
            from ..utils.telegram import get_notifier
            await get_notifier().send_alert(f"[US] 헬스 경고\n{message}")
        except Exception as e:
            logger.error(f"[HealthMonitor] 알림 발송 실패: {e}")
