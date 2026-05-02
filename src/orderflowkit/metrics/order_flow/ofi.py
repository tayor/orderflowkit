"""Order-flow imbalance from L2 events."""

from __future__ import annotations

import numpy as np
import pandas as pd

from orderflowkit.utils.validators import require_columns


def order_flow_imbalance(book_events: pd.DataFrame, window: str = "1s") -> pd.Series:
    """Compute signed size changes from normalized L2 book events over a time window."""

    require_columns(book_events, ["ts_local", "side", "price", "size"])
    frame = book_events.copy()
    frame["ts_local"] = pd.to_datetime(frame["ts_local"], utc=True)
    frame["_event_order"] = np.arange(len(frame))
    frame = frame.sort_values(["ts_local", "_event_order"])
    frame["price"] = pd.to_numeric(frame["price"], errors="coerce")
    frame["size"] = pd.to_numeric(frame["size"], errors="coerce").fillna(0.0)
    group_keys = [column for column in ("exchange", "symbol") if column in frame.columns]
    group_keys.extend(["side", "price"])
    previous_size = frame.groupby(group_keys, sort=False)["size"].shift().fillna(0.0)
    side_sign = frame["side"].str.lower().map({"bid": 1.0, "ask": -1.0}).fillna(0.0)
    frame["signed_size_delta"] = side_sign * (frame["size"] - previous_size)
    result = frame.set_index("ts_local")["signed_size_delta"].rolling(window).sum()
    return pd.Series(result, name=f"ofi_{window}")
