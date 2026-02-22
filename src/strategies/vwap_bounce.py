"""
AI Trader US - VWAP Reclaim/Bounce Strategy

Buy when price reclaims VWAP from below with volume confirmation.
Day trading strategy.
"""

from typing import Dict, Any, Optional
import pandas as pd

from .base import BaseStrategy
from ..core.types import Signal, Portfolio, StrategyType, TimeHorizon


class VWAPBounceStrategy(BaseStrategy):
    """VWAP Reclaim: price crosses above VWAP with volume"""

    name = "vwap_bounce"
    strategy_type = StrategyType.VWAP_BOUNCE
    time_horizon = TimeHorizon.DAY

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.min_volume_ratio = self.config.get('min_volume_ratio', 1.5)
        self.reclaim_confirm_bars = self.config.get('reclaim_confirm_bars', 3)
        self.stop_loss_atr_mult = self.config.get('stop_loss_atr_mult', 0.5)
        self.take_profit_atr_mult = self.config.get('take_profit_atr_mult', 1.5)

    def generate_signal(self, symbol: str, indicators: Dict[str, Any],
                        history: pd.DataFrame, portfolio: Portfolio) -> Optional[Signal]:
        """
        Daily approximation of VWAP bounce:
        - Close > VWAP (reclaim)
        - Previous bars were below VWAP (dip)
        - Volume above average
        - RSI in neutral zone (40-60)
        """
        close = indicators.get('close', 0)
        vwap = indicators.get('vwap', 0)
        vol_ratio = indicators.get('vol_ratio', 0)
        rsi = indicators.get('rsi', 50)
        atr = indicators.get('atr', 0)
        ma20 = indicators.get('ma20', 0)
        change_1d = indicators.get('change_1d', 0)

        if close <= 0 or vwap <= 0:
            return None

        if len(history) < self.reclaim_confirm_bars + 5:
            return None

        # --- VWAP Reclaim Detection ---
        # Current: above VWAP
        if close <= vwap:
            return None

        # Recent bars: at least some were below VWAP
        from ..indicators.technical import vwap as calc_vwap
        recent_vwaps = calc_vwap(
            history['high'], history['low'], history['close'],
            history['volume'], period=20
        )

        if recent_vwaps.empty or len(recent_vwaps) < self.reclaim_confirm_bars + 2:
            return None

        # Check if N bars ago was below VWAP (the dip)
        bars_below = 0
        for i in range(-self.reclaim_confirm_bars - 2, -1):
            if (len(history) + i >= 0 and len(recent_vwaps) + i >= 0):
                bar_close = float(history['close'].iloc[i])
                bar_vwap = float(recent_vwaps.iloc[i])
                if bar_close < bar_vwap:
                    bars_below += 1

        if bars_below < 1:
            return None  # No dip below VWAP

        # --- Filters ---
        if vol_ratio < self.min_volume_ratio:
            return None

        # RSI neutral zone (not overbought/oversold)
        if rsi < 35 or rsi > 70:
            return None

        # --- Score (0-100) ---
        score = 0

        # VWAP reclaim strength (30 pts)
        reclaim_dist = (close - vwap) / vwap * 100
        score += min(30, reclaim_dist * 15)

        # Volume confirmation (25 pts)
        score += min(25, vol_ratio * 5)

        # Trend alignment (20 pts)
        if ma20 > 0 and close > ma20:
            score += 12
        if change_1d > 0:
            score += min(8, change_1d * 4)

        # RSI position - prefer middle range (15 pts)
        rsi_dist_from_50 = abs(rsi - 50)
        score += max(0, 15 - rsi_dist_from_50 * 0.5)

        # Dip depth (10 pts) - deeper dip = stronger signal
        score += min(10, bars_below * 3)

        score = max(0, min(100, score))

        if score < self.min_score:
            return None

        # Stop/Target using ATR
        stop = close - atr * self.stop_loss_atr_mult if atr > 0 else close * 0.98
        target = close + atr * self.take_profit_atr_mult if atr > 0 else close * 1.03

        reason = (f"VWAP reclaim +{reclaim_dist:.2f}% | "
                  f"vol {vol_ratio:.1f}x | RSI {rsi:.0f}")

        return self._create_signal(
            symbol=symbol, score=score, reason=reason,
            price=close, stop_price=stop, target_price=target,
        )
