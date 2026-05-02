"""Order-flow imbalance helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def imbalance_ratio(buy_volume: pd.Series, sell_volume: pd.Series) -> pd.Series:
    """Return normalized buy/sell volume imbalance."""

    buy = pd.to_numeric(buy_volume, errors="coerce").fillna(0.0)
    sell = pd.to_numeric(sell_volume, errors="coerce").fillna(0.0)
    denominator = (buy + sell).replace(0, np.nan)
    result = (buy - sell) / denominator
    return pd.Series(
        result.replace([np.inf, -np.inf], np.nan), index=buy_volume.index, name="order_imbalance"
    )


def from_signed_volume(signed_volume: pd.Series, window: int | None = None) -> pd.Series:
    """Compute normalized imbalance from signed volume."""

    signed = pd.to_numeric(signed_volume, errors="coerce").fillna(0.0)
    numerator = (
        signed.rolling(window, min_periods=1).sum() if window is not None else signed.cumsum()
    )
    denominator_source = signed.abs()
    denominator = (
        denominator_source.rolling(window, min_periods=1).sum()
        if window is not None
        else denominator_source.cumsum()
    ).replace(0, np.nan)
    result = numerator / denominator
    return pd.Series(
        result.replace([np.inf, -np.inf], np.nan).fillna(0.0),
        index=signed_volume.index,
        name="order_imbalance",
    )
