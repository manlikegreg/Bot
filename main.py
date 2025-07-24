"""Main entry point for the breakout scalping signal bot."""
from __future__ import annotations

import time
from datetime import datetime
from typing import List, Optional

import schedule

import pandas as pd

from config import ASSETS, SCHEDULE_INTERVAL_MINUTES
from data_sources.yfinance_source import fetch_ohlcv
from signals import compute_consensus
from logger import get_logger
from telegram_alert import TelegramAlerter

logger = get_logger()
alerter = TelegramAlerter()


# ---------------------------------------------------------------------------
# Core bot execution logic (placeholder for now)
# ---------------------------------------------------------------------------

def format_alert(consensus: dict, price: float) -> str:  # noqa: D401
    """Format the Telegram alert text according to spec."""
    pair = consensus["pair"]
    signal = consensus["signal"]
    confidence = consensus["confidence"]

    # Basic risk parameters (2% stop / take-profit)
    if signal == "BUY":
        sl = price * 0.98
        tp = price * 1.02
    else:  # SELL
        sl = price * 1.02
        tp = price * 0.98

    # Concatenate reasons
    reasons = ", ".join(s["reason"] for s in consensus["details"])

    msg = (
        "📊 Strong Signal Alert\n"
        f"Pair: {pair}\n"
        f"Signal: {signal}\n"
        f"Entry: ${price:,.2f}\n"
        f"SL: ${sl:,.2f}\n"
        f"TP: ${tp:,.2f}\n"
        "Timeframe: 15min to 1hr\n"
        f"Confidence: {confidence}%\n"
        f"Reason: {reasons}."
    )
    return msg


def run_bot() -> None:
    """Run the entire analysis pipeline once and send signals as alerts.

    This function will eventually:
    1. Fetch data from all sources for each asset.
    2. Calculate indicators.
    3. Generate individual signals and aggregate consensus.
    4. Send Telegram alert(s) when strong BUY/SELL conditions are met.
    """
    logger.info("Bot run started at %s", datetime.utcnow().isoformat())

    for pair in ASSETS:
        df: Optional[pd.DataFrame] = fetch_ohlcv(pair)
        if df is None:
            continue

        consensus = compute_consensus(pair, df)
        if not consensus:
            logger.info("No strong consensus for %s", pair)
            continue

        price = df["close"].iloc[-1]
        alert_text = format_alert(consensus, price)
        alerter.send_message(alert_text)

    logger.info("Bot run completed")


# ---------------------------------------------------------------------------
# Scheduler setup
# ---------------------------------------------------------------------------

def main() -> None:
    """Configure and start the 10-minute scheduler loop."""
    logger.info("Starting breakout scalping signal bot (interval=%s min)", SCHEDULE_INTERVAL_MINUTES)

    schedule.every(SCHEDULE_INTERVAL_MINUTES).minutes.do(run_bot)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error in scheduler: %s", exc)


if __name__ == "__main__":
    main()