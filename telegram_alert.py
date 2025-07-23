"""Telegram alerting utility."""
from __future__ import annotations

import logging
from typing import Optional

import requests
from requests import Session, Response

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from logger import get_logger

logger: logging.Logger = get_logger()


class TelegramAlerter:
    """Helper class to send formatted Telegram messages."""

    _API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session or requests.Session()

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send a plain text message to the configured chat.

        Args:
            text: Message body.
            parse_mode: Telegram parse mode (Markdown, HTML, etc.).

        Returns:
            True if message sent successfully, False otherwise.
        """
        url: str = f"{self._API_URL}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }

        try:
            response: Response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Sent Telegram alert (%s characters)", len(text))
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send Telegram message: %s", exc, exc_info=False)
            return False