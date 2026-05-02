"""Liquidity event labels."""

from __future__ import annotations

import pandas as pd


def spread_widening_event(spread_bps: pd.Series, *, threshold_bps: float = 5.0) -> pd.Series:
    """Flag spread values above a basis-point threshold."""

    return (pd.to_numeric(spread_bps, errors="coerce") >= threshold_bps).astype("int8")


def liquidity_drop_event(depth: pd.Series, *, threshold_pct: float = 50.0) -> pd.Series:
    """Flag depth values that fall below a percentage of their expanding median."""

    numeric = pd.to_numeric(depth, errors="coerce")
    baseline = numeric.expanding(min_periods=1).median()
    return (numeric <= baseline * (threshold_pct / 100.0)).astype("int8")


def volatility_burst_event(volatility: pd.Series, *, percentile: float = 95.0) -> pd.Series:
    """Flag volatility values above an expanding percentile threshold."""

    numeric = pd.to_numeric(volatility, errors="coerce")
    threshold = numeric.expanding(min_periods=1).quantile(percentile / 100.0)
    return (numeric >= threshold).astype("int8")
