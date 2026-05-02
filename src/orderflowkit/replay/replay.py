"""Replay normalized L2 events into book states."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import sleep

import pandas as pd

from orderflowkit.book import LocalBook, Side


@dataclass(frozen=True, slots=True)
class BookState:
    """Immutable snapshot emitted during replay."""

    ts: pd.Timestamp | None
    symbol: str
    exchange: str
    mid: float | None
    spread_bps: float | None
    bids: tuple[tuple[float, float], ...]
    asks: tuple[tuple[float, float], ...]
    valid: bool
    status: str

    def imbalance(self, levels: int = 10) -> float | None:
        """Compute top-N imbalance from the captured state."""

        bid_depth = sum(size for _, size in self.bids[:levels])
        ask_depth = sum(size for _, size in self.asks[:levels])
        total = bid_depth + ask_depth
        if total <= 0:
            return None
        return (bid_depth - ask_depth) / total


class Replay:
    """Replay normalized L2 event Parquet files."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def books(self, speed: str | float = "max") -> list[BookState]:
        """Replay all events and return reconstructed book states."""

        events = pd.read_parquet(self.path).sort_values("ts_local").reset_index(drop=True)
        if events.empty:
            return []
        first = events.iloc[0]
        book = LocalBook(symbol=str(first["symbol"]), exchange=str(first["exchange"]), depth=100)
        states: list[BookState] = []
        previous_ts: pd.Timestamp | None = None
        multiplier = _speed_multiplier(speed)
        for event in events.to_dict(orient="records"):
            current_ts = (
                pd.Timestamp(event.get("ts_local")) if event.get("ts_local") is not None else None
            )
            if multiplier is not None and previous_ts is not None and current_ts is not None:
                delay = max((current_ts - previous_ts).total_seconds() / multiplier, 0.0)
                if delay > 0:
                    sleep(min(delay, 1.0))
            book.apply(event)
            previous_ts = current_ts
            states.append(
                BookState(
                    ts=book.last_local_ts,
                    symbol=book.symbol,
                    exchange=book.exchange,
                    mid=book.mid,
                    spread_bps=book.spread_bps,
                    bids=tuple((level.price, level.size) for level in book.top_n(Side.BID, 100)),
                    asks=tuple((level.price, level.size) for level in book.top_n(Side.ASK, 100)),
                    valid=book.valid,
                    status=book.status.value,
                )
            )
        return states


def _speed_multiplier(speed: str | float) -> float | None:
    if speed == "max":
        return None
    if isinstance(speed, int | float):
        return float(speed)
    value = str(speed).rstrip("x")
    return float(value)
