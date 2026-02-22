"""
AI Trader US - Backtest Engine

Event-driven backtesting engine. Replays historical data through strategies.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Type
import pandas as pd
from loguru import logger

from ..core.types import (
    Order, Fill, Position, Portfolio, Signal, TradeResult,
    OrderSide, OrderStatus, PositionSide, TradingConfig, TimeHorizon
)
from ..core.event import MarketDataEvent
from ..execution.broker.paper import PaperBroker
from ..strategies.base import BaseStrategy
from ..indicators.technical import compute_indicators_all


@dataclass
class BacktestResult:
    """Backtest result container"""
    trades: List[TradeResult] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)
    portfolio: Optional[Portfolio] = None

    # Benchmark comparison
    benchmark_curve: List[Dict] = field(default_factory=list)
    benchmark_return_pct: float = 0.0
    alpha: float = 0.0  # Strategy return - benchmark return

    # Computed metrics
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    avg_trade_pnl_pct: float = 0.0


class BacktestEngine:
    """Event-driven backtest engine"""

    def __init__(self, config: TradingConfig = None):
        self._config = config or TradingConfig()
        self._broker = PaperBroker(
            commission=self._config.commission,
            slippage=self._config.slippage,
        )

    def run(
        self,
        strategy: BaseStrategy = None,
        data: Dict[str, pd.DataFrame] = None,
        initial_capital: float = 100_000,
        start_date: date = None,
        end_date: date = None,
        strategies: List[BaseStrategy] = None,
        benchmark: str = "SPY",
    ) -> BacktestResult:
        """
        Run backtest with one or multiple strategies.

        Args:
            strategy: Single strategy instance (backward compatible)
            data: Dict of {symbol: DataFrame(OHLCV)} with DatetimeIndex
            initial_capital: Starting capital in USD
            start_date: Start date (None = use all data)
            end_date: End date (None = use all data)
            strategies: List of strategy instances (multi-strategy mode)
        """
        # Support both single and multi-strategy
        if strategies:
            strategy_list = strategies
        elif strategy:
            strategy_list = [strategy]
        else:
            raise ValueError("Provide either strategy or strategies")

        # Map strategy type to strategy instance for exit handling
        self._strategy_map = {s.strategy_type.value: s for s in strategy_list}

        portfolio = Portfolio(
            cash=Decimal(str(initial_capital)),
            initial_capital=Decimal(str(initial_capital)),
        )

        # Collect all dates across symbols
        # Keep full data for history/indicators, only filter simulation dates
        all_dates = set()
        # Build date-to-row-index mapping for fast lookups
        date_idx_map: Dict[str, Dict] = {}  # symbol -> {date -> row_index}

        for symbol, df in data.items():
            date_idx_map[symbol] = {}
            dates = df.index.date if hasattr(df.index, 'date') else df.index
            for i, d in enumerate(dates):
                d_val = d if not hasattr(d, 'date') else d
                date_idx_map[symbol][d_val] = i
                if start_date and d_val < start_date:
                    continue
                if end_date and d_val > end_date:
                    continue
                all_dates.add(d_val)

        sorted_dates = sorted(all_dates)
        if not sorted_dates:
            logger.warning("No data to backtest")
            return BacktestResult()

        strat_names = "+".join(s.name for s in strategy_list)
        logger.info(
            f"Backtest: {strat_names} | {len(data)} symbols | "
            f"{sorted_dates[0]} ~ {sorted_dates[-1]} | ${initial_capital:,.0f}"
        )

        # Pre-compute all indicators for all symbols (massive speed boost)
        precomputed: Dict[str, pd.DataFrame] = {}
        for symbol, df in data.items():
            precomputed[symbol] = compute_indicators_all(df)

        trades: List[TradeResult] = []
        equity_curve: List[Dict] = []
        prev_equity = Decimal(str(initial_capital))
        daily_returns: List[float] = []

        # Day-by-day simulation
        for current_date in sorted_dates:
            ts = pd.Timestamp(current_date)
            portfolio.reset_daily()

            # Process each symbol's data for this date
            signals: List[Signal] = []

            for symbol, df in data.items():
                row_idx = date_idx_map[symbol].get(current_date)
                if row_idx is None:
                    continue

                bar = df.iloc[row_idx]
                close = Decimal(str(bar['close']))

                # Update existing position prices
                if symbol in portfolio.positions:
                    pos = portfolio.positions[symbol]
                    pos.current_price = close
                    if pos.highest_price is None or close > pos.highest_price:
                        pos.highest_price = close

                # Get pre-computed indicators (O(1) lookup instead of full recompute)
                ind_row = precomputed[symbol].iloc[row_idx]
                indicators = {}
                for k, v in ind_row.items():
                    if pd.notna(v):
                        indicators[k] = int(v) if k == 'volume' else float(v)

                # Build history slice for strategies that need raw bars
                # iloc creates a view (O(1)), not a copy
                hist = df.iloc[:row_idx + 1]

                # Generate signals from ALL strategies (bypass evaluate() overhead)
                for strat in strategy_list:
                    if not strat.enabled or len(hist) < 20:
                        continue
                    signal = strat.generate_signal(symbol, indicators, hist, portfolio)
                    if signal and signal.score >= strat.min_score:
                        signals.append(signal)

            # Check exits first (using strategy that opened each position)
            exit_trades = self._check_exits_multi(
                strategy_list, portfolio, data, ts, date_idx_map
            )
            trades.extend(exit_trades)

            # Process entry signals (sorted by score, highest first)
            signals.sort(key=lambda s: s.score, reverse=True)
            for signal in signals:
                if not signal.is_buy:
                    continue
                if signal.symbol in portfolio.positions:
                    continue  # Already holding

                # Position sizing
                trade_result = self._execute_entry(
                    signal, portfolio, data, ts
                )
                # Entry executed if position was added

            # Record daily equity
            equity = portfolio.total_equity
            daily_ret = float((equity - prev_equity) / prev_equity * 100) if prev_equity > 0 else 0
            daily_returns.append(daily_ret)
            prev_equity = equity

            equity_curve.append({
                'date': current_date,
                'equity': float(equity),
                'cash': float(portfolio.cash),
                'positions': len(portfolio.positions),
                'daily_return': daily_ret,
            })

        # Close remaining positions at last known prices
        for symbol in list(portfolio.positions.keys()):
            pos = portfolio.positions[symbol]
            trade = self._close_position(portfolio, pos, pos.current_price,
                                         datetime.combine(sorted_dates[-1], datetime.min.time()),
                                         "end_of_backtest")
            if trade:
                trades.append(trade)

        # Build result
        result = BacktestResult(
            trades=trades,
            equity_curve=equity_curve,
            daily_returns=daily_returns,
            portfolio=portfolio,
            total_trades=len(trades),
        )

        # Compute metrics
        self._compute_metrics(result, initial_capital)

        # Compute benchmark comparison
        if benchmark and sorted_dates:
            self._compute_benchmark(result, benchmark, data, sorted_dates, initial_capital)

        logger.info(
            f"Result: {result.total_trades} trades | "
            f"Return: {result.total_return_pct:+.1f}% | "
            f"MaxDD: {result.max_drawdown_pct:.1f}% | "
            f"Sharpe: {result.sharpe_ratio:.2f} | "
            f"WinRate: {result.win_rate:.0f}% | "
            f"Alpha: {result.alpha:+.1f}%"
        )

        return result

    def _execute_entry(self, signal: Signal, portfolio: Portfolio,
                       data: Dict[str, pd.DataFrame], ts: pd.Timestamp) -> bool:
        """Execute entry signal"""
        symbol = signal.symbol
        if symbol not in data or ts not in data[symbol].index:
            return False

        bar = data[symbol].loc[ts]
        price = Decimal(str(bar['close']))

        # Position sizing
        risk_cfg = self._config.risk
        max_position_value = portfolio.total_equity * Decimal(str(risk_cfg.max_position_pct / 100))
        base_position_value = portfolio.total_equity * Decimal(str(risk_cfg.base_position_pct / 100))
        min_cash = portfolio.total_equity * Decimal(str(risk_cfg.min_cash_reserve_pct / 100))

        available_cash = portfolio.cash - min_cash
        if available_cash < Decimal(str(risk_cfg.min_position_value)):
            return False

        # Check max positions
        if len(portfolio.positions) >= risk_cfg.max_positions:
            return False

        # Check sector limit
        if risk_cfg.max_positions_per_sector > 0 and signal.metadata.get('sector'):
            sector = signal.metadata['sector']
            sector_count = sum(
                1 for p in portfolio.positions.values()
                if p.sector == sector
            )
            if sector_count >= risk_cfg.max_positions_per_sector:
                return False

        position_value = min(base_position_value, available_cash, max_position_value)
        quantity = int(position_value / price)
        if quantity <= 0:
            return False

        # Execute via paper broker
        order = Order(
            symbol=symbol, side=OrderSide.BUY, quantity=quantity,
            price=price, strategy=signal.strategy.value,
            signal_score=signal.score, reason=signal.reason,
        )

        fill = self._broker.execute_order(order, price, ts.to_pydatetime())
        if not fill:
            return False

        # Create position
        pos = Position(
            symbol=symbol, quantity=fill.quantity,
            avg_price=fill.price, current_price=fill.price,
            highest_price=fill.price,
            strategy=signal.strategy.value,
            entry_time=fill.timestamp,
            sector=signal.metadata.get('sector'),
            stop_loss=signal.stop_price,
            take_profit=signal.target_price,
            side=PositionSide.LONG,
            time_horizon=signal.metadata.get('time_horizon'),
        )

        portfolio.positions[symbol] = pos
        portfolio.cash -= fill.total_cost
        portfolio.daily_trades += 1

        return True

    def _check_exits_multi(self, strategies: List[BaseStrategy], portfolio: Portfolio,
                           data: Dict[str, pd.DataFrame], ts: pd.Timestamp,
                           date_idx_map: Dict[str, Dict] = None) -> List[TradeResult]:
        """Check exit conditions for all positions using the strategy that opened each"""
        trades = []

        for symbol in list(portfolio.positions.keys()):
            pos = portfolio.positions[symbol]
            if symbol not in data:
                continue

            # Use fast index lookup
            row_idx = None
            if date_idx_map and symbol in date_idx_map:
                current_date = ts.date() if hasattr(ts, 'date') else ts
                row_idx = date_idx_map[symbol].get(current_date)
            if row_idx is None:
                continue

            df = data[symbol]
            bar = df.iloc[row_idx]
            current_price = Decimal(str(bar['close']))
            low_price = Decimal(str(bar['low']))
            pos.current_price = current_price

            # Find the strategy that opened this position
            owning_strategy = self._strategy_map.get(pos.strategy, strategies[0])

            exit_reason = None

            # Stop loss (check against low)
            if pos.stop_loss and low_price <= pos.stop_loss:
                exit_reason = "stop_loss"
                current_price = pos.stop_loss  # Assume filled at stop

            # Take profit
            elif pos.take_profit and current_price >= pos.take_profit:
                exit_reason = "take_profit"

            # Trailing stop
            elif pos.trailing_stop_pct and pos.highest_price:
                trail_price = pos.highest_price * (1 - Decimal(str(pos.trailing_stop_pct / 100)))
                if low_price <= trail_price:
                    exit_reason = "trailing_stop"
                    current_price = trail_price

            # Day trade EOD close
            elif pos.time_horizon == TimeHorizon.DAY:
                if pos.entry_time and pos.entry_time.date() < ts.date():
                    exit_reason = "eod_close"

            # Max holding days (swing) - use owning strategy's config
            elif pos.entry_time:
                holding_days = (ts.to_pydatetime() - pos.entry_time).days
                max_days = owning_strategy.config.get('max_holding_days', 20)
                if holding_days >= max_days:
                    exit_reason = "max_holding"

            # Strategy custom exit (use owning strategy)
            if not exit_reason:
                hist = df.iloc[:row_idx + 1]
                exit_signal = owning_strategy.check_exit(symbol, hist, pos)
                if exit_signal:
                    exit_reason = exit_signal

            if exit_reason:
                trade = self._close_position(
                    portfolio, pos, current_price,
                    ts.to_pydatetime(), exit_reason
                )
                if trade:
                    trades.append(trade)

        return trades

    def _close_position(self, portfolio: Portfolio, pos: Position,
                        exit_price: Decimal, timestamp: datetime,
                        reason: str) -> Optional[TradeResult]:
        """Close a position and record trade"""
        order = Order(
            symbol=pos.symbol, side=OrderSide.SELL,
            quantity=pos.quantity, price=exit_price,
            strategy=pos.strategy, reason=reason,
        )

        fill = self._broker.execute_order(order, exit_price, timestamp)
        if not fill:
            return None

        trade = TradeResult(
            symbol=pos.symbol,
            side=OrderSide.BUY,
            entry_price=pos.avg_price,
            exit_price=fill.price,
            quantity=pos.quantity,
            entry_time=pos.entry_time or timestamp,
            exit_time=timestamp,
            strategy=pos.strategy or "",
            reason=reason,
            commission=fill.commission,
        )

        # Update portfolio
        portfolio.cash += fill.total_value - fill.commission
        portfolio.daily_pnl += trade.pnl
        del portfolio.positions[pos.symbol]

        return trade

    def _compute_benchmark(self, result: BacktestResult, benchmark: str,
                           data: Dict[str, pd.DataFrame], sorted_dates: list,
                           initial_capital: float):
        """Compute benchmark buy-and-hold comparison"""
        # Try to get benchmark from existing data, or download
        bench_df = data.get(benchmark)
        if bench_df is None:
            try:
                from ..data.providers.yfinance_provider import YFinanceProvider
                from ..data.store import DataStore
                provider = YFinanceProvider()
                store = DataStore()
                bench_df = store.load(benchmark, 'daily')
                if bench_df is None or bench_df.empty:
                    bench_df = provider.get_daily_bars(
                        benchmark, sorted_dates[0], sorted_dates[-1]
                    )
                    if not bench_df.empty:
                        store.save(benchmark, bench_df, 'daily')
            except Exception as e:
                logger.debug(f"Could not load benchmark {benchmark}: {e}")
                return

        if bench_df is None or bench_df.empty:
            return

        # Calculate buy-and-hold equity curve
        benchmark_curve = []
        first_price = None

        for current_date in sorted_dates:
            ts = pd.Timestamp(current_date)
            if ts not in bench_df.index:
                continue

            price = float(bench_df.loc[ts, 'close'])
            if first_price is None:
                first_price = price

            bench_equity = initial_capital * (price / first_price)
            benchmark_curve.append({
                'date': current_date,
                'equity': bench_equity,
                'price': price,
            })

        if benchmark_curve:
            result.benchmark_curve = benchmark_curve
            result.benchmark_return_pct = (
                (benchmark_curve[-1]['equity'] - initial_capital) / initial_capital * 100
            )
            result.alpha = result.total_return_pct - result.benchmark_return_pct

    def _compute_metrics(self, result: BacktestResult, initial_capital: float):
        """Compute performance metrics"""
        from ..backtest.metrics import PerformanceMetrics
        metrics = PerformanceMetrics.compute(
            trades=result.trades,
            equity_curve=result.equity_curve,
            daily_returns=result.daily_returns,
            initial_capital=initial_capital,
        )
        result.total_return_pct = metrics.get('total_return_pct', 0)
        result.max_drawdown_pct = metrics.get('max_drawdown_pct', 0)
        result.sharpe_ratio = metrics.get('sharpe_ratio', 0)
        result.win_rate = metrics.get('win_rate', 0)
        result.profit_factor = metrics.get('profit_factor', 0)
        result.avg_trade_pnl_pct = metrics.get('avg_trade_pnl_pct', 0)
