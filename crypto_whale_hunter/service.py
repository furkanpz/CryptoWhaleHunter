from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from crypto_whale_hunter.coinlist import load_coinlist
from crypto_whale_hunter.config import Settings
from crypto_whale_hunter.exceptions import MarketDataError
from crypto_whale_hunter.notifier import NotificationError
from crypto_whale_hunter.signals import apply_decision, evaluate_signal

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScanSummary:
    symbols_scanned: int
    notifications_sent: int
    skipped_symbols: int


class SignalScannerService:
    def __init__(self, settings: Settings, repository, market_data, notifier) -> None:
        self.settings = settings
        self.repository = repository
        self.market_data = market_data
        self.notifier = notifier

    def run_forever(self) -> None:
        LOGGER.info("Starting signal scanner.")
        while True:
            summary = self.run_once()
            LOGGER.info("Scan completed: %s", summary)
            time.sleep(self.settings.poll_interval_seconds)

    def run_once(self) -> ScanSummary:
        symbols = load_coinlist(self.settings.coinlist_path)
        if not symbols:
            raise ValueError(f"No symbols found in coin list: {self.settings.coinlist_path}")

        self.repository.initialize(symbols)

        notifications_sent = 0
        skipped_symbols = 0
        for symbol in symbols:
            now_ts = int(time.time())
            try:
                snapshot = self.market_data.fetch_snapshot(symbol)
            except MarketDataError as exc:
                skipped_symbols += 1
                LOGGER.warning("%s", exc)
                continue

            current_state = self.repository.get_coin_state(symbol)
            decision = evaluate_signal(
                snapshot=snapshot,
                state=current_state,
                cooldown_seconds=self.settings.signal_cooldown_seconds,
                overbought_threshold=self.settings.rsi_overbought,
                oversold_threshold=self.settings.rsi_oversold,
                min_recent_volume_usdt=self.settings.min_recent_volume_usdt,
                now_ts=now_ts,
            )
            if decision is None:
                continue

            try:
                self.notifier.notify(decision)
            except NotificationError as exc:
                skipped_symbols += 1
                LOGGER.error("Notification failed for %s: %s", symbol, exc)
                continue

            new_state = apply_decision(current_state, decision, now_ts)
            self.repository.upsert_state(new_state)
            notifications_sent += 1
            LOGGER.info(
                "Signal sent for %s: type=%s count=%s volume=%s",
                symbol,
                decision.signal_type,
                decision.signal_count,
                decision.recent_volume_usdt,
            )

        return ScanSummary(
            symbols_scanned=len(symbols),
            notifications_sent=notifications_sent,
            skipped_symbols=skipped_symbols,
        )
