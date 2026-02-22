"""
AI Trader US - Market Calendar

US stock market holidays and trading days.
Uses exchange-calendars package for accuracy.
"""

from datetime import date, timedelta
from typing import List, Optional

from loguru import logger


class USMarketCalendar:
    """US market calendar using exchange-calendars"""

    def __init__(self):
        self._cal = None
        self._init_calendar()

    def _init_calendar(self):
        try:
            import exchange_calendars as xcals
            self._cal = xcals.get_calendar("XNYS")  # NYSE calendar
            logger.debug("Exchange calendar loaded (XNYS)")
        except ImportError:
            logger.warning("exchange-calendars not installed, using basic weekend check")

    def is_trading_day(self, d: Optional[date] = None) -> bool:
        """Check if date is a trading day"""
        if d is None:
            d = date.today()

        # Weekend check (always)
        if d.weekday() >= 5:
            return False

        # Exchange calendar (if available)
        if self._cal is not None:
            try:
                import pandas as pd
                ts = pd.Timestamp(d)
                return self._cal.is_session(ts)
            except Exception:
                pass

        return True  # Assume trading day if no calendar

    def next_trading_day(self, d: Optional[date] = None) -> date:
        """Get next trading day"""
        if d is None:
            d = date.today()

        candidate = d + timedelta(days=1)
        while not self.is_trading_day(candidate):
            candidate += timedelta(days=1)
        return candidate

    def prev_trading_day(self, d: Optional[date] = None) -> date:
        """Get previous trading day"""
        if d is None:
            d = date.today()

        candidate = d - timedelta(days=1)
        while not self.is_trading_day(candidate):
            candidate -= timedelta(days=1)
        return candidate

    def trading_days_between(self, start: date, end: date) -> List[date]:
        """Get list of trading days in range"""
        days = []
        current = start
        while current <= end:
            if self.is_trading_day(current):
                days.append(current)
            current += timedelta(days=1)
        return days
