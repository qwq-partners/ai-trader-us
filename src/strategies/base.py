"""
AI Trader US - Base Strategy

Abstract base class for all trading strategies.
Provides indicator computation, price history cache, and signal generation interface.
Adapted from ai-trader-v2.
"""

from abc import ABC, abstractmethod
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Any, List
import pandas as pd
from loguru import logger

from ..core.types import (
    Signal, Portfolio, Position, OrderSide, SignalStrength, StrategyType, TimeHorizon
)
from ..indicators.technical import compute_indicators


class BaseStrategy(ABC):
    """Base class for all trading strategies"""

    # Override in subclass
    name: str = "base"
    strategy_type: StrategyType = StrategyType.MOMENTUM_BREAKOUT
    time_horizon: TimeHorizon = TimeHorizon.DAY

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.min_score = self.config.get('min_score', 65)

        # Indicator cache: {symbol: {indicator_name: value}}
        self._indicator_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._max_cache_symbols = 500

    def evaluate(self, symbol: str, history: pd.DataFrame,
                 portfolio: Portfolio) -> Optional[Signal]:
        """
        Main entry point: evaluate a symbol and return a Signal or None.

        Args:
            symbol: Ticker symbol (e.g., 'AAPL')
            history: OHLCV DataFrame up to current bar (inclusive)
            portfolio: Current portfolio state
        """
        if not self.enabled:
            return None

        if history is None or len(history) < 20:
            return None

        # Compute indicators
        indicators = self._get_indicators(symbol, history)
        if not indicators:
            return None

        # Check entry conditions (implemented by subclass)
        signal = self.generate_signal(symbol, indicators, history, portfolio)

        if signal and signal.score >= self.min_score:
            return signal

        return None

    @abstractmethod
    def generate_signal(
        self,
        symbol: str,
        indicators: Dict[str, Any],
        history: pd.DataFrame,
        portfolio: Portfolio,
    ) -> Optional[Signal]:
        """
        Generate trading signal. Implement in subclass.

        Args:
            symbol: Ticker
            indicators: Pre-computed technical indicators
            history: Full price history up to current bar
            portfolio: Current portfolio

        Returns:
            Signal object or None
        """
        pass

    def check_exit(self, symbol: str, history: pd.DataFrame,
                   position: Position) -> Optional[str]:
        """
        Check custom exit conditions. Override in subclass.

        Returns:
            Exit reason string, or None to keep holding.
        """
        return None

    def _get_indicators(self, symbol: str, history: pd.DataFrame) -> Dict[str, Any]:
        """Compute and cache indicators"""
        try:
            indicators = compute_indicators(history)

            # Cache management (LRU)
            if symbol in self._indicator_cache:
                self._indicator_cache.move_to_end(symbol)
            self._indicator_cache[symbol] = indicators

            while len(self._indicator_cache) > self._max_cache_symbols:
                self._indicator_cache.popitem(last=False)

            return indicators
        except Exception as e:
            logger.debug(f"Indicator computation failed for {symbol}: {e}")
            return {}

    def _create_signal(
        self,
        symbol: str,
        score: float,
        reason: str,
        price: float = None,
        stop_price: float = None,
        target_price: float = None,
        strength: SignalStrength = None,
        metadata: dict = None,
    ) -> Signal:
        """Helper to create a Signal object"""
        if strength is None:
            if score >= 85:
                strength = SignalStrength.VERY_STRONG
            elif score >= 75:
                strength = SignalStrength.STRONG
            elif score >= 65:
                strength = SignalStrength.NORMAL
            else:
                strength = SignalStrength.WEAK

        meta = metadata or {}
        meta['time_horizon'] = self.time_horizon

        return Signal(
            symbol=symbol,
            side=OrderSide.BUY,
            strength=strength,
            strategy=self.strategy_type,
            price=Decimal(str(price)) if price else None,
            target_price=Decimal(str(target_price)) if target_price else None,
            stop_price=Decimal(str(stop_price)) if stop_price else None,
            score=score,
            confidence=score / 100,
            reason=reason,
            metadata=meta,
        )
