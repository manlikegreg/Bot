"""Consensus signal aggregation module."""
from __future__ import annotations

from statistics import mean
from typing import Dict, List, Optional, Tuple

from indicators import SignalDict, generate_indicator_signals
from logger import get_logger

logger = get_logger()

Consensus = Dict[str, str | float | List[SignalDict]]


def compute_consensus(pair: str, df) -> Optional[Consensus]:  # type: ignore[return-type]
    """Generate consensus signal for a pair based on all indicators.

    Returns None when no strong signal.
    """
    indicator_signals = generate_indicator_signals(df)

    # Filter out HOLD
    actionable = [s for s in indicator_signals if s["signal"] in {"BUY", "SELL"}]
    if not actionable:
        return None

    buy_signals = [s for s in actionable if s["signal"] == "BUY"]
    sell_signals = [s for s in actionable if s["signal"] == "SELL"]

    avg_confidence = mean(s["confidence"] for s in actionable)

    if avg_confidence < 80:
        logger.debug("%s consensus below threshold: %.1f", pair, avg_confidence)
        return None

    final_signal: str
    if len(buy_signals) > len(sell_signals):
        final_signal = "BUY"
    elif len(sell_signals) > len(buy_signals):
        final_signal = "SELL"
    else:
        logger.debug("%s equal buy/sell counts; treating as no signal", pair)
        return None

    return {
        "pair": pair,
        "signal": final_signal,
        "confidence": round(avg_confidence, 1),
        "details": actionable,
    }