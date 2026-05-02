"""Realized volatility."""

from __future__ import annotations

import numpy as np
import pandas as pd


def realized_vol(close: pd.Series, window: int = 20) -> pd.Series:
    """Compute rolling realized volatility from log returns."""

    prices = pd.to_numeric(close, errors="coerce").replace(0, np.nan)
    log_returns = np.log(prices).diff()
    result = np.sqrt(log_returns.pow(2).rolling(window=window, min_periods=window).sum())
    return pd.Series(result, index=close.index, name="realized_vol")
