"""Trade schema helpers."""

from __future__ import annotations

import pandas as pd

TRADE_COLUMNS = [
    "timestamp",
    "symbol",
    "source",
    "trade_id",
    "price",
    "quantity",
    "side",
    "is_buyer_maker",
    "notional",
]


def normalize_trades(frame: pd.DataFrame, *, symbol: str, source: str) -> pd.DataFrame:
    """Normalize trades into the standard OrderFlowKit schema."""

    normalized = frame.copy()
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], utc=True)
    normalized["symbol"] = symbol
    normalized["source"] = source
    normalized["price"] = pd.to_numeric(normalized["price"], errors="coerce")
    normalized["quantity"] = pd.to_numeric(normalized["quantity"], errors="coerce")
    normalized["notional"] = normalized["price"] * normalized["quantity"]
    if "trade_id" not in normalized.columns:
        normalized["trade_id"] = normalized.index.astype(str)
    if "side" not in normalized.columns:
        normalized["side"] = None
    if "is_buyer_maker" not in normalized.columns:
        normalized["is_buyer_maker"] = None
    return normalized[TRADE_COLUMNS].sort_values("timestamp").reset_index(drop=True)
