from __future__ import annotations

from typing import Optional

import pandas as pd
import pandas_ta as ta


def calculate_rsi(data: pd.DataFrame, period: int) -> Optional[float]:
    if data.empty or len(data.index) <= period:
        return None
    rsi_series = ta.rsi(data["Close"], length=period)
    if rsi_series is None or rsi_series.empty:
        return None
    latest = rsi_series.iloc[-1]
    if pd.isna(latest):
        return None
    return float(latest)


def calculate_usdt_volume(data: pd.DataFrame, periods: int) -> float:
    if len(data.index) < periods:
        raise ValueError(f"Not enough candle data: expected {periods}, got {len(data.index)}")
    subset = data.tail(periods)
    total = (subset["Volume"] * subset["Close"]).sum()
    return round(float(total), 2)


def latest_price(data: pd.DataFrame) -> float:
    if data.empty:
        raise ValueError("No candle data available.")
    return float(data["Close"].iloc[-1])
