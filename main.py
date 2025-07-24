"""Main entry point for the breakout scalping signal bot."""
from __future__ import annotations

import time
from datetime import datetime

import schedule

from config import SCHEDULE_INTERVAL_MINUTES
from logger import get_logger
from telegram_alert import TelegramAlerter

logger = get_logger()
alerter = TelegramAlerter()


# ---------------------------------------------------------------------------
# Core bot execution logic (placeholder for now)
# ---------------------------------------------------------------------------

def run_bot() -> None:
    """Run the entire analysis pipeline once and send signals as alerts.

    This function will eventually:
    1. Fetch data from all sources for each asset.
    2. Calculate indicators.
    3. Generate individual signals and aggregate consensus.
    4. Send Telegram alert(s) when strong BUY/SELL conditions are met.
    """
    logger.info("Bot run started at %s", datetime.utcnow().isoformat())

    # TODO: Implement full data processing and signal generation pipeline.
    # For now, just send a heartbeat message every run to verify scheduler.
    alerter.send_message("✅ Breakout bot heartbeat: running on schedule.")

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