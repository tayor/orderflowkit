"""Order-flow feature helpers."""

from __future__ import annotations

import pandas as pd


def add_flow_features(frame: pd.DataFrame, windows: list[str]) -> pd.DataFrame:
    """Add rolling quote-update counts when timestamps are available."""

    result = frame.copy()
    if "timestamp" not in result.columns:
        return result
    indexed = result.copy()
    indexed["timestamp"] = pd.to_datetime(indexed["timestamp"], utc=True)
    indexed = indexed.set_index("timestamp")
    for window in windows:
        result[f"quote_updates_{window}"] = (
            indexed["mid"].rolling(window).count().to_numpy() if "mid" in indexed.columns else 0
        )
    return result
