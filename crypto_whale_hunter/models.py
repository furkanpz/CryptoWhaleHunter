from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoinState:
    coinname: str
    last_signal_time: int = 0
    last_total_volume_usdt: float = 0.0
    signal_count: int = 0
    signal_type: str = "long"
    first_signal_time: int = 0


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    rsi: float
    daily_volume_usdt: float
    recent_volume_usdt: float
    last_price: float


@dataclass(frozen=True)
class SignalDecision:
    symbol: str
    signal_type: str
    recent_volume_usdt: float
    volume_percent: float
    last_price: float
    cumulative_volume_usdt: float
    signal_count: int
