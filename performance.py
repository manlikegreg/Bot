"""Thread-safe performance metrics for the breakout bot."""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Dict, List


after_run_lock = threading.Lock()


class _Metrics:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.start_time: datetime | None = None
        self.run_count: int = 0
        self.signals_sent: int = 0
        self.last_run: datetime | None = None
        self.last_signals: List[Dict[str, Any]] = []  # consensus dicts

    # ------------------------------------------------------------------
    # Lifecycle events
    # ------------------------------------------------------------------

    def bot_started(self) -> None:
        with after_run_lock:
            self.reset()
            self.start_time = datetime.now(timezone.utc)

    def bot_stopped(self) -> None:
        with after_run_lock:
            # Keep historical metrics but mark stopped
            pass

    # ------------------------------------------------------------------
    # Run events
    # ------------------------------------------------------------------

    def record_run(self, signals: List[Dict[str, Any]]) -> None:
        with after_run_lock:
            self.run_count += 1
            self.last_run = datetime.now(timezone.utc)
            self.last_signals = signals
            self.signals_sent += len(signals)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def snapshot(self, is_running: bool) -> Dict[str, Any]:
        with after_run_lock:
            return {
                "running": is_running,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "run_count": self.run_count,
                "signals_sent": self.signals_sent,
                "last_run": self.last_run.isoformat() if self.last_run else None,
                "last_signals": self.last_signals,
            }


metrics = _Metrics()