from __future__ import annotations

import unittest

from crypto_whale_hunter.models import CoinState
from crypto_whale_hunter.status import build_status_message


class StatusTests(unittest.TestCase):
    def test_build_status_message_uses_btc_eth_and_alt_aggregation(self) -> None:
        message = build_status_message(
            [
                CoinState(
                    "BTCUSDT",
                    last_total_volume_usdt=2_000_000_000,
                    signal_count=3,
                    signal_type="long",
                ),
                CoinState(
                    "ETHUSDT",
                    last_total_volume_usdt=600_000_000,
                    signal_count=2,
                    signal_type="short",
                ),
                CoinState(
                    "SOLUSDT",
                    last_total_volume_usdt=200_000_000,
                    signal_count=1,
                    signal_type="long",
                ),
                CoinState(
                    "AVAXUSDT",
                    last_total_volume_usdt=100_000_000,
                    signal_count=1,
                    signal_type="long",
                ),
            ]
        )

        self.assertIn("Bitcoin: Long", message)
        self.assertIn("Status: Extremly", message)
        self.assertIn("Ethereum: Short", message)
        self.assertIn("Altcoins: Long", message)
