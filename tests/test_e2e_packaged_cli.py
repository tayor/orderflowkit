from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run_command(
    command: list[str], *, cwd: Path = ROOT, timeout: int = 180
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _venv_executable(venv_dir: Path, name: str) -> Path:
    scripts_dir = "Scripts" if sys.platform.startswith("win") else "bin"
    suffix = ".exe" if sys.platform.startswith("win") else ""
    return venv_dir / scripts_dir / f"{name}{suffix}"


@pytest.mark.e2e()
def test_packaged_cli_workflow_end_to_end(
    sample_bars: pd.DataFrame, sample_l2_events: pd.DataFrame, tmp_path: Path
) -> None:
    uv_path = shutil.which("uv")
    if uv_path is None:
        pytest.skip("uv is required for packaged end-to-end validation")

    dist_dir = tmp_path / "dist"
    _run_command([sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir)])

    wheels = sorted(dist_dir.glob("orderflowkit-*.whl"))
    assert len(wheels) == 1
    wheel_path = wheels[0]

    venv_dir = tmp_path / "package-smoke-venv"
    _run_command([uv_path, "venv", "--python", sys.executable, str(venv_dir)])
    python_path = _venv_executable(venv_dir, "python")
    cli_path = _venv_executable(venv_dir, "ofk")
    _run_command([uv_path, "pip", "install", "--python", str(python_path), str(wheel_path)])

    bars_path = tmp_path / "bars.parquet"
    events_path = tmp_path / "events.parquet"
    metrics_path = tmp_path / "metrics.parquet"
    features_path = tmp_path / "features.parquet"
    labels_path = tmp_path / "labels.parquet"
    recording_dir = tmp_path / "recording"
    sample_bars.to_parquet(bars_path, index=False)
    sample_l2_events.to_parquet(events_path, index=False)
    for name in ["raw", "normalized", "books", "reports"]:
        (recording_dir / name).mkdir(parents=True, exist_ok=True)

    _run_command([str(cli_path), "metrics", "bars", str(bars_path), "--out", str(metrics_path)])
    _run_command(
        [
            str(cli_path),
            "features",
            "l2",
            str(events_path),
            "--levels",
            "1,2",
            "--windows",
            "1s",
            "--out",
            str(features_path),
        ]
    )
    _run_command(
        [
            str(cli_path),
            "labels",
            str(features_path),
            "--horizons",
            "1s",
            "--threshold-bps",
            "1",
            "--out",
            str(labels_path),
        ]
    )

    replay_result = _run_command([str(cli_path), "replay", str(events_path), "--speed", "max"])
    validate_result = _run_command([str(cli_path), "validate", str(recording_dir)])
    import_command = (
        "import orderflowkit; "
        "from orderflowkit import MicrostructurePipeline; "
        "print(orderflowkit.__version__, MicrostructurePipeline.__name__)"
    )
    import_result = _run_command(
        [
            str(python_path),
            "-c",
            import_command,
        ]
    )

    metrics = pd.read_parquet(metrics_path)
    features = pd.read_parquet(features_path)
    labels = pd.read_parquet(labels_path)

    assert "roll_spread_20" in metrics.columns
    assert {"mid", "spread_bps", "imbalance_1"}.issubset(features.columns)
    assert {"future_return_mid_1s", "label_udf_1s_1bps"}.issubset(labels.columns)
    assert labels["label_udf_1s_1bps"].isin([-1, 0, 1]).all()
    assert "status" in replay_result.stdout
    assert "looks complete" in validate_result.stdout
    assert "0.1.0 MicrostructurePipeline" in import_result.stdout
