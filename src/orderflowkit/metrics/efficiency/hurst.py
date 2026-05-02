"""Hurst exponent estimators."""

from __future__ import annotations

import numpy as np
import pandas as pd


def hurst_exponent(close: pd.Series, min_lag: int = 2, max_lag: int = 100) -> float:
    """Estimate the Hurst exponent using log-log lagged-difference scaling."""

    prices = pd.to_numeric(close, errors="coerce").dropna().to_numpy(dtype=float)
    if len(prices) < max_lag + 2:
        max_lag = max(min_lag + 1, len(prices) // 2)
    lags = range(min_lag, max_lag)
    tau = [
        np.sqrt(np.std(prices[lag:] - prices[:-lag]))
        for lag in lags
        if len(prices[lag:] - prices[:-lag]) > 1
    ]
    valid_lags = np.array(
        [lag for lag, value in zip(lags, tau, strict=False) if value > 0], dtype=float
    )
    valid_tau = np.array([value for value in tau if value > 0], dtype=float)
    if len(valid_lags) < 2:
        return float("nan")
    slope, _ = np.polyfit(np.log(valid_lags), np.log(valid_tau), 1)
    return float(slope * 2.0)


def rolling_hurst(
    close: pd.Series, window: int = 252, min_lag: int = 2, max_lag: int = 100
) -> pd.Series:
    """Compute a rolling Hurst exponent."""

    def calculate(values: np.ndarray) -> float:
        return hurst_exponent(pd.Series(values), min_lag=min_lag, max_lag=max_lag)

    prices = pd.to_numeric(close, errors="coerce")
    result = prices.rolling(window=window, min_periods=window).apply(calculate, raw=True)
    return pd.Series(result, index=close.index, name="hurst")
