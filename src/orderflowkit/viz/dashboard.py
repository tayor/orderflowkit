"""Microstructure dashboard charts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from orderflowkit.utils.exceptions import OptionalDependencyError


def plot_microstructure_dashboard(frame_or_path: pd.DataFrame | str | Path) -> object:
    """Create a compact Plotly dashboard from a feature table."""

    try:
        from plotly.subplots import make_subplots
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise OptionalDependencyError("Install OrderFlowKit[viz] to use plotting") from exc
    frame = (
        pd.read_parquet(frame_or_path) if isinstance(frame_or_path, str | Path) else frame_or_path
    )
    figure = make_subplots(
        rows=3, cols=1, shared_xaxes=True, subplot_titles=("Mid", "Spread bps", "Imbalance")
    )
    figure.add_scatter(x=frame["timestamp"], y=frame["mid"], name="Mid", row=1, col=1)
    if "spread_bps" in frame:
        figure.add_scatter(
            x=frame["timestamp"], y=frame["spread_bps"], name="Spread bps", row=2, col=1
        )
    imbalance_columns = [column for column in frame.columns if column.startswith("imbalance_")]
    if imbalance_columns:
        figure.add_scatter(
            x=frame["timestamp"],
            y=frame[imbalance_columns[0]],
            name=imbalance_columns[0],
            row=3,
            col=1,
        )
    figure.update_layout(height=800, title="Microstructure dashboard")
    return figure
