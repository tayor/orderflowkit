"""Bulk volume classification."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm


def bulk_volume_classify(
    open_: pd.Series,
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    *,
    window: int = 20,
) -> pd.DataFrame:
    """Split bar volume into probabilistic buy and sell volume using BVC."""

    open_values = pd.to_numeric(open_, errors="coerce")
    high_values = pd.to_numeric(high, errors="coerce")
    low_values = pd.to_numeric(low, errors="coerce")
    close_values = pd.to_numeric(close, errors="coerce")
    volumes = pd.to_numeric(volume, errors="coerce").fillna(0.0)
    bar_return = (close_values - open_values) / open_values.replace(0, np.nan)
    intrabar_range = ((high_values - low_values) / open_values.replace(0, np.nan)).abs()
    sigma = intrabar_range.rolling(window=window, min_periods=1).std().replace(0, np.nan)
    probability_buy = pd.Series(norm.cdf((bar_return / sigma).fillna(0.0)), index=close.index)
    buy_volume = volumes * probability_buy
    sell_volume = volumes - buy_volume
    return pd.DataFrame(
        {
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "signed_volume": buy_volume - sell_volume,
            "buy_probability": probability_buy,
        },
        index=close.index,
    )
