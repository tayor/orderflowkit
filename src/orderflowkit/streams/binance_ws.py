"""Binance Spot public depth stream."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

import orjson

from orderflowkit.utils.exceptions import OptionalDependencyError
from orderflowkit.utils.time import utc_now


def normalize_binance_depth_message(
    message: dict[str, Any], *, symbol: str
) -> list[dict[str, object]]:
    """Normalize a Binance depth update into one event per changed price level."""

    ts_exchange = (
        datetime.fromtimestamp(float(message.get("E", 0)) / 1000.0, tz=timezone.utc)
        if message.get("E")
        else None
    )
    ts_local = utc_now().to_pydatetime()
    first_update_id = int(message["U"]) if "U" in message else None
    last_update_id = int(message["u"]) if "u" in message else None
    raw_payload = orjson.dumps(message).decode("utf-8")
    rows: list[dict[str, object]] = []
    for side, key in (("bid", "b"), ("ask", "a")):
        for price, size in message.get(key, []):
            rows.append(
                {
                    "ts_exchange": ts_exchange,
                    "ts_local": ts_local,
                    "exchange": "binance",
                    "symbol": symbol.upper(),
                    "event_type": "delta",
                    "side": side,
                    "price": float(price),
                    "size": float(size),
                    "update_id": last_update_id,
                    "first_update_id": first_update_id,
                    "last_update_id": last_update_id,
                    "sequence": str(last_update_id) if last_update_id is not None else None,
                    "is_snapshot": False,
                    "raw_payload": raw_payload,
                }
            )
    return rows


class BinanceDepthStream:
    """Async iterator over Binance Spot public diff-depth events."""

    def __init__(self, symbol: str, *, depth: int = 100, speed: str = "100ms") -> None:
        self.symbol = symbol.upper()
        self.depth = depth
        self.speed = speed
        self.url = f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}@depth@{speed}"

    def __aiter__(self) -> AsyncIterator[dict[str, object]]:
        """Return the normalized event generator."""

        return self.events()

    async def events(self) -> AsyncIterator[dict[str, object]]:
        """Connect to Binance and yield normalized L2 events."""

        try:
            import websockets
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise OptionalDependencyError(
                "Install OrderFlowKit[stream] to use BinanceDepthStream"
            ) from exc

        async with websockets.connect(self.url, ping_interval=20, ping_timeout=20) as websocket:
            async for raw_message in websocket:
                message = orjson.loads(raw_message)
                for row in normalize_binance_depth_message(message, symbol=self.symbol):
                    yield row
