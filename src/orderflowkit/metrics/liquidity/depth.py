"""Depth-derived liquidity helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def depth_ratio(bid_depth: pd.Series, ask_depth: pd.Series) -> pd.Series:
    """Return bid depth divided by ask depth."""

    bid = pd.to_numeric(bid_depth, errors="coerce")
    ask = pd.to_numeric(ask_depth, errors="coerce").replace(0, np.nan)
    return pd.Series(
        (bid / ask).replace([np.inf, -np.inf], np.nan), index=bid_depth.index, name="depth_ratio"
    )


def liquidity_percentile(values: pd.Series, window: int = 252) -> pd.Series:
    """Rolling percentile rank where higher values are more liquid."""

    numeric = pd.to_numeric(values, errors="coerce")
    return numeric.rolling(window=window, min_periods=1).rank(pct=True)
