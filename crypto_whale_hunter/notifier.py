from __future__ import annotations

import logging
import random
from typing import Callable, List, Optional

from crypto_whale_hunter.models import SignalDecision

LOGGER = logging.getLogger(__name__)


class NotificationError(RuntimeError):
    """Raised when Telegram delivery fails."""


class TelegramNotifier:
    def __init__(
        self,
        bot_tokens: List[str],
        chat_id: str,
        plus_bot_token: Optional[str] = None,
        plus_chat_id: Optional[str] = None,
        bot_factory: Optional[Callable[[str], object]] = None,
    ) -> None:
        self.bot_tokens = bot_tokens
        self.chat_id = chat_id
        self.plus_bot_token = plus_bot_token
        self.plus_chat_id = plus_chat_id
        self.bot_factory = bot_factory or self._build_bot

    def _build_bot(self, token: str) -> object:
        import telebot

        return telebot.TeleBot(token, parse_mode="html")

    def notify(self, decision: SignalDecision) -> str:
        if not self.bot_tokens:
            raise NotificationError("No Telegram bot tokens configured.")

        message = build_signal_message(decision)
        token = random.choice(self.bot_tokens)
        try:
            self.bot_factory(token).send_message(self.chat_id, message)
        except Exception as exc:  # pragma: no cover - depends on Telegram runtime
            raise NotificationError(f"Failed to send Telegram message: {exc}") from exc

        if decision.volume_percent >= 1 and self.plus_bot_token and self.plus_chat_id:
            try:
                self.bot_factory(self.plus_bot_token).send_message(self.plus_chat_id, message)
            except Exception as exc:  # pragma: no cover - depends on Telegram runtime
                LOGGER.warning("Failed to relay plus Telegram message: %s", exc)

        return message


class TelegramStatusPublisher:
    def __init__(
        self,
        bot_token: Optional[str],
        chat_id: Optional[str],
        message_id: int,
        bot_factory: Optional[Callable[[str], object]] = None,
    ) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.message_id = message_id
        self.bot_factory = bot_factory or self._build_bot

    def _build_bot(self, token: str) -> object:
        import telebot

        return telebot.TeleBot(token, parse_mode="html")

    def publish(self, message: str) -> None:
        if not self.bot_token or not self.chat_id:
            raise NotificationError("Status bot token or chat id is not configured.")
        try:
            self.bot_factory(self.bot_token).edit_message_text(
                message,
                chat_id=self.chat_id,
                message_id=self.message_id,
            )
        except Exception as exc:  # pragma: no cover - depends on Telegram runtime
            raise NotificationError(f"Failed to publish status message: {exc}") from exc


def build_signal_message(decision: SignalDecision) -> str:
    critical = _critical_label(decision.volume_percent)
    header = "LONG" if decision.signal_type == "long" else "SHORT"
    color = "🟢" if decision.signal_type == "long" else "🔴"
    total_label = "T-Long" if decision.signal_type == "long" else "T-Short"
    count_label = "Long" if decision.signal_type == "long" else "Short"
    return (
        f"{color} CryptoGPT - {header} {color}\n"
        f"💎 Coin: #{decision.symbol} {critical}\n"
        f"💰 Volume: {decision.recent_volume_usdt:,.2f}$ (%{decision.volume_percent})\n"
        f"💲 Price: {decision.last_price}$\n"
        f"💵 {total_label}: {decision.cumulative_volume_usdt:,.2f}$\n"
        f"🎚 Count: {decision.signal_count}. {count_label}"
    )


def _critical_label(percent: float) -> str:
    if percent >= 3:
        return "🔥🔥🔥"
    if percent >= 2:
        return "🔥🔥"
    if percent >= 1:
        return "🔥"
    return ""
