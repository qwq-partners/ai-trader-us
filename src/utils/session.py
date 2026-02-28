"""
AI Trader US - Market Session Utilities

US market hours in Eastern Time (ET).
Regular: 09:30-16:00 ET
Pre-market: 04:00-09:30 ET
After-hours: 16:00-20:00 ET
"""

from datetime import datetime, time, date
from typing import Optional
from zoneinfo import ZoneInfo

from .calendar import USMarketCalendar
from ..core.types import MarketSession

ET = ZoneInfo("America/New_York")
KST = ZoneInfo("Asia/Seoul")

# Regular session times
REGULAR_OPEN = time(9, 30)
REGULAR_CLOSE = time(16, 0)
PRE_MARKET_OPEN = time(4, 0)
AFTER_HOURS_CLOSE = time(20, 0)


class USSession:
    """US market session manager"""

    def __init__(self):
        self._calendar = USMarketCalendar()

    def now_et(self) -> datetime:
        """Current time in ET"""
        return datetime.now(ET)

    def now_kst(self) -> datetime:
        """Current time in KST"""
        return datetime.now(KST)

    def get_session(self, dt: Optional[datetime] = None) -> MarketSession:
        """Get current market session"""
        if dt is None:
            dt = self.now_et()
        elif dt.tzinfo is None:
            dt = dt.replace(tzinfo=ET)

        t = dt.time()
        d = dt.date()

        if not self._calendar.is_trading_day(d):
            return MarketSession.CLOSED

        if REGULAR_OPEN <= t < REGULAR_CLOSE:
            return MarketSession.REGULAR
        elif PRE_MARKET_OPEN <= t < REGULAR_OPEN:
            return MarketSession.PRE_MARKET
        elif REGULAR_CLOSE <= t < AFTER_HOURS_CLOSE:
            return MarketSession.AFTER_HOURS
        else:
            return MarketSession.CLOSED

    def is_market_open(self, dt: Optional[datetime] = None) -> bool:
        """Is regular session open?"""
        return self.get_session(dt) == MarketSession.REGULAR

    def minutes_to_close(self, dt: Optional[datetime] = None) -> float:
        """Minutes until regular session close"""
        if dt is None:
            dt = self.now_et()
        close_dt = dt.replace(hour=16, minute=0, second=0, microsecond=0)
        diff = (close_dt - dt).total_seconds() / 60
        return max(0.0, diff)

    def is_trading_day(self, d: Optional[date] = None) -> bool:
        """Is today a trading day? (NYSE 기준)"""
        if d is None:
            d = self.now_et().date()
        return self._calendar.is_trading_day(d)

    def next_trading_day(self, d: Optional[date] = None) -> date:
        """Next NYSE trading day"""
        if d is None:
            d = self.now_et().date()
        return self._calendar.next_trading_day(d)

    def prev_trading_day(self, d: Optional[date] = None) -> date:
        """Previous NYSE trading day"""
        if d is None:
            d = self.now_et().date()
        return self._calendar.prev_trading_day(d)
