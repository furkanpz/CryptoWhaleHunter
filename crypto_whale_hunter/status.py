from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from crypto_whale_hunter.models import CoinState


@dataclass(frozen=True)
class MarketStatus:
    direction_label: str
    total_label: str
    severity: str


class StatusService:
    def __init__(self, repository, publisher) -> None:
        self.repository = repository
        self.publisher = publisher

    def publish(self, dry_run: bool = False) -> str:
        message = build_status_message(self.repository.list_states())
        if not dry_run:
            self.publisher.publish(message)
        return message


def build_status_message(states: Iterable[CoinState]) -> str:
    btc_state = None
    eth_state = None
    alt_long_count = 0
    alt_short_count = 0
    alt_long_total = 0.0
    alt_short_total = 0.0

    for state in states:
        if state.coinname == "BTCUSDT":
            btc_state = state
            continue
        if state.coinname == "ETHUSDT":
            eth_state = state
            continue
        if state.signal_type == "long":
            alt_long_count += 1
            alt_long_total += state.last_total_volume_usdt
        elif state.signal_type == "short":
            alt_short_count += 1
            alt_short_total += state.last_total_volume_usdt

    btc_status = _build_btc_status(btc_state)
    eth_status = _build_eth_status(eth_state)
    alt_status = _build_alt_status(
        alt_long_count=alt_long_count,
        alt_short_count=alt_short_count,
        alt_long_total=alt_long_total,
        alt_short_total=alt_short_total,
    )

    return (
        "❗️ Crypto Status - CryptoGPT ❗️\n"
        f"👑 Bitcoin: {btc_status.direction_label}\n"
        f"💰 Total: {btc_status.total_label}$\n"
        f"🎚 Status: {btc_status.severity}\n\n"
        "❗️ Ethereum and Altcoins ❗️\n"
        f"💎 Ethereum: {eth_status.direction_label}\n"
        f"💰 Total: {eth_status.total_label}$\n"
        f"🎚 Status: {eth_status.severity}\n\n"
        f"💲 Altcoins: {alt_status.direction_label}\n"
        f"💰 Total: {alt_status.total_label}$"
    )


def _build_btc_status(state: Optional[CoinState]) -> MarketStatus:
    total = state.last_total_volume_usdt if state else 0.0
    count = state.signal_count if state else 0
    direction = _format_direction(state.signal_type if state else None)
    if count >= 4:
        severity = _severity(total, high=1_500_000_000, extreme=3_000_000_000)
    elif count >= 2:
        severity = _severity(total, high=1_000_000_000, extreme=1_500_000_000)
    elif count >= 1:
        severity = _severity(total, high=500_000_000, extreme=1_000_000_000)
    else:
        severity = "None"
    return MarketStatus(direction, _format_money(total), severity)


def _build_eth_status(state: Optional[CoinState]) -> MarketStatus:
    total = state.last_total_volume_usdt if state else 0.0
    count = state.signal_count if state else 0
    direction = _format_direction(state.signal_type if state else None)
    if count >= 4:
        severity = _severity(total, high=1_000_000_000, extreme=1_500_000_000)
    elif count >= 2:
        severity = _severity(total, high=500_000_000, extreme=1_000_000_000)
    elif count >= 1:
        severity = _severity(total, high=250_000_000, extreme=500_000_000)
    else:
        severity = "None"
    return MarketStatus(direction, _format_money(total), severity)


def _build_alt_status(
    alt_long_count: int,
    alt_short_count: int,
    alt_long_total: float,
    alt_short_total: float,
) -> MarketStatus:
    if alt_long_count > alt_short_count:
        return MarketStatus("Long", _format_money(alt_long_total), "Directional")
    if alt_short_count > alt_long_count:
        return MarketStatus("Short", _format_money(alt_short_total), "Directional")
    return MarketStatus("Long = Short", _format_money(alt_long_total + alt_short_total), "Balanced")


def _severity(total: float, high: float, extreme: float) -> str:
    if total >= extreme:
        return "Extremly"
    if total >= high:
        return "High"
    return "Medium"


def _format_direction(direction: Optional[str]) -> str:
    if direction == "long":
        return "Long"
    if direction == "short":
        return "Short"
    return "None"


def _format_money(amount: float) -> str:
    return f"{amount:,.2f}"
