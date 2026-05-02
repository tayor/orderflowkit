"""VWAP and VWAP deviation."""

from __future__ import annotations

import numpy as np
import pandas as pd


def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Compute cumulative volume-weighted average price from typical price."""

    typical_price = (
        pd.to_numeric(high, errors="coerce")
        + pd.to_numeric(low, errors="coerce")
        + pd.to_numeric(close, errors="coerce")
    ) / 3.0
    volumes = pd.to_numeric(volume, errors="coerce").fillna(0.0)
    cumulative_volume = volumes.cumsum().replace(0, np.nan)
    result = (typical_price * volumes).cumsum() / cumulative_volume
    return pd.Series(result, index=close.index, name="vwap")


def vwap_deviation(close: pd.Series, vwap_values: pd.Series) -> pd.Series:
    """Return percentage deviation of close from VWAP."""

    prices = pd.to_numeric(close, errors="coerce")
    vwap_series = pd.to_numeric(vwap_values, errors="coerce").replace(0, np.nan)
    deviation = (prices - vwap_series) / vwap_series
    return pd.Series(
        deviation.replace([np.inf, -np.inf], np.nan), index=close.index, name="vwap_deviation"
    )
