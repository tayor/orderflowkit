from __future__ import annotations

from collections.abc import AsyncIterator

import pandas as pd
import pytest


@pytest.fixture()
def sample_bars() -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=80, freq="D", tz="UTC")
    close = pd.Series([100 + index * 0.2 + ((-1) ** index) * 0.1 for index in range(len(dates))])
    return pd.DataFrame(
        {
            "timestamp": dates,
            "symbol": "SPY",
            "source": "fixture",
            "open": close - 0.2,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": [1_000_000 + index * 1000 for index in range(len(dates))],
            "dollar_volume": close * 1_000_000,
            "interval": "1d",
        }
    )


@pytest.fixture()
def sample_l2_events() -> pd.DataFrame:
    base = pd.Timestamp("2026-05-03T12:00:00Z")
    rows = [
        _event(base, "snapshot", "bid", 100.0, 2.0, 1, is_snapshot=True),
        _event(base, "snapshot", "ask", 101.0, 2.0, 1, is_snapshot=True),
        _event(base + pd.Timedelta(seconds=1), "delta", "bid", 100.5, 1.5, 2),
        _event(base + pd.Timedelta(seconds=1), "delta", "ask", 101.0, 1.0, 2),
        _event(base + pd.Timedelta(seconds=2), "delta", "bid", 99.5, 0.5, 3),
        _event(base + pd.Timedelta(seconds=3), "delta", "ask", 101.5, 2.5, 4),
    ]
    return pd.DataFrame(rows)


def _event(
    timestamp: pd.Timestamp,
    event_type: str,
    side: str,
    price: float,
    size: float,
    update_id: int,
    *,
    is_snapshot: bool = False,
) -> dict[str, object]:
    return {
        "ts_exchange": timestamp,
        "ts_local": timestamp,
        "exchange": "binance",
        "symbol": "BTCUSDT",
        "event_type": event_type,
        "side": side,
        "price": price,
        "size": size,
        "update_id": update_id,
        "first_update_id": update_id,
        "last_update_id": update_id,
        "sequence": str(update_id),
        "is_snapshot": is_snapshot,
        "raw_payload": None,
    }


class FiniteAsyncStream:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows

    async def __aiter__(self) -> AsyncIterator[dict[str, object]]:
        for row in self.rows:
            yield row
