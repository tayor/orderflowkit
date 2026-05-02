"""Time parsing and UTC normalization utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd


def utc_now() -> pd.Timestamp:
    """Return the current time as a timezone-aware UTC pandas timestamp."""

    return pd.Timestamp.now(tz="UTC")


def ensure_utc(value: Any) -> pd.Timestamp:
    """Convert a scalar timestamp-like value into a timezone-aware UTC timestamp."""

    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def parse_duration(value: str | int | float | pd.Timedelta | None) -> pd.Timedelta | None:
    """Parse duration strings such as ``"1h"`` or numeric seconds."""

    if value is None:
        return None
    if isinstance(value, pd.Timedelta):
        return value
    if isinstance(value, int | float):
        return pd.Timedelta(seconds=float(value))
    return pd.Timedelta(value)


def to_milliseconds(value: Any) -> int:
    """Convert a timestamp-like value to Unix milliseconds."""

    return int(ensure_utc(value).timestamp() * 1000)


def datetime_from_milliseconds(value: int | float) -> datetime:
    """Convert Unix milliseconds to a timezone-aware datetime."""

    return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc)
