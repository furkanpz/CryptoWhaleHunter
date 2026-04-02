from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from crypto_whale_hunter.models import CoinState
from crypto_whale_hunter.repository import SQLiteSignalRepository


class RepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "database.db"
        self.repository = SQLiteSignalRepository(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_initialize_creates_missing_symbols(self) -> None:
        self.repository.initialize(["BTCUSDT", "ETHUSDT", "BTCUSDT"])

        states = self.repository.list_states()

        self.assertEqual([state.coinname for state in states], ["BTCUSDT", "ETHUSDT"])
        self.assertEqual(states[0].signal_count, 0)
        self.assertEqual(states[0].signal_type, "long")

    def test_upsert_updates_existing_state(self) -> None:
        self.repository.initialize(["BTCUSDT"])
        self.repository.upsert_state(
            CoinState(
                coinname="BTCUSDT",
                last_signal_time=123,
                last_total_volume_usdt=456.78,
                signal_count=3,
                signal_type="short",
                first_signal_time=99,
            )
        )

        state = self.repository.get_coin_state("BTCUSDT")

        self.assertEqual(state.last_signal_time, 123)
        self.assertEqual(state.last_total_volume_usdt, 456.78)
        self.assertEqual(state.signal_count, 3)
        self.assertEqual(state.signal_type, "short")
