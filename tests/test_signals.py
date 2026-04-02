from __future__ import annotations

import unittest

from crypto_whale_hunter.models import CoinState, MarketSnapshot
from crypto_whale_hunter.signals import apply_decision, evaluate_signal


class SignalTests(unittest.TestCase):
    def test_returns_long_signal_when_thresholds_match(self) -> None:
        decision = evaluate_signal(
            snapshot=MarketSnapshot(
                symbol="BTCUSDT",
                rsi=71.0,
                daily_volume_usdt=10_000_000.0,
                recent_volume_usdt=300_000.0,
                last_price=62_500.0,
            ),
            state=CoinState(coinname="BTCUSDT", signal_type="long"),
            cooldown_seconds=600,
            overbought_threshold=70,
            oversold_threshold=30,
            min_recent_volume_usdt=200_000,
            now_ts=1_000,
        )

        self.assertIsNotNone(decision)
        self.assertEqual(decision.signal_type, "long")
        self.assertEqual(decision.signal_count, 1)
        self.assertEqual(decision.cumulative_volume_usdt, 300_000.0)

    def test_blocks_same_direction_signal_inside_cooldown(self) -> None:
        decision = evaluate_signal(
            snapshot=MarketSnapshot(
                symbol="BTCUSDT",
                rsi=71.0,
                daily_volume_usdt=10_000_000.0,
                recent_volume_usdt=300_000.0,
                last_price=62_500.0,
            ),
            state=CoinState(
                coinname="BTCUSDT",
                last_signal_time=900,
                last_total_volume_usdt=150_000.0,
                signal_count=2,
                signal_type="long",
            ),
            cooldown_seconds=600,
            overbought_threshold=70,
            oversold_threshold=30,
            min_recent_volume_usdt=200_000,
            now_ts=1_000,
        )

        self.assertIsNone(decision)

    def test_direction_flip_resets_count_and_volume(self) -> None:
        decision = evaluate_signal(
            snapshot=MarketSnapshot(
                symbol="BTCUSDT",
                rsi=20.0,
                daily_volume_usdt=10_000_000.0,
                recent_volume_usdt=400_000.0,
                last_price=62_500.0,
            ),
            state=CoinState(
                coinname="BTCUSDT",
                last_signal_time=950,
                last_total_volume_usdt=900_000.0,
                signal_count=4,
                signal_type="long",
            ),
            cooldown_seconds=600,
            overbought_threshold=70,
            oversold_threshold=30,
            min_recent_volume_usdt=200_000,
            now_ts=1_000,
        )

        self.assertIsNotNone(decision)
        self.assertEqual(decision.signal_type, "short")
        self.assertEqual(decision.signal_count, 1)
        self.assertEqual(decision.cumulative_volume_usdt, 400_000.0)

    def test_recent_volume_floor_is_enforced(self) -> None:
        decision = evaluate_signal(
            snapshot=MarketSnapshot(
                symbol="BTCUSDT",
                rsi=71.0,
                daily_volume_usdt=10_000_000.0,
                recent_volume_usdt=199_999.0,
                last_price=62_500.0,
            ),
            state=CoinState(coinname="BTCUSDT", signal_type="long"),
            cooldown_seconds=600,
            overbought_threshold=70,
            oversold_threshold=30,
            min_recent_volume_usdt=200_000,
            now_ts=1_000,
        )

        self.assertIsNone(decision)

    def test_apply_decision_persists_new_state(self) -> None:
        decision = evaluate_signal(
            snapshot=MarketSnapshot(
                symbol="BTCUSDT",
                rsi=71.0,
                daily_volume_usdt=10_000_000.0,
                recent_volume_usdt=300_000.0,
                last_price=62_500.0,
            ),
            state=CoinState(coinname="BTCUSDT", signal_type="long"),
            cooldown_seconds=600,
            overbought_threshold=70,
            oversold_threshold=30,
            min_recent_volume_usdt=200_000,
            now_ts=1_000,
        )

        state = apply_decision(CoinState(coinname="BTCUSDT"), decision, now_ts=1_000)

        self.assertEqual(state.last_signal_time, 1_000)
        self.assertEqual(state.signal_count, 1)
        self.assertEqual(state.signal_type, "long")
