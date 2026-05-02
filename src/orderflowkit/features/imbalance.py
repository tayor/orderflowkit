"""Imbalance feature helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_imbalance_features(frame: pd.DataFrame, levels: list[int]) -> pd.DataFrame:
    """Add imbalance columns from bid and ask depth columns."""

    result = frame.copy()
    for level in levels:
        bid = f"bid_depth_{level}"
        ask = f"ask_depth_{level}"
        if bid in result.columns and ask in result.columns:
            bid_values = pd.to_numeric(result[bid], errors="coerce").fillna(0.0)
            ask_values = pd.to_numeric(result[ask], errors="coerce").fillna(0.0)
            denominator = (bid_values + ask_values).replace(0, np.nan)
            result[f"imbalance_{level}"] = (bid_values - ask_values) / denominator
    return result
