"""Telegram alerter (reused from v1).

Sends a plain-text message via the Telegram Bot API. Credentials come from .env
(TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID). Fails soft: if it is not configured, it
logs a warning and returns False rather than raising, so the agent stays usable.
"""
from __future__ import annotations

import logging

import requests

from edgesentry.config import Config

log = logging.getLogger(__name__)


class TelegramAlerter:
    def __init__(self, cfg: Config) -> None:
        self.token = cfg.telegram.bot_token
        self.chat_id = cfg.telegram.chat_id

    def send(self, message: str) -> bool:
        if not self.token or not self.chat_id:
            log.warning("Telegram not configured; skipping alert.")
            return False
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={"chat_id": self.chat_id, "text": message},
                timeout=10,
            )
            resp.raise_for_status()
            return True
        except requests.RequestException as exc:
            log.error("Telegram send failed: %s", exc)
            return False
