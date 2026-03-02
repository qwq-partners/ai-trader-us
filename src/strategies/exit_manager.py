"""
AI Trader US - Exit Manager

Multi-stage partial profit taking + dynamic stop loss.
Adapted from ai-trader-v2.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, Dict
from loguru import logger

from ..core.types import Position


@dataclass
class ExitConfig:
    """Exit configuration per position"""
    # Partial exits
    first_exit_pct: float = 3.0
    first_exit_ratio: float = 0.40

    second_exit_pct: float = 6.0
    second_exit_ratio: float = 0.50

    third_exit_pct: float = 10.0
    third_exit_ratio: float = 0.50
    # 참고: 3단계 분할매도 합계 = 약 85%.
    # 나머지 ~15%는 trailing_stop 또는 stop_loss로 최종 청산됨.
    # $700 소자본 시 대부분 1주 → 분할매도 스킵, trailing_stop이 전량 청산.

    # Stop loss
    stop_loss_pct: float = 3.0
    trailing_stop_pct: float = 2.0
    trailing_activate_pct: float = 3.0

    # Dynamic stop (ATR-based)
    enable_dynamic_stop: bool = True
    atr_multiplier: float = 2.0
    min_stop_pct: float = 2.0
    max_stop_pct: float = 6.0

    # Day trade EOD close
    eod_close: bool = False


class ExitManager:
    """Manages exits with partial profit-taking and trailing stops"""

    def __init__(self, config: dict = None):
        self._config = config or {}
        self._default = ExitConfig(
            first_exit_pct=self._config.get('first_exit_pct', 3.0),
            first_exit_ratio=self._config.get('first_exit_ratio', 0.40),
            second_exit_pct=self._config.get('second_exit_pct', 6.0),
            second_exit_ratio=self._config.get('second_exit_ratio', 0.50),
            third_exit_pct=self._config.get('third_exit_pct', 10.0),
            third_exit_ratio=self._config.get('third_exit_ratio', 0.50),
            stop_loss_pct=self._config.get('stop_loss_pct', 3.0),
            trailing_stop_pct=self._config.get('trailing_stop_pct', 2.0),
            trailing_activate_pct=self._config.get('trailing_activate_pct', 3.0),
            enable_dynamic_stop=self._config.get('enable_dynamic_stop', True),
            atr_multiplier=self._config.get('atr_multiplier', 2.0),
            min_stop_pct=self._config.get('min_stop_pct', 2.0),
            max_stop_pct=self._config.get('max_stop_pct', 6.0),
            eod_close=self._config.get('eod_close', False),
        )

        # Track partial exit state per symbol
        self._exit_stages: Dict[str, int] = {}  # symbol -> stage completed (0,1,2,3)

    def get_exit_config(self, position: Position) -> ExitConfig:
        """Get exit config (can be customized per strategy)"""
        return self._default

    def check_exit(self, position: Position, current_price: float,
                   atr: float = None) -> Optional[Dict]:
        """
        Check if position should be (partially) exited.

        Returns:
            {'action': 'close'|'partial', 'ratio': 0.4, 'reason': '...'} or None
        """
        if position.quantity <= 0:
            return None

        cfg = self.get_exit_config(position)
        avg_price = float(position.avg_price)
        if avg_price <= 0:
            return None

        pnl_pct = (current_price - avg_price) / avg_price * 100
        symbol = position.symbol
        stage = self._exit_stages.get(symbol, 0)

        # --- Stop loss ---
        stop_pct = cfg.stop_loss_pct

        # Dynamic ATR-based stop
        if cfg.enable_dynamic_stop and atr is not None and atr > 0 and avg_price > 0:
            atr_stop = atr * cfg.atr_multiplier / avg_price * 100
            stop_pct = max(cfg.min_stop_pct, min(atr_stop, cfg.max_stop_pct))

        if pnl_pct <= -stop_pct:
            self._exit_stages.pop(symbol, None)
            return {'action': 'close', 'ratio': 1.0, 'reason': f'stop_loss ({pnl_pct:.1f}%)'}

        # --- Trailing stop ---
        if position.highest_price is not None and pnl_pct >= cfg.trailing_activate_pct:
            trail_from_high = (float(position.highest_price) - current_price) / float(position.highest_price) * 100
            if trail_from_high >= cfg.trailing_stop_pct:
                self._exit_stages.pop(symbol, None)
                return {'action': 'close', 'ratio': 1.0,
                        'reason': f'trailing_stop (from high: -{trail_from_high:.1f}%)'}

        # --- Partial exits ---
        # 1주 보유 시 분할매도 불가 → stage 진행 않고 trailing_stop에 위임
        qty = position.quantity
        if stage < 1 and pnl_pct >= cfg.first_exit_pct:
            sell_qty = int(qty * cfg.first_exit_ratio)
            if sell_qty >= 1:
                self._exit_stages[symbol] = 1
                return {'action': 'partial', 'ratio': cfg.first_exit_ratio,
                        'reason': f'first_exit (+{pnl_pct:.1f}%)'}
            # 분할매도 불가 → trailing_stop 활성화 대기 (stage 유지)

        if stage < 2 and pnl_pct >= cfg.second_exit_pct:
            sell_qty = int(qty * cfg.second_exit_ratio)
            if sell_qty >= 1:
                self._exit_stages[symbol] = 2
                return {'action': 'partial', 'ratio': cfg.second_exit_ratio,
                        'reason': f'second_exit (+{pnl_pct:.1f}%)'}

        if stage < 3 and pnl_pct >= cfg.third_exit_pct:
            sell_qty = int(qty * cfg.third_exit_ratio)
            if sell_qty >= 1:
                self._exit_stages[symbol] = 3
                return {'action': 'partial', 'ratio': cfg.third_exit_ratio,
                        'reason': f'third_exit (+{pnl_pct:.1f}%)'}

        return None

    def on_position_closed(self, symbol: str):
        """Clean up when position is fully closed"""
        self._exit_stages.pop(symbol, None)

    def get_stages(self) -> Dict[str, int]:
        """영속화용 스테이지 상태 반환"""
        return dict(self._exit_stages)

    def restore_stages(self, stages: Dict[str, int]):
        """재시작 시 스테이지 복원"""
        self._exit_stages.update(stages)
