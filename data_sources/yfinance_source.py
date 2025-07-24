"""Data fetcher using yfinance for both crypto, forex and commodities."""
from __future__ import annotations

from typing import Optional

import pandas as pd
import yfinance as yf

from logger import get_logger

logger = get_logger()

# Mapping from user-friendly pair names to yfinance tickers
PAIR_TO_TICKER: dict[str, str] = {
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "XRP/USD": "XRP-USD",
    "XAU/USD": "XAUUSD=X",  # spot gold
    "EUR/USD": "EURUSD=X",
}


def fetch_ohlcv(pair: str, period: str = "2d", interval: str = "15m") -> Optional[pd.DataFrame]:
    """Fetch recent OHLCV data for a trading pair.

    Args:
        pair: A pair string like "BTC/USD".
        period: Data period (e.g., "2d", "7d").
        interval: Candle interval (e.g., "15m", "30m").

    Returns:
        DataFrame indexed by datetime with lowercase columns (open, high, low, close, volume).
        Returns None when data is unavailable.
    """
    ticker = PAIR_TO_TICKER.get(pair)
    if ticker is None:
        logger.warning("Unsupported pair for yfinance fetch: %s", pair)
        return None

    try:
        df = yf.download(tickers=ticker, period=period, interval=interval, progress=False)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to fetch %s via yfinance: %s", pair, exc, exc_info=False)
        return None

    if df.empty:
        logger.warning("No data returned for %s (%s)", pair, ticker)
        return None

    # Normalise column names and drop adj close if exists
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    if "adj_close" in df.columns:
        df = df.drop(columns=["adj_close"])  # not needed for indicators

    return df