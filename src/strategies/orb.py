"""
AI Trader US - Opening Range Breakout (ORB) Strategy

Trades breakout from first 30-minute range after market open.
Day trading strategy - all positions closed by EOD.
"""

from typing import Dict, Any, Optional
import pandas as pd
from loguru import logger

from .base import BaseStrategy
from ..core.types import Signal, Portfolio, StrategyType, TimeHorizon


class ORBStrategy(BaseStrategy):
    """Opening Range Breakout: first 30 min high/low breakout"""

    name = "orb"
    strategy_type = StrategyType.ORB
    time_horizon = TimeHorizon.DAY

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.or_period_minutes = self.config.get('or_period_minutes', 30)
        self.min_or_range_pct = self.config.get('min_or_range_pct', 0.5)
        self.max_or_range_pct = self.config.get('max_or_range_pct', 3.0)
        self.volume_confirm_ratio = self.config.get('volume_confirm_ratio', 1.5)
        self.stop_loss_pct = self.config.get('stop_loss_pct', 1.5)
        self.take_profit_r = self.config.get('take_profit_r', 2.0)

    def generate_signal(self, symbol: str, indicators: Dict[str, Any],
                        history: pd.DataFrame, portfolio: Portfolio) -> Optional[Signal]:
        """
        For daily backtesting: approximate ORB using daily OHLCV.
        On intraday data, this would use the actual 30-min opening range.

        Daily approximation:
        - Gap up from prev close = bullish OR breakout proxy
        - High volume day = confirmation
        - Close near high = breakout held
        """
        close = indicators.get('close', 0)
        if close <= 0:
            return None

        vol_ratio = indicators.get('vol_ratio', 0)
        rsi = indicators.get('rsi', 50)
        ma20 = indicators.get('ma20', 0)
        vwap = indicators.get('vwap', 0)
        change_1d = indicators.get('change_1d', 0)

        if len(history) < 2:
            return None

        # Current bar data
        today = history.iloc[-1]
        yesterday = history.iloc[-2]

        today_open = float(today['open'])
        today_high = float(today['high'])
        today_low = float(today['low'])
        today_close = float(today['close'])
        prev_close = float(yesterday['close'])

        if prev_close <= 0 or today_open <= 0:
            return None

        # Gap calculation
        gap_pct = (today_open - prev_close) / prev_close * 100

        # Day range
        day_range_pct = (today_high - today_low) / today_low * 100 if today_low > 0 else 0

        # Close position in range (0=low, 1=high)
        if today_high > today_low:
            close_position = (today_close - today_low) / (today_high - today_low)
        else:
            close_position = 0.5

        # --- Filters ---
        # Need meaningful day range
        if day_range_pct < self.min_or_range_pct:
            return None
        if day_range_pct > self.max_or_range_pct * 2:
            return None  # Too volatile

        # Volume confirmation
        if vol_ratio < self.volume_confirm_ratio:
            return None

        # Close should be near high (breakout held)
        if close_position < 0.6:
            return None

        # Positive day
        if change_1d < 0.3:
            return None

        # RSI not extreme
        if rsi > 80:
            return None

        # --- Score (0-100) ---
        score = 0

        # Volume confirmation (30 pts)
        score += min(30, vol_ratio * 6)

        # Gap direction alignment (25 pts)
        if gap_pct > 0:
            score += min(25, gap_pct * 5)
        else:
            score += max(0, 10 + gap_pct * 2)  # Mild penalty for gap down

        # Close position (near high = strong) (20 pts)
        score += close_position * 20

        # Trend alignment (15 pts)
        if ma20 > 0 and close > ma20:
            score += 8
        if vwap > 0 and close > vwap:
            score += 7

        # Day strength (10 pts)
        score += min(10, change_1d * 3)

        score = max(0, min(100, score))

        if score < self.min_score:
            return None

        # Stop/Target using day range as risk unit (R)
        risk = day_range_pct / 100 * close
        stop = close - risk * (self.stop_loss_pct / day_range_pct if day_range_pct > 0 else 0.015)
        target = close + risk * self.take_profit_r

        reason = (f"ORB breakout | gap {gap_pct:+.1f}% | "
                  f"range {day_range_pct:.1f}% | vol {vol_ratio:.1f}x")

        return self._create_signal(
            symbol=symbol, score=score, reason=reason,
            price=close, stop_price=stop, target_price=target,
        )
