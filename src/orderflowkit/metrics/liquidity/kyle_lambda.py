"""Kyle lambda proxy."""

from __future__ import annotations

import numpy as np
import pandas as pd


def kyle_lambda(close: pd.Series, volume: pd.Series, window: int = 20) -> pd.Series:
    """Estimate price impact as absolute price changes per unit volume."""

    prices = pd.to_numeric(close, errors="coerce")
    volumes = pd.to_numeric(volume, errors="coerce").replace(0, np.nan)
    impact = prices.diff().abs() / volumes
    result = impact.rolling(window=window, min_periods=window).mean()
    return pd.Series(
        result.replace([np.inf, -np.inf], np.nan), index=close.index, name="kyle_lambda"
    )
