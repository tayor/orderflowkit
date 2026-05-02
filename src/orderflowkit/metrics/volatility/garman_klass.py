"""Garman-Klass volatility estimator."""

from __future__ import annotations

import numpy as np
import pandas as pd


def garman_klass_vol(
    open_: pd.Series,
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 20,
) -> pd.Series:
    """Estimate volatility using OHLC prices."""

    open_values = pd.to_numeric(open_, errors="coerce").replace(0, np.nan)
    high_values = pd.to_numeric(high, errors="coerce")
    low_values = pd.to_numeric(low, errors="coerce").replace(0, np.nan)
    close_values = pd.to_numeric(close, errors="coerce")
    log_high_low = (high_values / low_values).apply(np.log)
    log_close_open = (close_values / open_values).apply(np.log)
    variance = 0.5 * log_high_low.pow(2) - (2.0 * np.log(2.0) - 1.0) * log_close_open.pow(2)
    result = np.sqrt(variance.clip(lower=0.0).rolling(window=window, min_periods=window).mean())
    return pd.Series(result, index=close.index, name="garman_klass_vol")
