"""Binance public REST feeder."""

from __future__ import annotations

from typing import Any

import httpx
import pandas as pd

from orderflowkit.schemas.bars import normalize_bars
from orderflowkit.schemas.trades import normalize_trades
from orderflowkit.utils.time import to_milliseconds


class BinanceRestFeeder:
    """Fetch Binance Spot klines and aggregate trades from public REST endpoints."""

    source = "binance"

    def __init__(self, *, base_url: str = "https://api.binance.com", timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch(self, symbol: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        """Alias for ``fetch_klines``."""

        return self.fetch_klines(symbol=symbol, start=start, end=end, interval=interval)

    def fetch_klines(
        self, symbol: str, start: str, end: str, interval: str = "1d", limit: int = 1000
    ) -> pd.DataFrame:
        """Fetch public klines and normalize to the bar schema."""

        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "startTime": to_milliseconds(start),
            "endTime": to_milliseconds(end),
            "limit": limit,
        }
        data = self._get_json("/api/v3/klines", params=params)
        frame = pd.DataFrame(
            data,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_volume",
                "taker_buy_quote_volume",
                "ignore",
            ],
        )
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
        return normalize_bars(frame, symbol=symbol.upper(), source=self.source, interval=interval)

    def fetch_trades(self, symbol: str, start: str, end: str, limit: int = 1000) -> pd.DataFrame:
        """Fetch public aggregate trades and normalize to the trade schema."""

        params = {
            "symbol": symbol.upper(),
            "startTime": to_milliseconds(start),
            "endTime": to_milliseconds(end),
            "limit": limit,
        }
        data = self._get_json("/api/v3/aggTrades", params=params)
        frame = pd.DataFrame(data)
        if frame.empty:
            return normalize_trades(
                pd.DataFrame(
                    columns=["timestamp", "trade_id", "price", "quantity", "is_buyer_maker"]
                ),
                symbol=symbol.upper(),
                source=self.source,
            )
        frame = frame.rename(
            columns={
                "a": "trade_id",
                "p": "price",
                "q": "quantity",
                "T": "timestamp",
                "m": "is_buyer_maker",
            }
        )
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
        frame["side"] = frame["is_buyer_maker"].map({True: "sell", False: "buy"})
        return normalize_trades(frame, symbol=symbol.upper(), source=self.source)

    def _get_json(self, path: str, *, params: dict[str, Any]) -> Any:
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            response = client.get(path, params=params)
            response.raise_for_status()
            return response.json()
