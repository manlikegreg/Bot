"""Centralised application logger."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import LOG_DIR

LOG_PATH: Path = LOG_DIR / "bot.log"

# Ensure log directory exists
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Create and configure logger
logger = logging.getLogger("breakout_bot")
logger.setLevel(logging.INFO)

# Create handlers
file_handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=5)
file_handler.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter and add to handlers
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Convenience function

def get_logger() -> logging.Logger:
    """Return the configured application logger."""
    return logger