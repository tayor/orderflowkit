"""Simple high-low spread proxy."""

from __future__ import annotations

import numpy as np
import pandas as pd


def high_low_spread(high: pd.Series, low: pd.Series, close: pd.Series | None = None) -> pd.Series:
    """Estimate spread as the high-low range scaled by a reference price."""

    high_values = pd.to_numeric(high, errors="coerce")
    low_values = pd.to_numeric(low, errors="coerce")
    if close is None:
        reference = (high_values + low_values) / 2.0
    else:
        reference = pd.to_numeric(close, errors="coerce")
    spread = (high_values - low_values).clip(lower=0.0) / reference.replace(0, np.nan)
    return pd.Series(
        spread.replace([np.inf, -np.inf], np.nan), index=high.index, name="high_low_spread"
    )
