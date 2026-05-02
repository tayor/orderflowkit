"""Tick-rule trade signing."""

from __future__ import annotations

import numpy as np
import pandas as pd


def tick_rule(price: pd.Series) -> pd.Series:
    """Classify trades as buyer- or seller-initiated from price changes."""

    prices = pd.to_numeric(price, errors="coerce")
    raw = np.sign(prices.diff()).replace(0, np.nan)
    signs = raw.ffill().fillna(0).astype("int8")
    return pd.Series(signs, index=price.index, name="tick_sign")
