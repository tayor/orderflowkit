"""Volatility feature helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_volatility_features(frame: pd.DataFrame, windows: list[str]) -> pd.DataFrame:
    """Add rolling realized volatility from log mid returns."""

    result = frame.copy()
    if "timestamp" not in result.columns or "mid" not in result.columns:
        return result
    indexed = result.copy()
    indexed["timestamp"] = pd.to_datetime(indexed["timestamp"], utc=True)
    indexed = indexed.set_index("timestamp")
    log_returns = np.log(pd.to_numeric(indexed["mid"], errors="coerce")).diff()
    for window in windows:
        result[f"realized_vol_{window}"] = np.sqrt(
            log_returns.pow(2).rolling(window).sum()
        ).to_numpy()
    return result
