import logging
from datetime import datetime, timezone

import httpx

from config import AlertConfig


class Alerter:
    def __init__(self, config: AlertConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def send(self, event: str, message: str, context: dict | None = None) -> None:
        context = context or {}
        payload = {
            "event": event,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": context,
        }

        self.logger.error("ALERT %s | %s | %s", event, message, context)

        self._send_webhook(payload)
        self._send_telegram(payload)

    def _send_webhook(self, payload: dict) -> None:
        if not self.config.webhook_url:
            return

        try:
            httpx.post(
                self.config.webhook_url,
                json=payload,
                timeout=10.0,
            ).raise_for_status()
        except Exception:
            self.logger.exception("Failed to send alert webhook")

    def _send_telegram(self, payload: dict) -> None:
        token = self.config.telegram_bot_token
        chat_id = self.config.telegram_chat_id

        if not token or not chat_id:
            return

        context_text = "\n".join(
            f"{key}: {value}"
            for key, value in payload["context"].items()
        )

        text = (
            f"HH scraper alert: {payload['event']}\n"
            f"{payload['message']}\n"
            f"{context_text}"
        ).strip()

        try:
            httpx.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=10.0,
            ).raise_for_status()
        except Exception:
            self.logger.exception("Failed to send Telegram alert")
