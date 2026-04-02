from __future__ import annotations

from typing import Optional

from crypto_whale_hunter.models import CoinState, MarketSnapshot, SignalDecision


def evaluate_signal(
    snapshot: MarketSnapshot,
    state: CoinState,
    cooldown_seconds: int,
    overbought_threshold: float,
    oversold_threshold: float,
    min_recent_volume_usdt: float,
    now_ts: int,
) -> Optional[SignalDecision]:
    signal_type = _resolve_signal_type(snapshot.rsi, overbought_threshold, oversold_threshold)
    if signal_type is None:
        return None
    if snapshot.recent_volume_usdt < min_recent_volume_usdt:
        return None
    if snapshot.daily_volume_usdt <= 0:
        return None
    if state.signal_type == signal_type and state.last_signal_time + cooldown_seconds > now_ts:
        return None

    is_same_direction = state.signal_type == signal_type
    base_count = state.signal_count if is_same_direction else 0
    base_volume = state.last_total_volume_usdt if is_same_direction else 0.0
    volume_percent = round((snapshot.recent_volume_usdt / snapshot.daily_volume_usdt) * 100, 2)
    cumulative_volume = round(base_volume + snapshot.recent_volume_usdt, 2)

    return SignalDecision(
        symbol=snapshot.symbol,
        signal_type=signal_type,
        recent_volume_usdt=round(snapshot.recent_volume_usdt, 2),
        volume_percent=volume_percent,
        last_price=snapshot.last_price,
        cumulative_volume_usdt=cumulative_volume,
        signal_count=base_count + 1,
    )


def apply_decision(state: CoinState, decision: SignalDecision, now_ts: int) -> CoinState:
    first_signal_time = state.first_signal_time or now_ts
    if state.signal_type != decision.signal_type or state.signal_count == 0:
        first_signal_time = now_ts

    return CoinState(
        coinname=state.coinname,
        last_signal_time=now_ts,
        last_total_volume_usdt=decision.cumulative_volume_usdt,
        signal_count=decision.signal_count,
        signal_type=decision.signal_type,
        first_signal_time=first_signal_time,
    )


def _resolve_signal_type(
    rsi: float,
    overbought_threshold: float,
    oversold_threshold: float,
) -> Optional[str]:
    if rsi >= overbought_threshold:
        return "long"
    if rsi <= oversold_threshold:
        return "short"
    return None
