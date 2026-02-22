"""
AI Trader US - Backtest Report

Generate HTML report with Plotly charts.
"""

from pathlib import Path
from typing import List, Dict
from datetime import datetime

from ..core.types import TradeResult


class BacktestReport:
    """Generate interactive HTML backtest report"""

    @staticmethod
    def generate(
        equity_curve: List[Dict],
        trades: List[TradeResult],
        metrics: Dict,
        output_path: str = None,
        title: str = "Backtest Report",
    ) -> str:
        """Generate HTML report and return path"""
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            raise ImportError("plotly required: pip install plotly")

        if output_path is None:
            output_path = f"data/results/backtest_{datetime.now():%Y%m%d_%H%M%S}.html"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Build charts
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Equity Curve', 'Drawdown',
                'Monthly Returns', 'Trade PnL Distribution',
                'Win Rate by Strategy', 'Cumulative PnL'
            ),
            vertical_spacing=0.08,
            horizontal_spacing=0.08,
        )

        if equity_curve:
            dates = [e['date'] for e in equity_curve]
            equities = [e['equity'] for e in equity_curve]

            # 1. Equity Curve
            fig.add_trace(
                go.Scatter(x=dates, y=equities, name='Portfolio',
                           line=dict(color='#2196F3', width=2)),
                row=1, col=1
            )

            # 2. Drawdown
            peak = equities[0]
            drawdowns = []
            for eq in equities:
                if eq > peak:
                    peak = eq
                dd = (eq - peak) / peak * 100 if peak > 0 else 0
                drawdowns.append(dd)

            fig.add_trace(
                go.Scatter(x=dates, y=drawdowns, name='Drawdown',
                           fill='tozeroy', line=dict(color='#F44336', width=1)),
                row=1, col=2
            )

        # 3. Monthly Returns Heatmap (simplified as bar chart)
        if equity_curve and len(equity_curve) > 20:
            import pandas as pd
            eq_df = pd.DataFrame(equity_curve)
            eq_df['date'] = pd.to_datetime(eq_df['date'])
            eq_df = eq_df.set_index('date')
            monthly = eq_df['equity'].resample('ME').last().pct_change() * 100
            monthly = monthly.dropna()

            colors = ['#4CAF50' if r > 0 else '#F44336' for r in monthly.values]
            fig.add_trace(
                go.Bar(x=monthly.index, y=monthly.values, name='Monthly %',
                       marker_color=colors),
                row=2, col=1
            )

        # 4. Trade PnL Distribution
        if trades:
            pnl_pcts = [t.pnl_pct for t in trades]
            colors = ['#4CAF50' if p > 0 else '#F44336' for p in pnl_pcts]
            fig.add_trace(
                go.Histogram(x=pnl_pcts, name='Trade PnL %',
                             marker_color='#2196F3', nbinsx=30),
                row=2, col=2
            )

        # 5. Strategy breakdown
        breakdown = metrics.get('strategy_breakdown', {})
        if breakdown:
            strats = list(breakdown.keys())
            win_rates = [breakdown[s]['win_rate'] for s in strats]
            fig.add_trace(
                go.Bar(x=strats, y=win_rates, name='Win Rate %',
                       marker_color='#4CAF50'),
                row=3, col=1
            )

        # 6. Cumulative PnL
        if trades:
            cum_pnl = []
            running = 0
            for t in trades:
                running += float(t.pnl)
                cum_pnl.append(running)
            fig.add_trace(
                go.Scatter(y=cum_pnl, name='Cumulative PnL',
                           line=dict(color='#FF9800', width=2)),
                row=3, col=2
            )

        # Layout
        fig.update_layout(
            title=f"{title} | Return: {metrics.get('total_return_pct', 0):+.1f}% | "
                  f"Sharpe: {metrics.get('sharpe_ratio', 0):.2f} | "
                  f"MaxDD: {metrics.get('max_drawdown_pct', 0):.1f}% | "
                  f"Trades: {metrics.get('total_trades', 0)} | "
                  f"WinRate: {metrics.get('win_rate', 0):.0f}%",
            height=900,
            showlegend=False,
            template='plotly_dark',
        )

        fig.write_html(output_path)
        return output_path
