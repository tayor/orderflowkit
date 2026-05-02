"""Typer CLI for OrderFlowKit."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, cast

import pandas as pd
import typer
from rich.console import Console

from orderflowkit import MicrostructurePipeline
from orderflowkit.features import FeaturePipeline
from orderflowkit.feeders import BinanceRestFeeder, YFinanceFeeder
from orderflowkit.labels import Labeler
from orderflowkit.replay import Replay
from orderflowkit.viz import plot_microstructure_dashboard

app = typer.Typer(help="Free-data microstructure analytics and L2 book replay.")
fetch_app = typer.Typer(help="Fetch public market data.")
metrics_app = typer.Typer(help="Compute microstructure metrics.")
features_app = typer.Typer(help="Build feature tables.")
app.add_typer(fetch_app, name="fetch")
app.add_typer(metrics_app, name="metrics")
app.add_typer(features_app, name="features")
console = Console()


@fetch_app.command("bars")
def fetch_bars(
    symbol: str,
    source: Annotated[str, typer.Option(help="Data source: yfinance or binance")] = "yfinance",
    start: Annotated[str, typer.Option(help="Start date or timestamp")] = "2024-01-01",
    end: Annotated[str, typer.Option(help="End date or timestamp")] = "2024-12-31",
    interval: Annotated[str, typer.Option(help="Bar interval")] = "1d",
    out: Annotated[Path, typer.Option(help="Output Parquet path")] = Path("bars.parquet"),
) -> None:
    """Fetch OHLCV bars and write Parquet."""

    feeder = YFinanceFeeder() if source == "yfinance" else BinanceRestFeeder()
    bars = feeder.fetch(symbol=symbol, start=start, end=end, interval=interval)
    out.parent.mkdir(parents=True, exist_ok=True)
    bars.to_parquet(out, index=False)
    console.print(f"Wrote {len(bars)} bars to {out}")


@metrics_app.command("bars")
def metrics_bars(
    path: Path,
    preset: Annotated[str, typer.Option(help="Metric preset")] = "academic",
    out: Annotated[Path, typer.Option(help="Output Parquet path")] = Path("metrics.parquet"),
) -> None:
    """Compute bar-based metrics."""

    bars = pd.read_parquet(path)
    pipeline = MicrostructurePipeline(bars)
    if preset == "academic":
        pipeline.add_academic_preset()
    else:
        raise typer.BadParameter(f"Unknown preset: {preset}")
    result = pipeline.run().metrics
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(out, index=False)
    console.print(f"Wrote metrics to {out}")


@features_app.command("l2")
def features_l2(
    path: Path,
    levels: Annotated[str, typer.Option(help="Comma-separated depth levels")] = "1,5,10",
    windows: Annotated[str, typer.Option(help="Comma-separated rolling windows")] = "1s,5s",
    out: Annotated[Path, typer.Option(help="Output Parquet path")] = Path("features.parquet"),
) -> None:
    """Build L2 features from normalized events."""

    pipeline = FeaturePipeline(
        levels=[int(value) for value in levels.split(",")], windows=windows.split(",")
    )
    features = pipeline.from_l2_events(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(out, index=False)
    console.print(f"Wrote {len(features)} feature rows to {out}")


@app.command("labels")
def labels_command(
    path: Path,
    horizons: Annotated[str, typer.Option(help="Comma-separated horizons")] = "1s,5s,30s",
    threshold_bps: Annotated[float, typer.Option(help="Classification threshold in bps")] = 2.0,
    out: Annotated[Path, typer.Option(help="Output Parquet path")] = Path("dataset.parquet"),
) -> None:
    """Generate ML labels from features."""

    features = pd.read_parquet(path)
    dataset = Labeler(horizons=horizons.split(","), thresholds_bps=[threshold_bps]).apply(features)
    out.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_parquet(out, index=False)
    console.print(f"Wrote labeled dataset to {out}")


@app.command("replay")
def replay_command(
    path: Path,
    speed: Annotated[
        str, typer.Option(help="Replay speed: max, 10x, or a numeric multiplier")
    ] = "max",
) -> None:
    """Replay a normalized L2 event file."""

    states = Replay(path).books(speed=speed)
    for state in states[-5:]:
        console.print(
            {
                "ts": str(state.ts),
                "mid": state.mid,
                "spread_bps": state.spread_bps,
                "status": state.status,
            }
        )


@app.command("plot")
def plot_command(
    path: Path,
    out: Annotated[Path, typer.Option(help="Output HTML path")] = Path("dashboard.html"),
) -> None:
    """Write a Plotly microstructure dashboard."""

    figure = cast(Any, plot_microstructure_dashboard(path))
    out.parent.mkdir(parents=True, exist_ok=True)
    figure.write_html(out)
    console.print(f"Wrote dashboard to {out}")


@app.command("validate")
def validate_command(path: Path) -> None:
    """Validate that a recording directory contains expected outputs."""

    required = ["raw", "normalized", "books", "reports"]
    missing = [name for name in required if not (path / name).exists()]
    if missing:
        raise typer.BadParameter(f"Missing recording folders: {', '.join(missing)}")
    console.print(f"Recording directory looks complete: {path}")


if __name__ == "__main__":
    app()
