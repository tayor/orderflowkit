"""User-facing order imbalance module."""

from __future__ import annotations

import pandas as pd

from orderflowkit.metrics.order_flow.imbalance import from_signed_volume, imbalance_ratio


def calculate(buy_volume: pd.Series, sell_volume: pd.Series) -> pd.Series:
    """Return normalized buy/sell volume imbalance."""

    return imbalance_ratio(buy_volume, sell_volume)


__all__ = ["calculate", "from_signed_volume", "imbalance_ratio"]
