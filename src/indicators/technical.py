"""
AI Trader US - Technical Indicators

Pure numpy/pandas indicator calculations.
"""

from typing import Optional, Dict, Any
import numpy as np
import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average"""
    return series.rolling(window=period, min_periods=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """RSI (Wilder's smoothing)"""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.inf)
    return 100 - (100 / (1 + rs))


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range"""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()


def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series,
         period: int = None) -> pd.Series:
    """Volume Weighted Average Price"""
    tp = (high + low + close) / 3
    if period:
        cum_tp_vol = (tp * volume).rolling(period).sum()
        cum_vol = volume.rolling(period).sum()
    else:
        cum_tp_vol = (tp * volume).cumsum()
        cum_vol = volume.cumsum()
    return cum_tp_vol / cum_vol.replace(0, np.nan)


def bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0):
    """Bollinger Bands -> (upper, middle, lower)"""
    middle = sma(series, period)
    std = series.rolling(window=period).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return upper, middle, lower


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD -> (macd_line, signal_line, histogram)"""
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def volume_ratio(volume: pd.Series, period: int = 20) -> pd.Series:
    """Volume relative to N-day average"""
    avg_vol = sma(volume, period)
    return volume / avg_vol.replace(0, np.nan)


def high_low_range(high: pd.Series, low: pd.Series, period: int = 20):
    """N-day high and low"""
    period_high = high.rolling(window=period).max()
    period_low = low.rolling(window=period).min()
    return period_high, period_low


def rs_rating(close: pd.Series, benchmark_close: pd.Series, period: int = 252) -> pd.Series:
    """Relative Strength vs benchmark (0-100 percentile rank)"""
    stock_return = close.pct_change(period)
    bench_return = benchmark_close.pct_change(period)
    relative = stock_return - bench_return
    return relative.rank(pct=True) * 100


def compute_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute all standard indicators for a DataFrame with OHLCV columns.

    Returns dict of indicator values (latest bar).
    """
    if len(df) < 20:
        return {}

    c = df['close']
    h = df['high']
    l = df['low']
    v = df['volume']

    indicators = {}

    # Moving averages
    for p in [5, 10, 20, 50, 150, 200]:
        ma = sma(c, p)
        if not ma.empty and not pd.isna(ma.iloc[-1]):
            indicators[f'ma{p}'] = float(ma.iloc[-1])

    # RSI
    rsi_val = rsi(c, 14)
    if not rsi_val.empty and not pd.isna(rsi_val.iloc[-1]):
        indicators['rsi'] = float(rsi_val.iloc[-1])

    # RSI-2 (for mean reversion)
    rsi2_val = rsi(c, 2)
    if not rsi2_val.empty and not pd.isna(rsi2_val.iloc[-1]):
        indicators['rsi2'] = float(rsi2_val.iloc[-1])

    # ATR
    atr_val = atr(h, l, c, 14)
    if not atr_val.empty and not pd.isna(atr_val.iloc[-1]):
        indicators['atr'] = float(atr_val.iloc[-1])
        if c.iloc[-1] > 0:
            indicators['atr_pct'] = float(atr_val.iloc[-1] / c.iloc[-1] * 100)

    # VWAP (20-bar)
    vwap_val = vwap(h, l, c, v, period=20)
    if not vwap_val.empty and not pd.isna(vwap_val.iloc[-1]):
        indicators['vwap'] = float(vwap_val.iloc[-1])

    # Volume ratio
    vr = volume_ratio(v, 20)
    if not vr.empty and not pd.isna(vr.iloc[-1]):
        indicators['vol_ratio'] = float(vr.iloc[-1])

    # Highs/Lows
    h20, l20 = high_low_range(h, l, 20)
    if not pd.isna(h20.iloc[-1]):
        indicators['high_20d'] = float(h20.iloc[-1])
        indicators['low_20d'] = float(l20.iloc[-1])

    # Previous day's 20-day high/low (for breakout detection)
    # Breakout = today's close > yesterday's 20-day high
    if len(h20) >= 2 and not pd.isna(h20.iloc[-2]):
        indicators['prev_high_20d'] = float(h20.iloc[-2])
        indicators['prev_low_20d'] = float(l20.iloc[-2])

    if len(df) >= 252:
        h52, l52 = high_low_range(h, l, 252)
        if not pd.isna(h52.iloc[-1]):
            indicators['high_52w'] = float(h52.iloc[-1])
            indicators['low_52w'] = float(l52.iloc[-1])
            if h52.iloc[-1] > 0:
                indicators['pct_from_52w_high'] = float(
                    (c.iloc[-1] - h52.iloc[-1]) / h52.iloc[-1] * 100
                )
            if l52.iloc[-1] > 0:
                indicators['pct_from_52w_low'] = float(
                    (c.iloc[-1] - l52.iloc[-1]) / l52.iloc[-1] * 100
                )

    # Price momentum
    for days in [1, 5, 20]:
        if len(df) > days:
            change = float((c.iloc[-1] - c.iloc[-1 - days]) / c.iloc[-1 - days] * 100)
            indicators[f'change_{days}d'] = change

    # Current price
    indicators['close'] = float(c.iloc[-1])
    indicators['volume'] = int(v.iloc[-1])

    return indicators


def compute_indicators_all(df: pd.DataFrame) -> pd.DataFrame:
    """Pre-compute all indicators for every row in the DataFrame.

    Much faster than calling compute_indicators() per-row.
    Used by BacktestEngine for bulk pre-computation.

    Returns DataFrame with indicator columns, same index as input.
    """
    if len(df) < 20:
        return pd.DataFrame(index=df.index)

    c = df['close'].astype(float)
    h = df['high'].astype(float)
    l = df['low'].astype(float)
    v = df['volume'].astype(float)

    result = pd.DataFrame(index=df.index)
    result['close'] = c
    result['volume'] = v

    # Moving averages
    for p in [5, 10, 20, 50, 150, 200]:
        result[f'ma{p}'] = sma(c, p)

    # RSI
    result['rsi'] = rsi(c, 14)
    result['rsi2'] = rsi(c, 2)

    # ATR
    atr_series = atr(h, l, c, 14)
    result['atr'] = atr_series
    result['atr_pct'] = atr_series / c * 100

    # VWAP (20-bar)
    result['vwap'] = vwap(h, l, c, v, period=20)

    # Volume ratio
    result['vol_ratio'] = volume_ratio(v, 20)

    # 20-day highs/lows
    h20, l20 = high_low_range(h, l, 20)
    result['high_20d'] = h20
    result['low_20d'] = l20
    result['prev_high_20d'] = h20.shift(1)
    result['prev_low_20d'] = l20.shift(1)

    # 52-week highs/lows
    h52, l52 = high_low_range(h, l, 252)
    result['high_52w'] = h52
    result['low_52w'] = l52
    result['pct_from_52w_high'] = (c - h52) / h52 * 100
    result['pct_from_52w_low'] = (c - l52) / l52 * 100

    # Price momentum
    for days in [1, 5, 20]:
        result[f'change_{days}d'] = c.pct_change(days) * 100

    return result
