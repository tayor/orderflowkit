from __future__ import annotations

import pandas as pd
from typer.testing import CliRunner

from orderflowkit.cli.main import app


def test_cli_metrics_bars(sample_bars: pd.DataFrame, tmp_path) -> None:  # type: ignore[no-untyped-def]
    input_path = tmp_path / "bars.parquet"
    output_path = tmp_path / "metrics.parquet"
    sample_bars.to_parquet(input_path, index=False)

    result = CliRunner().invoke(
        app, ["metrics", "bars", str(input_path), "--out", str(output_path)]
    )

    assert result.exit_code == 0, result.output
    assert output_path.exists()
    metrics = pd.read_parquet(output_path)
    assert "roll_spread_20" in metrics


def test_cli_features_and_labels(sample_l2_events: pd.DataFrame, tmp_path) -> None:  # type: ignore[no-untyped-def]
    events_path = tmp_path / "events.parquet"
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    sample_l2_events.to_parquet(events_path, index=False)

    runner = CliRunner()
    features_result = runner.invoke(
        app,
        [
            "features",
            "l2",
            str(events_path),
            "--levels",
            "1,2",
            "--windows",
            "1s",
            "--out",
            str(features_path),
        ],
    )
    labels_result = runner.invoke(
        app,
        [
            "labels",
            str(features_path),
            "--horizons",
            "1s",
            "--threshold-bps",
            "1",
            "--out",
            str(labels_path),
        ],
    )

    assert features_result.exit_code == 0, features_result.output
    assert labels_result.exit_code == 0, labels_result.output
    assert labels_path.exists()
