"""
AI Trader US - Walk-Forward Analysis

Sliding window backtest to detect overfitting.
Train on N months, validate on M months, slide forward.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Dict, Optional
import pandas as pd
from loguru import logger

from .engine import BacktestEngine, BacktestResult
from ..strategies.base import BaseStrategy
from ..core.types import TradingConfig


@dataclass
class WalkForwardWindow:
    """Single walk-forward window result"""
    window_id: int
    train_start: date
    train_end: date
    test_start: date
    test_end: date
    train_result: Optional[BacktestResult] = None
    test_result: Optional[BacktestResult] = None

    @property
    def train_return(self) -> float:
        return self.train_result.total_return_pct if self.train_result else 0

    @property
    def test_return(self) -> float:
        return self.test_result.total_return_pct if self.test_result else 0

    @property
    def efficiency(self) -> float:
        """Test return / Train return. Good if > 0.5"""
        if self.train_return <= 0:
            return 0
        return self.test_return / self.train_return


@dataclass
class WalkForwardResult:
    """Aggregate walk-forward analysis result"""
    windows: List[WalkForwardWindow] = field(default_factory=list)
    strategy_name: str = ""

    @property
    def n_windows(self) -> int:
        return len(self.windows)

    @property
    def avg_train_return(self) -> float:
        returns = [w.train_return for w in self.windows]
        return sum(returns) / len(returns) if returns else 0

    @property
    def avg_test_return(self) -> float:
        returns = [w.test_return for w in self.windows]
        return sum(returns) / len(returns) if returns else 0

    @property
    def avg_efficiency(self) -> float:
        effs = [w.efficiency for w in self.windows if w.train_return > 0]
        return sum(effs) / len(effs) if effs else 0

    @property
    def test_positive_pct(self) -> float:
        """% of test windows that are profitable"""
        if not self.windows:
            return 0
        positive = sum(1 for w in self.windows if w.test_return > 0)
        return positive / len(self.windows) * 100

    @property
    def is_robust(self) -> bool:
        """Strategy is robust if test performance is consistent"""
        return (
            self.avg_efficiency > 0.3 and
            self.test_positive_pct >= 60 and
            self.avg_test_return > 0
        )


class WalkForwardAnalyzer:
    """Walk-Forward analysis engine"""

    def __init__(self, config: TradingConfig = None):
        self._config = config or TradingConfig()

    def analyze(
        self,
        strategy: BaseStrategy,
        data: Dict[str, pd.DataFrame],
        train_months: int = 6,
        test_months: int = 3,
        step_months: int = 1,
        initial_capital: float = 100_000,
        strategies: List[BaseStrategy] = None,
    ) -> WalkForwardResult:
        """
        Run walk-forward analysis.

        Args:
            strategy: Strategy to test (single) or None if strategies provided
            data: {symbol: DataFrame} price data
            train_months: Training window length
            test_months: Testing window length
            step_months: How far to slide each iteration
            initial_capital: Starting capital per window
            strategies: List of strategies (multi-strategy mode)
        """
        # Find date range across all data
        all_dates = set()
        for df in data.values():
            all_dates.update(df.index.date if hasattr(df.index, 'date') else df.index)

        sorted_dates = sorted(all_dates)
        if not sorted_dates:
            return WalkForwardResult()

        data_start = sorted_dates[0]
        data_end = sorted_dates[-1]

        strat_name = strategy.name if strategy else "+".join(s.name for s in (strategies or []))
        logger.info(
            f"Walk-Forward: {strat_name} | "
            f"train={train_months}m test={test_months}m step={step_months}m | "
            f"{data_start} ~ {data_end}"
        )

        # Generate windows
        windows = []
        window_id = 0
        current_start = data_start

        while True:
            train_start = current_start
            train_end = train_start + timedelta(days=train_months * 30)
            test_start = train_end + timedelta(days=1)
            test_end = test_start + timedelta(days=test_months * 30)

            if test_end > data_end:
                break

            window = WalkForwardWindow(
                window_id=window_id,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
            windows.append(window)

            window_id += 1
            current_start = current_start + timedelta(days=step_months * 30)

        if not windows:
            logger.warning("Not enough data for walk-forward analysis")
            return WalkForwardResult()

        logger.info(f"Generated {len(windows)} walk-forward windows")

        # Run each window
        for i, window in enumerate(windows):
            logger.info(
                f"  Window {i+1}/{len(windows)}: "
                f"train {window.train_start}~{window.train_end} | "
                f"test {window.test_start}~{window.test_end}"
            )

            engine = BacktestEngine(config=self._config)

            # Train period
            train_result = engine.run(
                strategy=strategy,
                strategies=strategies,
                data={s: df.copy() for s, df in data.items()},
                initial_capital=initial_capital,
                start_date=window.train_start,
                end_date=window.train_end,
            )
            window.train_result = train_result

            # Test period (fresh engine)
            engine = BacktestEngine(config=self._config)
            test_result = engine.run(
                strategy=strategy,
                strategies=strategies,
                data={s: df.copy() for s, df in data.items()},
                initial_capital=initial_capital,
                start_date=window.test_start,
                end_date=window.test_end,
            )
            window.test_result = test_result

        result = WalkForwardResult(
            windows=windows,
            strategy_name=strat_name,
        )

        # Print summary
        self._print_summary(result)

        return result

    def _print_summary(self, result: WalkForwardResult):
        """Print walk-forward analysis summary"""
        print("\n" + "=" * 80)
        print(f"WALK-FORWARD ANALYSIS: {result.strategy_name}")
        print("=" * 80)

        print(f"\n{'Window':>6s} | {'Train Period':>25s} | {'Test Period':>25s} | "
              f"{'Train%':>7s} | {'Test%':>7s} | {'Eff':>5s} | {'Trades':>6s}")
        print("-" * 95)

        for w in result.windows:
            train_trades = w.train_result.total_trades if w.train_result else 0
            test_trades = w.test_result.total_trades if w.test_result else 0

            print(f"  {w.window_id+1:>4d} | "
                  f"{w.train_start} ~ {w.train_end} | "
                  f"{w.test_start} ~ {w.test_end} | "
                  f"{w.train_return:>+6.1f}% | "
                  f"{w.test_return:>+6.1f}% | "
                  f"{w.efficiency:>4.1f}x | "
                  f"{train_trades:>3d}/{test_trades:<3d}")

        print("-" * 95)
        print(f"  Average:{'':>51s}"
              f"{result.avg_train_return:>+6.1f}% | "
              f"{result.avg_test_return:>+6.1f}% | "
              f"{result.avg_efficiency:>4.1f}x |")

        print(f"\n  Test Positive Windows: {result.test_positive_pct:.0f}%")
        print(f"  Walk-Forward Efficiency: {result.avg_efficiency:.2f}")

        if result.is_robust:
            print(f"  Verdict: ROBUST (strategy generalizes well)")
        else:
            issues = []
            if result.avg_efficiency <= 0.3:
                issues.append("low efficiency (possible overfit)")
            if result.test_positive_pct < 60:
                issues.append("inconsistent test performance")
            if result.avg_test_return <= 0:
                issues.append("negative avg test return")
            print(f"  Verdict: WEAK ({', '.join(issues)})")

        print("=" * 80)
