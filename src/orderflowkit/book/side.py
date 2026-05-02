"""Order-book side helpers."""

from __future__ import annotations

from enum import Enum


class Side(str, Enum):
    """Normalized order-book sides."""

    BID = "bid"
    ASK = "ask"


def normalize_side(side: str | Side) -> Side:
    """Normalize common side aliases into ``Side`` values."""

    if isinstance(side, Side):
        return side
    value = side.lower()
    if value in {"bid", "b", "buy"}:
        return Side.BID
    if value in {"ask", "a", "sell", "offer"}:
        return Side.ASK
    raise ValueError(f"Unknown book side: {side}")
