"""OHLCV bar schema helpers."""

from __future__ import annotations

import pandas as pd

from orderflowkit.utils.validators import require_columns

BAR_COLUMNS = [
    "timestamp",
    "symbol",
    "source",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "dollar_volume",
    "interval",
]


def normalize_bars(
    frame: pd.DataFrame,
    *,
    symbol: str,
    source: str,
    interval: str,
    timestamp_column: str = "timestamp",
) -> pd.DataFrame:
    """Normalize a bar DataFrame into the standard OrderFlowKit schema."""

    lower = {str(column).lower(): column for column in frame.columns}
    required = ["open", "high", "low", "close", "volume"]
    missing = [column for column in required if column not in lower]
    if missing:
        require_columns(frame, missing, name="bars")

    normalized = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(frame[timestamp_column], utc=True)
            if timestamp_column in frame.columns
            else pd.to_datetime(frame.index, utc=True),
            "symbol": symbol,
            "source": source,
            "open": pd.to_numeric(frame[lower["open"]], errors="coerce"),
            "high": pd.to_numeric(frame[lower["high"]], errors="coerce"),
            "low": pd.to_numeric(frame[lower["low"]], errors="coerce"),
            "close": pd.to_numeric(frame[lower["close"]], errors="coerce"),
            "volume": pd.to_numeric(frame[lower["volume"]], errors="coerce").fillna(0.0),
            "interval": interval,
        }
    )
    normalized["dollar_volume"] = normalized["close"] * normalized["volume"]
    return normalized[BAR_COLUMNS].sort_values("timestamp").reset_index(drop=True)
