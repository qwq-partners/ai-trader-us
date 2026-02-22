"""
AI Trader US - Event System

Event-driven architecture core. Ported from ai-trader-v2.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum, auto
from typing import Optional, Dict, Any, List
import uuid

from .types import (
    Order, Fill, Position, Signal, Price, Quote,
    OrderSide, OrderStatus, SignalStrength, StrategyType, MarketSession
)


class EventType(Enum):
    # Market data
    MARKET_DATA = auto()
    QUOTE = auto()
    TICK = auto()

    # Trading
    SIGNAL = auto()
    ORDER = auto()
    FILL = auto()
    POSITION = auto()

    # Risk
    RISK_ALERT = auto()
    STOP_TRIGGERED = auto()

    # System
    HEARTBEAT = auto()
    SESSION = auto()
    ERROR = auto()


@dataclass
class Event:
    """Base event"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    type: EventType = EventType.HEARTBEAT
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    priority: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other):
        if not isinstance(other, Event):
            return NotImplemented
        if self.priority == other.priority:
            return self.timestamp < other.timestamp
        return self.priority < other.priority


# ============================================================
# Market Data Events
# ============================================================

@dataclass
class MarketDataEvent(Event):
    """OHLCV market data"""
    type: EventType = EventType.MARKET_DATA

    symbol: str = ""
    open: Decimal = Decimal("0")
    high: Decimal = Decimal("0")
    low: Decimal = Decimal("0")
    close: Decimal = Decimal("0")
    volume: int = 0
    value: Decimal = Decimal("0")

    prev_close: Optional[Decimal] = None
    change: Decimal = Decimal("0")
    change_pct: float = 0.0

    def to_price(self) -> Price:
        return Price(
            symbol=self.symbol, timestamp=self.timestamp,
            open=self.open, high=self.high, low=self.low,
            close=self.close, volume=self.volume, value=self.value
        )


@dataclass
class QuoteEvent(Event):
    """Level 1 quote"""
    type: EventType = EventType.QUOTE
    priority: int = 2

    symbol: str = ""
    bid_price: Decimal = Decimal("0")
    bid_size: int = 0
    ask_price: Decimal = Decimal("0")
    ask_size: int = 0

    @property
    def spread(self) -> Decimal:
        return self.ask_price - self.bid_price

    @property
    def mid_price(self) -> Decimal:
        return (self.bid_price + self.ask_price) / 2


# ============================================================
# Trading Events
# ============================================================

@dataclass
class SignalEvent(Event):
    """Trading signal event"""
    type: EventType = EventType.SIGNAL
    priority: int = 3

    signal: Optional[Signal] = None

    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    strength: SignalStrength = SignalStrength.NORMAL
    strategy: StrategyType = StrategyType.MOMENTUM_BREAKOUT

    price: Optional[Decimal] = None
    target_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None

    score: float = 0.0
    confidence: float = 0.0
    reason: str = ""

    @classmethod
    def from_signal(cls, signal: Signal, source: str = "") -> "SignalEvent":
        return cls(
            source=source, signal=signal,
            symbol=signal.symbol, side=signal.side,
            strength=signal.strength, strategy=signal.strategy,
            price=signal.price, target_price=signal.target_price,
            stop_price=signal.stop_price, score=signal.score,
            confidence=signal.confidence, reason=signal.reason,
            metadata=dict(signal.metadata) if signal.metadata else {}
        )


@dataclass
class OrderEvent(Event):
    """Order event"""
    type: EventType = EventType.ORDER
    priority: int = 1

    order: Optional[Order] = None

    order_id: str = ""
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    quantity: int = 0
    price: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.PENDING

    @classmethod
    def from_order(cls, order: Order, source: str = "") -> "OrderEvent":
        return cls(
            source=source, order=order, order_id=order.id,
            symbol=order.symbol, side=order.side,
            quantity=order.quantity, price=order.price,
            status=order.status
        )


@dataclass
class FillEvent(Event):
    """Fill/execution event"""
    type: EventType = EventType.FILL
    priority: int = 1

    fill: Optional[Fill] = None

    order_id: str = ""
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    quantity: int = 0
    price: Decimal = Decimal("0")
    commission: Decimal = Decimal("0")

    @classmethod
    def from_fill(cls, fill: Fill, source: str = "") -> "FillEvent":
        return cls(
            source=source, fill=fill, order_id=fill.order_id,
            symbol=fill.symbol, side=fill.side,
            quantity=fill.quantity, price=fill.price,
            commission=fill.commission
        )


@dataclass
class PositionEvent(Event):
    """Position change event"""
    type: EventType = EventType.POSITION
    priority: int = 3

    position: Optional[Position] = None
    action: str = ""  # opened, closed, increased, decreased

    symbol: str = ""
    quantity_change: int = 0
    pnl: Optional[Decimal] = None


# ============================================================
# Risk Events
# ============================================================

@dataclass
class RiskAlertEvent(Event):
    """Risk alert"""
    type: EventType = EventType.RISK_ALERT
    priority: int = 1

    alert_type: str = ""
    message: str = ""
    current_value: float = 0.0
    threshold: float = 0.0
    action: str = ""  # warn, block, liquidate

    @property
    def is_critical(self) -> bool:
        return self.action in ("block", "liquidate")


@dataclass
class StopTriggeredEvent(Event):
    """Stop loss / take profit trigger"""
    type: EventType = EventType.STOP_TRIGGERED
    priority: int = 1

    symbol: str = ""
    trigger_type: str = ""  # stop_loss, take_profit, trailing_stop
    trigger_price: Decimal = Decimal("0")
    current_price: Decimal = Decimal("0")


# ============================================================
# System Events
# ============================================================

@dataclass
class SessionEvent(Event):
    """Market session change"""
    type: EventType = EventType.SESSION
    priority: int = 2

    session: MarketSession = MarketSession.CLOSED
    prev_session: Optional[MarketSession] = None


@dataclass
class HeartbeatEvent(Event):
    """Heartbeat"""
    type: EventType = EventType.HEARTBEAT
    priority: int = 10

    uptime_seconds: float = 0.0
    active_positions: int = 0
    pending_orders: int = 0


@dataclass
class ErrorEvent(Event):
    """Error event"""
    type: EventType = EventType.ERROR
    priority: int = 1

    error_type: str = ""
    message: str = ""
    traceback: str = ""
    recoverable: bool = True
