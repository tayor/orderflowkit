"""Amihud illiquidity."""

from __future__ import annotations

import numpy as np
import pandas as pd


def amihud_illiquidity(close: pd.Series, volume: pd.Series, window: int = 20) -> pd.Series:
    """Compute rolling Amihud illiquidity using absolute returns per dollar volume."""

    prices = pd.to_numeric(close, errors="coerce")
    volumes = pd.to_numeric(volume, errors="coerce")
    returns = prices.pct_change().abs()
    dollar_volume = (prices * volumes).replace(0, np.nan)
    ratio = returns / dollar_volume
    illiquidity = ratio.rolling(window=window, min_periods=window).mean()
    return pd.Series(
        illiquidity.replace([np.inf, -np.inf], np.nan), index=close.index, name="amihud_illiquidity"
    )
