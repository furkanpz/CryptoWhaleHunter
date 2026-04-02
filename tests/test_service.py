from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from crypto_whale_hunter.config import Settings
from crypto_whale_hunter.models import MarketSnapshot
from crypto_whale_hunter.repository import SQLiteSignalRepository
from crypto_whale_hunter.service import SignalScannerService


class FakeMarketData:
    def __init__(self, snapshots) -> None:
        self.snapshots = snapshots

    def fetch_snapshot(self, symbol: str) -> MarketSnapshot:
        return self.snapshots[symbol]


class FakeNotifier:
    def __init__(self) -> None:
        self.messages = []

    def notify(self, decision) -> str:
        self.messages.append(decision)
        return "ok"


class ServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.coinlist_path = self.base_path / "coinlist.csv"
        self.coinlist_path.write_text("BTCUSDT\n", encoding="utf-8")
        self.db_path = self.base_path / "database.db"
        self.repository = SQLiteSignalRepository(self.db_path)
        self.original_env = dict(os.environ)
        os.environ["COINLIST_PATH"] = str(self.coinlist_path)
        os.environ["DB_PATH"] = str(self.db_path)
        os.environ["TELEGRAM_BOT_TOKENS"] = "token-1"
        os.environ["TELEGRAM_CHAT_ID"] = "chat-1"
        self.settings = Settings.from_env(env_file=self.base_path / ".env.missing")

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)
        self.temp_dir.cleanup()

    def test_run_once_bootstraps_and_persists_signal(self) -> None:
        market_data = FakeMarketData(
            {
                "BTCUSDT": MarketSnapshot(
                    symbol="BTCUSDT",
                    rsi=75.0,
                    daily_volume_usdt=2_000_000.0,
                    recent_volume_usdt=300_000.0,
                    last_price=62_000.0,
                )
            }
        )
        notifier = FakeNotifier()
        service = SignalScannerService(
            settings=self.settings,
            repository=self.repository,
            market_data=market_data,
            notifier=notifier,
        )

        summary = service.run_once()
        state = self.repository.get_coin_state("BTCUSDT")

        self.assertEqual(summary.symbols_scanned, 1)
        self.assertEqual(summary.notifications_sent, 1)
        self.assertEqual(len(notifier.messages), 1)
        self.assertEqual(state.signal_count, 1)
        self.assertEqual(state.signal_type, "long")
        self.assertEqual(state.last_total_volume_usdt, 300_000.0)
