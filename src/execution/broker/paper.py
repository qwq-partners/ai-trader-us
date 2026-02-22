"""
AI Trader US - Paper Broker (Simulator)

Simulates order execution for backtesting.
Supports slippage and commission modeling.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Callable
from loguru import logger

from ...core.types import (
    Order, Fill, Position, OrderSide, OrderStatus, OrderType,
    CommissionConfig, SlippageConfig
)


class PaperBroker:
    """Paper trading broker for backtesting"""

    def __init__(
        self,
        commission: CommissionConfig = None,
        slippage: SlippageConfig = None,
    ):
        self._commission = commission or CommissionConfig()
        self._slippage = slippage or SlippageConfig()
        self._fills: List[Fill] = []

    def execute_order(self, order: Order, market_price: Decimal,
                      timestamp: datetime = None) -> Optional[Fill]:
        """Execute order at market price with slippage and commission"""
        if order.quantity <= 0:
            return None

        # Apply slippage
        fill_price = self._apply_slippage(market_price, order.side)

        # Calculate commission
        commission = self._calculate_commission(fill_price, order.quantity)

        # Create fill
        fill = Fill(
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            commission=commission,
            timestamp=timestamp or datetime.now(),
            strategy=order.strategy,
            reason=order.reason,
            signal_score=order.signal_score,
        )

        # Update order status
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.filled_price = fill_price
        order.updated_at = fill.timestamp

        self._fills.append(fill)

        logger.debug(
            f"FILL: {order.side.value} {order.quantity} {order.symbol} "
            f"@ ${fill_price:.2f} (slip: ${fill_price - market_price:.4f}, "
            f"comm: ${commission:.2f})"
        )

        return fill

    def _apply_slippage(self, price: Decimal, side: OrderSide) -> Decimal:
        """Apply slippage model"""
        if self._slippage.model == "percentage":
            slip_pct = Decimal(str(self._slippage.rate / 100))
            if side == OrderSide.BUY:
                return price * (1 + slip_pct)
            else:
                return price * (1 - slip_pct)
        elif self._slippage.model == "fixed":
            slip = Decimal(str(self._slippage.rate))
            if side == OrderSide.BUY:
                return price + slip
            else:
                return price - slip
        return price

    def _calculate_commission(self, price: Decimal, quantity: int) -> Decimal:
        """Calculate commission"""
        if self._commission.type == "zero":
            return Decimal("0")
        elif self._commission.type == "per_share":
            comm = Decimal(str(self._commission.rate)) * quantity
            min_comm = Decimal(str(self._commission.min_commission))
            return max(comm, min_comm)
        elif self._commission.type == "percentage":
            return price * quantity * Decimal(str(self._commission.rate / 100))
        return Decimal("0")

    @property
    def fills(self) -> List[Fill]:
        return self._fills

    def reset(self):
        self._fills.clear()
