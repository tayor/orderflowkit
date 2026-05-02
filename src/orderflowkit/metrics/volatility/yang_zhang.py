"""Yang-Zhang volatility estimator."""

from __future__ import annotations

import numpy as np
import pandas as pd


def yang_zhang_vol(
    open_: pd.Series,
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 20,
) -> pd.Series:
    """Estimate volatility with overnight, open-close, and Rogers-Satchell components."""

    open_values = pd.to_numeric(open_, errors="coerce").replace(0, np.nan)
    high_values = pd.to_numeric(high, errors="coerce")
    low_values = pd.to_numeric(low, errors="coerce").replace(0, np.nan)
    close_values = pd.to_numeric(close, errors="coerce").replace(0, np.nan)
    overnight = (open_values / close_values.shift(1)).apply(np.log)
    open_close = (close_values / open_values).apply(np.log)
    rs = (high_values / close_values).apply(np.log) * (high_values / open_values).apply(np.log) + (
        low_values / close_values
    ).apply(np.log) * (low_values / open_values).apply(np.log)
    k = 0.34 / (1.34 + (window + 1.0) / (window - 1.0))
    variance = (
        overnight.rolling(window).var()
        + k * open_close.rolling(window).var()
        + (1.0 - k) * rs.rolling(window).mean()
    )
    result = np.sqrt(variance.clip(lower=0.0))
    return pd.Series(result, index=close.index, name="yang_zhang_vol")
