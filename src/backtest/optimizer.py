"""
AI Trader US - Parameter Optimizer

Grid Search + Walk-Forward combined optimization.
Tests parameter combinations in parallel and validates with walk-forward.

Optimized for speed:
- Pre-computed indicators (compute once, lookup per-day)
- Initializer-based data sharing (no per-task pickling)
- ProcessPoolExecutor with fork-safe worker pattern
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Type
from itertools import product
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
import time
import pandas as pd
from loguru import logger

from .engine import BacktestEngine, BacktestResult
from .walk_forward import WalkForwardAnalyzer, WalkForwardResult
from ..strategies.base import BaseStrategy
from ..core.types import TradingConfig


@dataclass
class OptimizationResult:
    """Single parameter combination result"""
    params: Dict[str, Any]
    backtest: Optional[BacktestResult] = None
    walk_forward: Optional[WalkForwardResult] = None

    @property
    def total_return(self) -> float:
        return self.backtest.total_return_pct if self.backtest else 0

    @property
    def sharpe(self) -> float:
        return self.backtest.sharpe_ratio if self.backtest else 0

    @property
    def max_dd(self) -> float:
        return self.backtest.max_drawdown_pct if self.backtest else 0

    @property
    def win_rate(self) -> float:
        return self.backtest.win_rate if self.backtest else 0

    @property
    def profit_factor(self) -> float:
        return self.backtest.profit_factor if self.backtest else 0

    @property
    def total_trades(self) -> int:
        return self.backtest.total_trades if self.backtest else 0

    @property
    def wf_efficiency(self) -> float:
        return self.walk_forward.avg_efficiency if self.walk_forward else 0

    @property
    def wf_robust(self) -> bool:
        return self.walk_forward.is_robust if self.walk_forward else False

    @property
    def composite_score(self) -> float:
        """Combined score: return-weighted by robustness"""
        if self.total_trades < 10:
            return -999

        score = 0.0

        # Sharpe (40% weight)
        score += min(3.0, max(-2.0, self.sharpe)) * 40

        # Risk-adjusted return (30% weight)
        calmar = self.total_return / self.max_dd if self.max_dd > 0 else 0
        score += min(5.0, calmar) * 30

        # Win rate bonus (15% weight)
        score += min(70, self.win_rate) * 15 / 70

        # Profit factor (15% weight)
        score += min(3.0, self.profit_factor) * 15 / 3

        # Walk-forward robustness bonus/penalty
        if self.walk_forward:
            if self.wf_robust:
                score *= 1.2  # 20% bonus for robust strategies
            else:
                score *= 0.6  # 40% penalty for non-robust

        return score


@dataclass
class OptimizerResult:
    """Overall optimization result"""
    strategy_name: str
    param_grid: Dict[str, List[Any]]
    results: List[OptimizationResult] = field(default_factory=list)
    total_combinations: int = 0
    elapsed_seconds: float = 0.0

    @property
    def best_by_return(self) -> Optional[OptimizationResult]:
        valid = [r for r in self.results if r.total_trades >= 10]
        return max(valid, key=lambda r: r.total_return) if valid else None

    @property
    def best_by_sharpe(self) -> Optional[OptimizationResult]:
        valid = [r for r in self.results if r.total_trades >= 10]
        return max(valid, key=lambda r: r.sharpe) if valid else None

    @property
    def best_by_composite(self) -> Optional[OptimizationResult]:
        valid = [r for r in self.results if r.total_trades >= 10]
        return max(valid, key=lambda r: r.composite_score) if valid else None

    @property
    def robust_results(self) -> List[OptimizationResult]:
        return [r for r in self.results if r.wf_robust and r.total_trades >= 10]


# ================================================================
# Worker functions (top-level for pickling)
# ================================================================

# Global worker state (initialized once per worker process via initializer)
_WORKER_DATA = None
_WORKER_STRATEGY_CLS = None


def _init_worker(data_dict, strategy_cls_name, strategy_module,
                 initial_capital, start_date, end_date):
    """Initialize worker with shared data (called once per worker process)."""
    global _WORKER_DATA, _WORKER_STRATEGY_CLS
    import importlib

    mod = importlib.import_module(strategy_module)
    _WORKER_STRATEGY_CLS = getattr(mod, strategy_cls_name)

    _WORKER_DATA = {
        'data': data_dict,
        'initial_capital': initial_capital,
        'start_date': start_date,
        'end_date': end_date,
    }


def _run_single_backtest(params: dict) -> dict:
    """
    Worker function for parallel backtest execution.
    Uses global _WORKER_DATA initialized via _init_worker.
    Only receives the parameter dict (lightweight).
    """
    global _WORKER_DATA, _WORKER_STRATEGY_CLS

    config = TradingConfig()
    strategy = _WORKER_STRATEGY_CLS(config=params)
    engine = BacktestEngine(config=config)

    result = engine.run(
        strategy=strategy,
        data=_WORKER_DATA['data'],
        initial_capital=_WORKER_DATA['initial_capital'],
        start_date=_WORKER_DATA['start_date'],
        end_date=_WORKER_DATA['end_date'],
        benchmark=None,  # Skip benchmark in parallel workers
    )

    return {
        'params': params,
        'total_return_pct': result.total_return_pct,
        'max_drawdown_pct': result.max_drawdown_pct,
        'sharpe_ratio': result.sharpe_ratio,
        'win_rate': result.win_rate,
        'profit_factor': result.profit_factor,
        'total_trades': result.total_trades,
        'avg_trade_pnl_pct': result.avg_trade_pnl_pct,
    }


class ParameterOptimizer:
    """Grid Search + Walk-Forward parameter optimization (parallel)"""

    def __init__(self, config: TradingConfig = None):
        self._config = config or TradingConfig()

    def optimize(
        self,
        strategy_cls: Type[BaseStrategy],
        data: Dict[str, pd.DataFrame],
        param_grid: Dict[str, List[Any]],
        initial_capital: float = 100_000,
        start_date: date = None,
        end_date: date = None,
        validate: bool = True,
        wf_train_months: int = 6,
        wf_test_months: int = 3,
        wf_step_months: int = 2,
        sort_by: str = "composite",
        n_workers: int = None,
    ) -> OptimizerResult:
        """
        Run grid search optimization with parallel backtest execution.

        Args:
            strategy_cls: Strategy class to optimize
            data: {symbol: DataFrame} price data
            param_grid: {param_name: [values]} parameter grid
            initial_capital: Starting capital
            start_date/end_date: Date range
            validate: Run walk-forward validation on top results
            n_workers: Number of parallel workers (default: CPU count)
        """
        # Generate all parameter combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))
        total = len(combinations)

        if n_workers is None:
            n_workers = min(os.cpu_count() or 4, total, 20)  # Cap at 20

        logger.info(
            f"Optimizer: {strategy_cls.name} | "
            f"{len(param_names)} params x {total} combinations | "
            f"{n_workers} workers"
        )

        opt_result = OptimizerResult(
            strategy_name=strategy_cls.name,
            param_grid=param_grid,
            total_combinations=total,
        )

        print(f"\n{'='*70}")
        print(f"GRID SEARCH: {strategy_cls.name} ({total} combinations, {n_workers} workers)")
        print(f"{'='*70}")

        t0 = time.time()

        # Phase 1: Parallel Grid Search
        strategy_module = strategy_cls.__module__
        strategy_cls_name = strategy_cls.__name__

        all_params = [dict(zip(param_names, combo)) for combo in combinations]

        completed = 0
        results_map = {}  # params_key -> result dict

        with ProcessPoolExecutor(
            max_workers=n_workers,
            initializer=_init_worker,
            initargs=(data, strategy_cls_name, strategy_module,
                      initial_capital, start_date, end_date),
        ) as executor:
            future_to_params = {}
            for params in all_params:
                future = executor.submit(_run_single_backtest, params)
                future_to_params[future] = params

            for future in as_completed(future_to_params):
                params = future_to_params[future]
                completed += 1
                try:
                    res = future.result()
                    results_map[str(params)] = res

                    trades = res['total_trades']
                    ret = res['total_return_pct']
                    sr = res['sharpe_ratio']
                    wr = res['win_rate']

                    # Progress (print every 10 or for last)
                    if completed % 10 == 0 or completed == total:
                        elapsed = time.time() - t0
                        rate = completed / elapsed
                        eta = (total - completed) / rate if rate > 0 else 0
                        print(f"  [{completed:4d}/{total}] "
                              f"trades={trades:4d} ret={ret:+6.1f}% sr={sr:+5.2f} wr={wr:4.0f}% "
                              f"| ETA {eta:.0f}s | {params}")
                except Exception as e:
                    logger.error(f"Worker error for {params}: {e}")

        elapsed = time.time() - t0
        opt_result.elapsed_seconds = elapsed

        # Convert results to OptimizationResult objects (ordered by original grid)
        for params in all_params:
            res = results_map.get(str(params))
            if res:
                bt = BacktestResult(
                    total_return_pct=res['total_return_pct'],
                    max_drawdown_pct=res['max_drawdown_pct'],
                    sharpe_ratio=res['sharpe_ratio'],
                    win_rate=res['win_rate'],
                    profit_factor=res['profit_factor'],
                    total_trades=res['total_trades'],
                    avg_trade_pnl_pct=res['avg_trade_pnl_pct'],
                )
                opt_result.results.append(OptimizationResult(params=params, backtest=bt))

        print(f"\n  Completed {total} backtests in {elapsed:.1f}s "
              f"({total/elapsed:.1f} backtests/sec)")

        # Phase 2: Walk-Forward validation on top N results
        if validate:
            sort_key = {
                "return": lambda r: r.total_return,
                "sharpe": lambda r: r.sharpe,
                "composite": lambda r: r.composite_score,
            }.get(sort_by, lambda r: r.composite_score)

            valid_results = [r for r in opt_result.results if r.total_trades >= 10]
            valid_results.sort(key=sort_key, reverse=True)

            top_n = min(5, len(valid_results))
            if top_n > 0:
                print(f"\n{'='*70}")
                print(f"WALK-FORWARD VALIDATION: Top {top_n} parameter sets")
                print(f"{'='*70}")

                wf_analyzer = WalkForwardAnalyzer(config=self._config)

                for j, opt_res in enumerate(valid_results[:top_n]):
                    logger.info(f"  WF [{j+1}/{top_n}] params={opt_res.params}")

                    strategy = strategy_cls(config=opt_res.params)
                    wf_result = wf_analyzer.analyze(
                        strategy=strategy,
                        data=data,
                        train_months=wf_train_months,
                        test_months=wf_test_months,
                        step_months=wf_step_months,
                        initial_capital=initial_capital,
                    )
                    opt_res.walk_forward = wf_result

        # Print summary
        self._print_summary(opt_result, sort_by)

        return opt_result

    def _print_summary(self, result: OptimizerResult, sort_by: str):
        """Print optimization results summary"""
        print(f"\n{'='*90}")
        print(f"OPTIMIZATION RESULTS: {result.strategy_name}")
        print(f"  Tested: {result.total_combinations} combinations in {result.elapsed_seconds:.1f}s")
        print(f"{'='*90}")

        # Sort by composite score
        valid = [r for r in result.results if r.total_trades >= 10]
        if not valid:
            print("  No valid results (all combinations had < 10 trades)")
            return

        valid.sort(key=lambda r: r.composite_score, reverse=True)

        print(f"\n{'Rank':>4s} {'Return':>8s} {'Sharpe':>7s} {'MaxDD':>7s} "
              f"{'WR%':>5s} {'PF':>5s} {'Trades':>6s} "
              f"{'WF-Eff':>7s} {'Robust':>6s} {'Score':>7s} | Parameters")
        print("-" * 110)

        for i, r in enumerate(valid[:20]):
            wf_eff = f"{r.wf_efficiency:.2f}" if r.walk_forward else "  --"
            robust = "YES" if r.wf_robust else ("NO" if r.walk_forward else "--")

            print(f"  {i+1:>2d}. {r.total_return:>+7.1f}% {r.sharpe:>+6.2f} "
                  f"{r.max_dd:>6.1f}% {r.win_rate:>4.0f}% {r.profit_factor:>4.2f} "
                  f"{r.total_trades:>5d} {wf_eff:>7s} {robust:>6s} "
                  f"{r.composite_score:>6.0f} | {r.params}")

        # Recommendations
        print(f"\n{'='*90}")
        print("RECOMMENDATIONS:")

        best = result.best_by_composite
        if best:
            print(f"\n  Best Overall (Composite Score):")
            print(f"    Params: {best.params}")
            print(f"    Return={best.total_return:+.1f}% Sharpe={best.sharpe:.2f} "
                  f"MaxDD={best.max_dd:.1f}% WR={best.win_rate:.0f}% "
                  f"PF={best.profit_factor:.2f}")

        robust = result.robust_results
        if robust:
            best_robust = max(robust, key=lambda r: r.composite_score)
            print(f"\n  Best Robust (Walk-Forward Validated):")
            print(f"    Params: {best_robust.params}")
            print(f"    Return={best_robust.total_return:+.1f}% "
                  f"Sharpe={best_robust.sharpe:.2f} "
                  f"WF-Efficiency={best_robust.wf_efficiency:.2f}")
        elif any(r.walk_forward for r in result.results):
            print(f"\n  WARNING: No robust parameter set found!")
            print(f"  All tested combinations may be overfit to training data.")

        best_return = result.best_by_return
        if best_return and best_return != best:
            print(f"\n  Highest Return (may be overfit):")
            print(f"    Params: {best_return.params}")
            print(f"    Return={best_return.total_return:+.1f}% "
                  f"Sharpe={best_return.sharpe:.2f}")

        print(f"{'='*90}")
