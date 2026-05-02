"""Book snapshot schema."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

BOOK_SNAPSHOT_COLUMNS = [
    "ts_exchange",
    "ts_local",
    "exchange",
    "symbol",
    "level",
    "bid_price",
    "bid_size",
    "ask_price",
    "ask_size",
    "mid",
    "spread",
    "spread_bps",
    "microprice",
    "valid",
    "status",
]


class BookSnapshot(BaseModel):
    """One top-of-book or depth snapshot row."""

    ts_exchange: datetime | None = None
    ts_local: datetime
    exchange: str
    symbol: str
    level: int
    bid_price: float | None = None
    bid_size: float | None = None
    ask_price: float | None = None
    ask_size: float | None = None
    mid: float | None = None
    spread: float | None = None
    spread_bps: float | None = None
    microprice: float | None = None
    valid: bool
    status: str

    def as_row(self) -> dict[str, object]:
        """Return a dict ordered according to the public book snapshot schema."""

        data = self.model_dump()
        return {column: data.get(column) for column in BOOK_SNAPSHOT_COLUMNS}
