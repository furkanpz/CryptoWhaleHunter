from __future__ import annotations

import logging

import pandas as pd

from crypto_whale_hunter.config import Settings
from crypto_whale_hunter.exceptions import MarketDataError
from crypto_whale_hunter.indicators import calculate_rsi, calculate_usdt_volume, latest_price
from crypto_whale_hunter.models import MarketSnapshot

LOGGER = logging.getLogger(__name__)


class BinanceFuturesMarketData:
    def __init__(self, settings: Settings) -> None:
        from ccxt import binanceusdm

        self.settings = settings
        self.client = binanceusdm({"enableRateLimit": True})

    def fetch_snapshot(self, symbol: str) -> MarketSnapshot:
        try:
            candles = self.client.fetch_ohlcv(
                symbol,
                timeframe=self.settings.timeframe,
                limit=self.settings.limit,
            )
        except Exception as exc:  # pragma: no cover - network exceptions vary by runtime
            raise MarketDataError(f"Failed to fetch OHLCV for {symbol}: {exc}") from exc

        data = pd.DataFrame(
            data=candles,
            columns=("Time", "Open", "High", "Low", "Close", "Volume"),
        )
        if data.empty:
            raise MarketDataError(f"Binance returned no OHLCV rows for {symbol}.")
        if len(data.index) < self.settings.limit:
            raise MarketDataError(
                f"Binance returned {len(data.index)} candles for {symbol}, "
                f"expected at least {self.settings.limit}."
            )

        rsi = calculate_rsi(data, self.settings.rsi_period)
        if rsi is None:
            raise MarketDataError(f"Failed to calculate RSI for {symbol}.")

        try:
            daily_volume = calculate_usdt_volume(data, self.settings.limit)
            recent_volume = calculate_usdt_volume(data, self.settings.recent_volume_window)
            price = latest_price(data)
        except ValueError as exc:
            raise MarketDataError(f"Invalid market data for {symbol}: {exc}") from exc

        LOGGER.debug(
            "Fetched market snapshot for %s: rsi=%.2f daily_volume=%.2f recent_volume=%.2f",
            symbol,
            rsi,
            daily_volume,
            recent_volume,
        )
        return MarketSnapshot(
            symbol=symbol,
            rsi=rsi,
            daily_volume_usdt=daily_volume,
            recent_volume_usdt=recent_volume,
            last_price=price,
        )
