"""Classification labels."""

from __future__ import annotations

import numpy as np
import pandas as pd


def up_down_flat(returns: pd.Series, *, threshold_bps: float = 2.0) -> pd.Series:
    """Classify future returns as down, flat, or up."""

    threshold = threshold_bps / 10_000.0
    numeric = pd.to_numeric(returns, errors="coerce")
    labels = np.where(numeric > threshold, 1, np.where(numeric < -threshold, -1, 0))
    return pd.Series(labels, index=returns.index, name=f"up_down_flat_{threshold_bps:g}bps").astype(
        "int8"
    )
