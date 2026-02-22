"""
AI Trader US - Core Types

All domain objects and enums for US stock trading.
Adapted from ai-trader-v2 (Korean market) with USD/ticker changes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum, auto
from typing import Optional, Dict, Any, List
import uuid


# ============================================================
# Enums
# ============================================================

class Market(str, Enum):
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    AMEX = "AMEX"


class MarketSession(str, Enum):
    PRE_MARKET = "pre_market"       # 04:00-09:30 ET
    REGULAR = "regular"             # 09:30-16:00 ET
    AFTER_HOURS = "after_hours"     # 16:00-20:00 ET
    CLOSED = "closed"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PositionSide(str, Enum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class SignalStrength(str, Enum):
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    NORMAL = "normal"
    WEAK = "weak"


class StrategyType(str, Enum):
    ORB = "orb"                             # Opening Range Breakout
    MOMENTUM_BREAKOUT = "momentum_breakout"
    VWAP_BOUNCE = "vwap_bounce"
    SEPA_TREND = "sepa_trend"               # Minervini SEPA
    EARNINGS_DRIFT = "earnings_drift"       # Post-Earnings Drift


class TimeHorizon(str, Enum):
    DAY = "day"             # Intraday (close by EOD)
    SHORT_TERM = "short"    # 2-5 days
    SWING = "swing"         # 5-20 days


# ============================================================
# Data Classes
# ============================================================

@dataclass
class Price:
    """OHLCV price bar"""
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    value: Optional[Decimal] = None  # Dollar volume

    @property
    def typical_price(self) -> Decimal:
        return (self.high + self.low + self.close) / 3


@dataclass
class Quote:
    """Level 1 quote"""
    symbol: str
    timestamp: datetime
    bid_price: Decimal
    bid_size: int
    ask_price: Decimal
    ask_size: int

    @property
    def spread(self) -> Decimal:
        return self.ask_price - self.bid_price

    @property
    def mid_price(self) -> Decimal:
        return (self.bid_price + self.ask_price) / 2


@dataclass
class Order:
    """Trade order"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    order_type: OrderType = OrderType.LIMIT
    quantity: int = 0
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None

    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    filled_price: Optional[Decimal] = None

    strategy: Optional[str] = None
    reason: Optional[str] = None
    signal_score: Optional[float] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    broker_order_id: Optional[str] = None

    @property
    def is_active(self) -> bool:
        return self.status in (OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL)

    @property
    def remaining_quantity(self) -> int:
        return self.quantity - self.filled_quantity


@dataclass
class Fill:
    """Execution fill"""
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    price: Decimal
    commission: Decimal = Decimal("0")
    timestamp: datetime = field(default_factory=datetime.now)

    strategy: Optional[str] = None
    reason: Optional[str] = None
    signal_score: Optional[float] = None

    @property
    def total_value(self) -> Decimal:
        return self.price * self.quantity

    @property
    def total_cost(self) -> Decimal:
        return self.total_value + self.commission


@dataclass
class Position:
    """Portfolio position"""
    symbol: str
    name: str = ""
    side: PositionSide = PositionSide.FLAT
    quantity: int = 0
    avg_price: Decimal = Decimal("0")
    current_price: Decimal = Decimal("0")

    # Risk
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    trailing_stop_pct: Optional[float] = None
    highest_price: Optional[Decimal] = None

    # Metadata
    strategy: Optional[str] = None
    entry_time: Optional[datetime] = None
    sector: Optional[str] = None
    time_horizon: Optional[TimeHorizon] = None

    @property
    def market_value(self) -> Decimal:
        return self.current_price * self.quantity

    @property
    def cost_basis(self) -> Decimal:
        return self.avg_price * self.quantity

    @property
    def unrealized_pnl(self) -> Decimal:
        if self.quantity == 0:
            return Decimal("0")
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.cost_basis == 0:
            return 0.0
        return float(self.unrealized_pnl / self.cost_basis * 100)

    @property
    def is_profit(self) -> bool:
        return self.unrealized_pnl > 0


@dataclass
class Portfolio:
    """Trading portfolio"""
    cash: Decimal = Decimal("0")
    positions: Dict[str, Position] = field(default_factory=dict)
    initial_capital: Decimal = Decimal("0")

    daily_pnl: Decimal = Decimal("0")
    daily_trades: int = 0
    daily_start_unrealized_pnl: Decimal = Decimal("0")

    @property
    def total_position_value(self) -> Decimal:
        return sum(p.market_value for p in self.positions.values())

    @property
    def total_equity(self) -> Decimal:
        return self.cash + self.total_position_value

    @property
    def total_pnl(self) -> Decimal:
        return self.total_equity - self.initial_capital

    @property
    def total_pnl_pct(self) -> float:
        if self.initial_capital == 0:
            return 0.0
        return float(self.total_pnl / self.initial_capital * 100)

    @property
    def total_unrealized_pnl(self) -> Decimal:
        return sum(p.unrealized_pnl for p in self.positions.values())

    @property
    def effective_daily_pnl(self) -> Decimal:
        """Realized + today's unrealized change"""
        return self.daily_pnl + (self.total_unrealized_pnl - self.daily_start_unrealized_pnl)

    @property
    def cash_ratio(self) -> float:
        if self.total_equity == 0:
            return 1.0
        return float(self.cash / self.total_equity)

    def reset_daily(self):
        """Reset daily stats (call at market open)"""
        self.daily_pnl = Decimal("0")
        self.daily_trades = 0
        self.daily_start_unrealized_pnl = self.total_unrealized_pnl


@dataclass
class Signal:
    """Trading signal"""
    symbol: str
    side: OrderSide
    strength: SignalStrength
    strategy: StrategyType

    price: Optional[Decimal] = None
    target_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None

    score: float = 0.0
    confidence: float = 0.0

    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    @property
    def is_buy(self) -> bool:
        return self.side == OrderSide.BUY

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


@dataclass
class TradeResult:
    """Closed trade result"""
    symbol: str
    side: OrderSide
    entry_price: Decimal
    exit_price: Decimal
    quantity: int
    entry_time: datetime
    exit_time: datetime
    strategy: str
    reason: str = ""
    commission: Decimal = Decimal("0")

    @property
    def pnl(self) -> Decimal:
        gross = (self.exit_price - self.entry_price) * self.quantity
        return gross - self.commission

    @property
    def pnl_pct(self) -> float:
        if self.entry_price == 0:
            return 0.0
        return float((self.exit_price - self.entry_price) / self.entry_price * 100)

    @property
    def holding_minutes(self) -> float:
        return (self.exit_time - self.entry_time).total_seconds() / 60

    @property
    def is_win(self) -> bool:
        return self.pnl > 0


@dataclass
class RiskMetrics:
    """Current risk state"""
    daily_loss: Decimal = Decimal("0")
    daily_loss_pct: float = 0.0
    daily_trades: int = 0
    total_exposure: float = 0.0
    is_daily_loss_limit_hit: bool = False
    can_trade: bool = True
    consecutive_losses: int = 0


# ============================================================
# Config Types
# ============================================================

@dataclass
class RiskConfig:
    """Risk management configuration"""
    daily_max_loss_pct: float = 3.0
    max_positions: int = 10
    base_position_pct: float = 10.0
    max_position_pct: float = 15.0
    min_cash_reserve_pct: float = 10.0
    min_position_value: float = 1000.0      # $1,000
    max_positions_per_sector: int = 3

    default_stop_loss_pct: float = 3.0
    default_take_profit_pct: float = 6.0
    trailing_stop_pct: float = 2.0

    # Adaptive sizing
    consecutive_loss_threshold: int = 3
    consecutive_loss_size_factor: float = 0.5


@dataclass
class CommissionConfig:
    """Commission structure"""
    type: str = "zero"              # zero, per_share, percentage
    rate: float = 0.0               # $0.005/share or 0.1%
    min_commission: float = 0.0


@dataclass
class SlippageConfig:
    """Slippage model"""
    model: str = "percentage"       # fixed, percentage, volume_impact
    rate: float = 0.05              # 0.05%


@dataclass
class TradingConfig:
    """Main trading configuration"""
    initial_capital: Decimal = Decimal("100000")
    market: str = "US"

    commission: CommissionConfig = field(default_factory=CommissionConfig)
    slippage: SlippageConfig = field(default_factory=SlippageConfig)

    risk: RiskConfig = field(default_factory=RiskConfig)

    enable_pre_market: bool = False
    enable_after_hours: bool = False
