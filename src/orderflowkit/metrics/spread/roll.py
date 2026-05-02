"""Roll effective-spread estimator."""

from __future__ import annotations

import numpy as np
import pandas as pd


def roll_spread(close: pd.Series, window: int = 20) -> pd.Series:
    """Estimate effective spread from negative serial covariance of price changes."""

    prices = pd.to_numeric(close, errors="coerce")
    changes = prices.diff()
    covariance = changes.rolling(window=window, min_periods=window).cov(changes.shift(1))
    spread = 2.0 * np.sqrt((-covariance).clip(lower=0.0))
    return pd.Series(spread, index=close.index, name="roll_spread")
