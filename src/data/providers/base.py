"""
AI Trader US - Data Provider Base
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional, Dict
import pandas as pd


class DataProvider(ABC):
    """Abstract data provider interface"""

    @abstractmethod
    def get_daily_bars(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        """Get daily OHLCV bars. Returns DataFrame with columns: open, high, low, close, volume"""
        pass

    @abstractmethod
    def get_intraday_bars(self, symbol: str, interval: str = "5m",
                          period: str = "60d") -> pd.DataFrame:
        """Get intraday bars. interval: 1m, 5m, 15m, 1h"""
        pass

    @abstractmethod
    def get_quote(self, symbol: str) -> Dict:
        """Get current quote"""
        pass

    @abstractmethod
    def get_universe(self, index: str = "sp500") -> List[str]:
        """Get list of tickers for an index"""
        pass
