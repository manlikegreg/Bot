"""Technical indicator calculations and heuristic signal generation."""
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import ta

from logger import get_logger

logger = get_logger()

SignalDict = Dict[str, str | float]


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _clamp(val: float, low: float = 0.0, high: float = 100.0) -> float:  # noqa: D401
    """Clamp a numeric value between low and high."""
    return max(low, min(high, val))


# ---------------------------------------------------------------------------
# Indicator-specific signal generators
# ---------------------------------------------------------------------------

def rsi_signal(df: pd.DataFrame, window: int = 14) -> SignalDict:
    rsi_series = ta.momentum.RSIIndicator(close=df["close"], window=window).rsi()
    latest_rsi = rsi_series.iloc[-1]
    if latest_rsi < 30:
        confidence = _clamp((30 - latest_rsi) / 30 * 100)
        sig = "BUY"
        reason = f"RSI oversold ({latest_rsi:.1f})"
    elif latest_rsi > 70:
        confidence = _clamp((latest_rsi - 70) / 30 * 100)
        sig = "SELL"
        reason = f"RSI overbought ({latest_rsi:.1f})"
    else:
        sig = "HOLD"
        confidence = 0
        reason = f"RSI neutral ({latest_rsi:.1f})"
    return {"source": "RSI", "signal": sig, "confidence": confidence, "reason": reason}


def macd_signal(df: pd.DataFrame) -> SignalDict:
    macd_ind = ta.trend.MACD(close=df["close"])  # default 12/26/9
    macd = macd_ind.macd().iloc[-1]
    macd_signal_line = macd_ind.macd_signal().iloc[-1]
    macd_hist = macd_ind.macd_diff().iloc[-1]

    if macd_hist > 0 and macd > macd_signal_line:
        confidence = _clamp(abs(macd_hist) * 100)
        sig = "BUY"
        reason = "MACD bullish crossover"
    elif macd_hist < 0 and macd < macd_signal_line:
        confidence = _clamp(abs(macd_hist) * 100)
        sig = "SELL"
        reason = "MACD bearish crossover"
    else:
        sig = "HOLD"
        confidence = 0
        reason = "MACD flat"
    confidence = min(confidence, 100)
    return {"source": "MACD", "signal": sig, "confidence": confidence, "reason": reason}


def bollinger_signal(df: pd.DataFrame, window: int = 20, n_std: float = 2) -> SignalDict:
    bb_ind = ta.volatility.BollingerBands(close=df["close"], window=window, window_dev=n_std)
    lower = bb_ind.bollinger_lband().iloc[-1]
    upper = bb_ind.bollinger_hband().iloc[-1]
    close = df["close"].iloc[-1]

    if close < lower:
        confidence = _clamp((lower - close) / (upper - lower) * 100)
        sig = "BUY"
        reason = "Price below lower Bollinger band"
    elif close > upper:
        confidence = _clamp((close - upper) / (upper - lower) * 100)
        sig = "SELL"
        reason = "Price above upper Bollinger band"
    else:
        sig = "HOLD"
        confidence = 0
        reason = "Price inside Bollinger bands"
    return {"source": "Bollinger", "signal": sig, "confidence": confidence, "reason": reason}


def ma_crossover_signal(df: pd.DataFrame, fast: int = 50, slow: int = 200) -> SignalDict:
    if len(df) < slow + 5:
        return {"source": "MA", "signal": "HOLD", "confidence": 0, "reason": "Insufficient data for MA"}

    fast_ma = df["close"].rolling(window=fast).mean().iloc[-1]
    slow_ma = df["close"].rolling(window=slow).mean().iloc[-1]

    diff_pct = (fast_ma - slow_ma) / slow_ma * 100

    if diff_pct > 0.2:  # uptrend
        confidence = _clamp(diff_pct)
        sig = "BUY"
        reason = "50/200 MA golden cross"
    elif diff_pct < -0.2:
        confidence = _clamp(abs(diff_pct))
        sig = "SELL"
        reason = "50/200 MA death cross"
    else:
        sig = "HOLD"
        confidence = 0
        reason = "MAs converging"

    return {"source": "MA", "signal": sig, "confidence": confidence, "reason": reason}


def volume_spike_signal(df: pd.DataFrame, window: int = 20, multiplier: float = 2.0) -> SignalDict:
    if "volume" not in df.columns or df["volume"].iloc[-window:].isna().all():
        return {"source": "Volume", "signal": "HOLD", "confidence": 0, "reason": "No volume data"}

    vol = df["volume"].iloc[-1]
    vol_ma = df["volume"].rolling(window=window).mean().iloc[-1]

    if vol_ma == 0 or np.isnan(vol_ma):
        return {"source": "Volume", "signal": "HOLD", "confidence": 0, "reason": "Volume MA invalid"}

    if vol > multiplier * vol_ma:
        # Determine direction by comparing price change in last candle
        price_change = df["close"].iloc[-1] - df["open"].iloc[-1]
        if price_change > 0:
            sig = "BUY"
        else:
            sig = "SELL"
        confidence = _clamp((vol / vol_ma - multiplier) / multiplier * 100)
        reason = "Volume spike detected"
    else:
        sig = "HOLD"
        confidence = 0
        reason = "No notable volume spike"

    return {"source": "Volume", "signal": sig, "confidence": confidence, "reason": reason}


# ---------------------------------------------------------------------------
# Aggregate helper
# ---------------------------------------------------------------------------

def generate_indicator_signals(df: pd.DataFrame) -> List[SignalDict]:
    """Compute all indicator signals for a single asset."""
    return [
        rsi_signal(df),
        macd_signal(df),
        bollinger_signal(df),
        ma_crossover_signal(df),
        volume_spike_signal(df),
    ]