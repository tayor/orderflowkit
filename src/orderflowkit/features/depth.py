"""Depth feature helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_depth_features(frame: pd.DataFrame, levels: list[int]) -> pd.DataFrame:
    """Add depth ratios for available top-N depth columns."""

    result = frame.copy()
    for level in levels:
        bid = f"bid_depth_{level}"
        ask = f"ask_depth_{level}"
        if bid in result.columns and ask in result.columns:
            denominator = pd.to_numeric(result[ask], errors="coerce").replace(0, np.nan)
            result[f"depth_ratio_{level}"] = (
                pd.to_numeric(result[bid], errors="coerce") / denominator
            )
    return result
