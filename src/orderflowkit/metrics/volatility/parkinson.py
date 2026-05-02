"""Parkinson volatility estimator."""

from __future__ import annotations

import numpy as np
import pandas as pd


def parkinson_vol(high: pd.Series, low: pd.Series, window: int = 20) -> pd.Series:
    """Estimate volatility from high-low ranges."""

    high_values = pd.to_numeric(high, errors="coerce")
    low_values = pd.to_numeric(low, errors="coerce").replace(0, np.nan)
    variance = (high_values / low_values).apply(np.log).pow(2) / (4.0 * np.log(2.0))
    result = np.sqrt(variance.rolling(window=window, min_periods=window).mean())
    return pd.Series(result, index=high.index, name="parkinson_vol")
