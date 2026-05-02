"""DataFrame validation helpers."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from orderflowkit.utils.exceptions import DataValidationError


def require_columns(frame: pd.DataFrame, columns: Iterable[str], *, name: str = "data") -> None:
    """Raise a validation error when a DataFrame is missing required columns."""

    missing = [column for column in columns if column not in frame.columns]
    if missing:
        joined = ", ".join(missing)
        raise DataValidationError(f"{name} is missing required columns: {joined}")


def require_non_negative(series: pd.Series, *, name: str) -> None:
    """Raise when a numeric series contains negative values."""

    if (series.dropna() < 0).any():
        raise DataValidationError(f"{name} must not contain negative values")


def ensure_sorted_by_time(frame: pd.DataFrame, column: str = "timestamp") -> pd.DataFrame:
    """Return a copy sorted by a timestamp column."""

    require_columns(frame, [column])
    return frame.sort_values(column).reset_index(drop=True)
