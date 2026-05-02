"""Corwin-Schultz high-low spread estimator."""

from __future__ import annotations

import numpy as np
import pandas as pd


def corwin_schultz_spread(high: pd.Series, low: pd.Series) -> pd.Series:
    """Estimate bid-ask spread from adjacent high-low ranges."""

    high_values = pd.to_numeric(high, errors="coerce")
    low_values = pd.to_numeric(low, errors="coerce").replace(0, np.nan)
    log_hl = (high_values / low_values).apply(np.log)
    beta = log_hl.pow(2) + log_hl.shift(1).pow(2)
    two_day_high = high_values.rolling(2, min_periods=2).max()
    two_day_low = low_values.rolling(2, min_periods=2).min()
    gamma = (two_day_high / two_day_low).apply(np.log).pow(2)
    denominator = 3.0 - 2.0 * np.sqrt(2.0)
    alpha = ((np.sqrt(2.0 * beta) - np.sqrt(beta)) / denominator) - np.sqrt(gamma / denominator)
    alpha = alpha.clip(lower=0.0)
    spread = 2.0 * (np.exp(alpha) - 1.0) / (1.0 + np.exp(alpha))
    return pd.Series(
        spread.replace([np.inf, -np.inf], np.nan), index=high.index, name="corwin_schultz_spread"
    )
