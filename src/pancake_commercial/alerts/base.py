"""Alert sender implementations."""

from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..models import AlertConfig, NormalizedConversation, PageConfig, StageDecision


class AlertSender:
    def send_alert(self, text: str) -> dict:
        raise NotImplementedError


class NoopAlertSender(AlertSender):
    def __init__(self, logger=None):
        self.logger = logger

    def send_alert(self, text: str) -> dict:
        if self.logger:
            self.logger.info("NOOP alert: %s", text)
        return {"success": True, "provider": "noop"}


class TelegramAlertSender(AlertSender):
    def __init__(self, bot_token: str, chat_id: str, logger=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = logger

    def send_alert(self, text: str) -> dict:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = urlencode({"chat_id": self.chat_id, "text": text}).encode("utf-8")
        request = Request(url, data=payload, method="POST")
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        if self.logger:
            self.logger.info("Telegram alert sent")
        return data


def create_alert_sender(config: AlertConfig, logger=None) -> AlertSender:
    provider = (config.provider or "noop").lower()
    if provider == "telegram":
        if not config.telegram_bot_token or not config.telegram_chat_id:
            raise ValueError("Telegram provider requires telegram_bot_token and telegram_chat_id.")
        return TelegramAlertSender(config.telegram_bot_token, config.telegram_chat_id, logger=logger)
    return NoopAlertSender(logger=logger)


def format_stage_alert(page: PageConfig, conversation: NormalizedConversation, decision: StageDecision) -> str:
    customer = conversation.customer_name or conversation.customer_id or "unknown customer"
    excerpt = decision.customer_message_text.strip() if decision.customer_message_text else "(no message)"
    return (
        f"[Pancake][Stage {decision.actual_stage}] {page.name}\n"
        f"Conversation: {conversation.conversation_id}\n"
        f"Customer: {customer}\n"
        f"Wait: {decision.wait_minutes} minutes\n"
        f"Message: {excerpt}"
    )
