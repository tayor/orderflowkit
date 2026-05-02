"""Order-book charts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from orderflowkit.utils.exceptions import OptionalDependencyError


def plot_orderbook_depth(frame_or_path: pd.DataFrame | str | Path) -> object:
    """Plot bid and ask depth by price for a book snapshot."""

    try:
        import plotly.graph_objects as go
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise OptionalDependencyError("Install OrderFlowKit[viz] to use plotting") from exc
    frame = (
        pd.read_parquet(frame_or_path) if isinstance(frame_or_path, str | Path) else frame_or_path
    )
    latest_ts = frame["ts_local"].max()
    latest = frame[frame["ts_local"] == latest_ts]
    figure = go.Figure()
    figure.add_bar(x=latest["bid_price"], y=latest["bid_size"], name="Bid depth")
    figure.add_bar(x=latest["ask_price"], y=latest["ask_size"], name="Ask depth")
    figure.update_layout(
        title="Order-book depth", xaxis_title="Price", yaxis_title="Size", barmode="overlay"
    )
    return figure
