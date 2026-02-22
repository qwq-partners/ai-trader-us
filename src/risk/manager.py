"""
AI Trader US - Risk Manager

Position sizing, daily loss limits, sector diversification.
Adapted from ai-trader-v2.
"""

from decimal import Decimal
from typing import Optional
from loguru import logger

from ..core.types import Portfolio, Signal, RiskConfig, RiskMetrics


class RiskManager:
    """Portfolio risk management"""

    def __init__(self, config: RiskConfig = None):
        self._config = config or RiskConfig()
        self._consecutive_losses = 0

    def can_open_position(self, portfolio: Portfolio, signal: Signal = None,
                          sector: str = None) -> bool:
        """Check if a new position can be opened"""
        # Daily loss limit
        if self._is_daily_loss_exceeded(portfolio):
            logger.warning("Daily loss limit reached")
            return False

        # Max positions
        if len(portfolio.positions) >= self._config.max_positions:
            logger.debug(f"Max positions reached ({self._config.max_positions})")
            return False

        # Min cash reserve
        min_cash = portfolio.total_equity * Decimal(str(self._config.min_cash_reserve_pct / 100))
        if portfolio.cash < min_cash:
            logger.debug("Below min cash reserve")
            return False

        # Sector limit
        if sector and self._config.max_positions_per_sector > 0:
            sector_count = sum(
                1 for p in portfolio.positions.values()
                if p.sector == sector
            )
            if sector_count >= self._config.max_positions_per_sector:
                logger.debug(f"Sector limit reached for {sector}")
                return False

        return True

    def calculate_position_size(self, portfolio: Portfolio,
                                price: Decimal) -> int:
        """Calculate position size in shares"""
        if price <= 0:
            return 0

        equity = portfolio.total_equity
        min_cash = equity * Decimal(str(self._config.min_cash_reserve_pct / 100))
        available = portfolio.cash - min_cash

        if available < Decimal(str(self._config.min_position_value)):
            return 0

        # Base position value
        base_value = equity * Decimal(str(self._config.base_position_pct / 100))
        max_value = equity * Decimal(str(self._config.max_position_pct / 100))

        position_value = min(base_value, available, max_value)

        # Consecutive loss reduction
        if self._consecutive_losses >= self._config.consecutive_loss_threshold:
            position_value *= Decimal(str(self._config.consecutive_loss_size_factor))
            logger.info(f"Size reduced by {self._config.consecutive_loss_size_factor}x "
                       f"(consecutive losses: {self._consecutive_losses})")

        quantity = int(position_value / price)
        return max(0, quantity)

    def record_trade_result(self, is_win: bool):
        """Track consecutive losses for adaptive sizing"""
        if is_win:
            self._consecutive_losses = 0
        else:
            self._consecutive_losses += 1

    def get_risk_metrics(self, portfolio: Portfolio) -> RiskMetrics:
        """Get current risk state"""
        daily_loss_pct = 0.0
        if portfolio.initial_capital > 0:
            daily_loss_pct = float(
                portfolio.effective_daily_pnl / portfolio.initial_capital * 100
            )

        return RiskMetrics(
            daily_loss=portfolio.effective_daily_pnl,
            daily_loss_pct=daily_loss_pct,
            daily_trades=portfolio.daily_trades,
            total_exposure=float(1 - portfolio.cash_ratio) * 100,
            is_daily_loss_limit_hit=self._is_daily_loss_exceeded(portfolio),
            can_trade=not self._is_daily_loss_exceeded(portfolio),
            consecutive_losses=self._consecutive_losses,
        )

    def _is_daily_loss_exceeded(self, portfolio: Portfolio) -> bool:
        if portfolio.initial_capital <= 0:
            return False
        loss_pct = float(
            portfolio.effective_daily_pnl / portfolio.initial_capital * 100
        )
        return loss_pct <= -self._config.daily_max_loss_pct
