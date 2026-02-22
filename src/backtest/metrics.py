"""
AI Trader US - Performance Metrics

Calculates trading performance statistics.
"""

from typing import List, Dict
import numpy as np

from ..core.types import TradeResult


class PerformanceMetrics:
    """Trading performance calculator"""

    @staticmethod
    def compute(
        trades: List[TradeResult],
        equity_curve: List[Dict],
        daily_returns: List[float],
        initial_capital: float,
        risk_free_rate: float = 4.5,  # Annual %
    ) -> Dict:
        """Compute all performance metrics"""
        metrics = {}

        # --- Return metrics ---
        if equity_curve:
            final_equity = equity_curve[-1]['equity']
            metrics['total_return_pct'] = (final_equity - initial_capital) / initial_capital * 100
            metrics['final_equity'] = final_equity

            # CAGR
            n_days = len(equity_curve)
            if n_days > 1:
                years = n_days / 252
                if years > 0 and final_equity > 0:
                    metrics['cagr'] = ((final_equity / initial_capital) ** (1 / years) - 1) * 100
                else:
                    metrics['cagr'] = 0
        else:
            metrics['total_return_pct'] = 0
            metrics['cagr'] = 0

        # --- Drawdown ---
        if equity_curve:
            equities = [e['equity'] for e in equity_curve]
            peak = equities[0]
            max_dd = 0
            for eq in equities:
                if eq > peak:
                    peak = eq
                dd = (peak - eq) / peak * 100 if peak > 0 else 0
                max_dd = max(max_dd, dd)
            metrics['max_drawdown_pct'] = max_dd
        else:
            metrics['max_drawdown_pct'] = 0

        # --- Risk metrics ---
        if daily_returns and len(daily_returns) > 1:
            returns = np.array(daily_returns)
            daily_rf = risk_free_rate / 252 / 100  # Daily risk-free

            # Sharpe Ratio (annualized)
            excess = returns / 100 - daily_rf
            std_excess = np.std(excess)
            if std_excess > 1e-10:
                sharpe = np.mean(excess) / std_excess * np.sqrt(252)
                metrics['sharpe_ratio'] = max(-10, min(10, sharpe))  # Clamp
            else:
                metrics['sharpe_ratio'] = 0

            # Sortino Ratio
            downside = excess[excess < 0]
            if len(downside) > 0 and np.std(downside) > 0:
                metrics['sortino_ratio'] = np.mean(excess) / np.std(downside) * np.sqrt(252)
            else:
                metrics['sortino_ratio'] = 0

            # Calmar Ratio
            cagr = metrics.get('cagr', 0)
            max_dd = metrics.get('max_drawdown_pct', 0)
            metrics['calmar_ratio'] = cagr / max_dd if max_dd > 0 else 0

            # Volatility
            metrics['annual_volatility'] = float(np.std(returns) * np.sqrt(252))
        else:
            metrics['sharpe_ratio'] = 0
            metrics['sortino_ratio'] = 0
            metrics['calmar_ratio'] = 0
            metrics['annual_volatility'] = 0

        # --- Trade metrics ---
        if trades:
            wins = [t for t in trades if t.is_win]
            losses = [t for t in trades if not t.is_win]

            metrics['total_trades'] = len(trades)
            metrics['wins'] = len(wins)
            metrics['losses'] = len(losses)
            metrics['win_rate'] = len(wins) / len(trades) * 100

            # PnL
            pnls = [float(t.pnl) for t in trades]
            pnl_pcts = [t.pnl_pct for t in trades]

            metrics['avg_trade_pnl'] = np.mean(pnls)
            metrics['avg_trade_pnl_pct'] = np.mean(pnl_pcts)
            metrics['avg_win_pct'] = np.mean([t.pnl_pct for t in wins]) if wins else 0
            metrics['avg_loss_pct'] = np.mean([t.pnl_pct for t in losses]) if losses else 0

            # Profit Factor
            total_wins = sum(float(t.pnl) for t in wins)
            total_losses = abs(sum(float(t.pnl) for t in losses))
            metrics['profit_factor'] = total_wins / total_losses if total_losses > 0 else float('inf')

            # R-Multiple (avg win / avg loss)
            avg_win = np.mean([float(t.pnl) for t in wins]) if wins else 0
            avg_loss = abs(np.mean([float(t.pnl) for t in losses])) if losses else 1
            metrics['r_multiple'] = avg_win / avg_loss if avg_loss > 0 else 0

            # Max consecutive losses
            max_consec = 0
            current_consec = 0
            for t in trades:
                if not t.is_win:
                    current_consec += 1
                    max_consec = max(max_consec, current_consec)
                else:
                    current_consec = 0
            metrics['max_consecutive_losses'] = max_consec

            # Average holding time
            metrics['avg_holding_minutes'] = np.mean([t.holding_minutes for t in trades])

            # Strategy breakdown
            strategies = set(t.strategy for t in trades)
            breakdown = {}
            for strat in strategies:
                strat_trades = [t for t in trades if t.strategy == strat]
                strat_wins = [t for t in strat_trades if t.is_win]
                breakdown[strat] = {
                    'trades': len(strat_trades),
                    'win_rate': len(strat_wins) / len(strat_trades) * 100 if strat_trades else 0,
                    'avg_pnl_pct': np.mean([t.pnl_pct for t in strat_trades]),
                    'total_pnl': sum(float(t.pnl) for t in strat_trades),
                }
            metrics['strategy_breakdown'] = breakdown
        else:
            metrics['total_trades'] = 0
            metrics['win_rate'] = 0
            metrics['profit_factor'] = 0
            metrics['avg_trade_pnl_pct'] = 0

        return metrics
