"""Normalized L2 event schema."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

L2_EVENT_COLUMNS = [
    "ts_exchange",
    "ts_local",
    "exchange",
    "symbol",
    "event_type",
    "side",
    "price",
    "size",
    "update_id",
    "first_update_id",
    "last_update_id",
    "sequence",
    "is_snapshot",
    "raw_payload",
]


class L2Event(BaseModel):
    """One normalized L2 price-level event."""

    model_config = ConfigDict(extra="allow")

    ts_exchange: datetime | None = None
    ts_local: datetime
    exchange: str
    symbol: str
    event_type: str = "delta"
    side: str
    price: float
    size: float
    update_id: int | None = None
    first_update_id: int | None = None
    last_update_id: int | None = None
    sequence: str | None = None
    is_snapshot: bool = False
    raw_payload: str | None = Field(default=None, repr=False)

    def as_row(self) -> dict[str, object]:
        """Return a dict ordered according to the public L2 event schema."""

        data = self.model_dump()
        return {column: data.get(column) for column in L2_EVENT_COLUMNS}
