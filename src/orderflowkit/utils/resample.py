"""Small pandas resampling helpers."""

from __future__ import annotations

import pandas as pd

from orderflowkit.utils.validators import require_columns


def time_resample_last(
    frame: pd.DataFrame, interval: str, *, timestamp: str = "timestamp"
) -> pd.DataFrame:
    """Resample a timestamped frame using the last observation in each interval."""

    require_columns(frame, [timestamp])
    indexed = frame.copy()
    indexed[timestamp] = pd.to_datetime(indexed[timestamp], utc=True)
    return indexed.set_index(timestamp).resample(interval).last().dropna(how="all").reset_index()
