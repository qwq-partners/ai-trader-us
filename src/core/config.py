"""
AI Trader US - Configuration

YAML config loader. Adapted from ai-trader-v2.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from decimal import Decimal
from dataclasses import dataclass

import yaml
from loguru import logger

from .types import TradingConfig, RiskConfig, CommissionConfig, SlippageConfig


def load_yaml_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load YAML config file"""
    if config_path is None:
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config" / "default.yml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        logger.warning(f"Config not found: {config_path}")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        logger.info(f"Config loaded: {config_path}")
        return config
    except Exception as e:
        logger.error(f"Config load failed: {e}")
        return {}


def create_trading_config(config: Optional[Dict[str, Any]] = None) -> TradingConfig:
    """Create TradingConfig from raw dict"""
    if config is None:
        config = load_yaml_config()

    trading = config.get("trading", {})
    risk_cfg = config.get("risk", {})
    exit_cfg = config.get("exit_manager", {})

    # Commission
    comm_cfg = trading.get("commission", {})
    commission = CommissionConfig(
        type=comm_cfg.get("type", "zero"),
        rate=float(comm_cfg.get("rate", 0.0)),
        min_commission=float(comm_cfg.get("min", 0.0)),
    )

    # Slippage
    slip_cfg = trading.get("slippage", {})
    slippage = SlippageConfig(
        model=slip_cfg.get("model", "percentage"),
        rate=float(slip_cfg.get("rate", 0.05)),
    )

    # Risk
    risk = RiskConfig(
        daily_max_loss_pct=float(risk_cfg.get("daily_max_loss_pct", 3.0)),
        max_positions=int(risk_cfg.get("max_positions", 10)),
        base_position_pct=float(risk_cfg.get("base_position_pct", 10.0)),
        max_position_pct=float(risk_cfg.get("max_position_pct", 15.0)),
        min_cash_reserve_pct=float(risk_cfg.get("min_cash_reserve_pct", 10.0)),
        min_position_value=float(risk_cfg.get("min_position_value", 1000.0)),
        max_positions_per_sector=int(risk_cfg.get("max_positions_per_sector", 3)),
        default_stop_loss_pct=float(risk_cfg.get("stop_loss_pct", exit_cfg.get("stop_loss_pct", 3.0))),
        default_take_profit_pct=float(risk_cfg.get("take_profit_pct", 6.0)),
        trailing_stop_pct=float(risk_cfg.get("trailing_stop_pct", exit_cfg.get("trailing_stop_pct", 2.0))),
        consecutive_loss_threshold=int(risk_cfg.get("consecutive_loss_threshold", 3)),
        consecutive_loss_size_factor=float(risk_cfg.get("consecutive_loss_size_factor", 0.5)),
    )

    initial_capital = os.getenv("INITIAL_CAPITAL") or trading.get("initial_capital", 100000)

    return TradingConfig(
        initial_capital=Decimal(str(initial_capital)),
        commission=commission,
        slippage=slippage,
        risk=risk,
        enable_pre_market=trading.get("enable_pre_market", False),
        enable_after_hours=trading.get("enable_after_hours", False),
    )


@dataclass
class AppConfig:
    """Application configuration"""
    trading: TradingConfig
    raw: Dict[str, Any]

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "AppConfig":
        raw = load_yaml_config(config_path)
        trading = create_trading_config(raw)
        return cls(trading=trading, raw=raw)

    def get(self, *keys: str, default: Any = None) -> Any:
        """Nested key lookup: config.get('strategies', 'orb', 'enabled')"""
        value = self.raw
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            if value is None:
                return default
        return value
