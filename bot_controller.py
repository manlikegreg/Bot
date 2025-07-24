"""Controller to start and stop the scheduled breakout bot run loop."""
from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Optional

import schedule

from config import SCHEDULE_INTERVAL_MINUTES
from logger import get_logger
from main import run_bot  # reusing existing run function (no side effects)
from performance import metrics

logger = get_logger()


class BotController:
    """Manage the lifecycle of the bot's scheduled execution."""

    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running: bool = False

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def start(self) -> bool:
        """Start the bot if not already running.

        Returns:
            True if started, False if it was already running.
        """
        if self._is_running:
            logger.info("Bot already running – start request ignored")
            return False

        logger.info("Starting bot controller …")
        metrics.bot_started()
        schedule.clear()
        schedule.every(SCHEDULE_INTERVAL_MINUTES).minutes.do(run_bot)

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._is_running = True
        logger.info("Bot started at %s", datetime.utcnow().isoformat())
        return True

    def stop(self) -> bool:
        """Stop the bot if it is running.

        Returns:
            True if stopped, False if it was already stopped.
        """
        if not self._is_running:
            logger.info("Bot is not running – stop request ignored")
            return False

        logger.info("Stopping bot controller …")
        metrics.bot_stopped()
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        schedule.clear()
        self._is_running = False
        logger.info("Bot stopped at %s", datetime.utcnow().isoformat())
        return True

    @property
    def is_running(self) -> bool:  # noqa: D401
        """Return True if the bot is currently running."""
        return self._is_running

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        """Background thread loop that ticks the schedule library."""
        logger.info("Bot loop thread started")
        while not self._stop_event.is_set():
            try:
                schedule.run_pending()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Error in scheduled job execution: %s", exc)
            time.sleep(1)
        logger.info("Bot loop thread exiting")