"""
AI Trader US - Base Broker
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from decimal import Decimal

from ...core.types import Order, Fill, Position


class BaseBroker(ABC):
    """Abstract broker interface"""

    @abstractmethod
    async def submit_order(self, order: Order) -> Order:
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        pass

    @abstractmethod
    async def get_positions(self) -> List[Position]:
        pass

    @abstractmethod
    async def get_account_value(self) -> Decimal:
        pass
