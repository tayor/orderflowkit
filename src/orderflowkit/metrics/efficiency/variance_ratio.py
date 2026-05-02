"""Variance-ratio tests."""

from __future__ import annotations

import numpy as np
import pandas as pd


def variance_ratio(close: pd.Series, lag: int = 5) -> dict[str, float]:
    """Return the Lo-MacKinlay-style variance ratio for one lag."""

    prices = pd.to_numeric(close, errors="coerce").replace(0, np.nan)
    returns = np.log(prices).diff().dropna()
    if len(returns) <= lag:
        return {
            "variance_ratio": float("nan"),
            "lag": float(lag),
            "observations": float(len(returns)),
        }
    one_period_var = returns.var(ddof=1)
    lagged_var = returns.rolling(lag).sum().dropna().var(ddof=1)
    ratio = lagged_var / (lag * one_period_var) if one_period_var > 0 else np.nan
    return {"variance_ratio": float(ratio), "lag": float(lag), "observations": float(len(returns))}


def rolling_variance_ratio(close: pd.Series, lag: int = 5, window: int = 120) -> pd.Series:
    """Compute a rolling variance ratio."""

    def calculate(values: np.ndarray) -> float:
        return variance_ratio(pd.Series(values), lag=lag)["variance_ratio"]

    prices = pd.to_numeric(close, errors="coerce")
    result = prices.rolling(window=window, min_periods=window).apply(calculate, raw=True)
    return pd.Series(result, index=close.index, name="variance_ratio")
