from __future__ import annotations

import numpy as np
import pandas as pd

from orderflowkit.features import FeaturePipeline
from orderflowkit.labels import Labeler, future_return_mid, up_down_flat
from orderflowkit.replay import Replay


def test_feature_pipeline_from_l2_events(sample_l2_events: pd.DataFrame, tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "events.parquet"
    sample_l2_events.to_parquet(path, index=False)

    features = FeaturePipeline(levels=[1, 2], windows=["1s", "2s"]).from_l2_events(path)

    assert not features.empty
    assert {
        "mid",
        "spread_bps",
        "imbalance_1",
        "bid_depth_2",
        "ask_depth_2",
        "realized_vol_1s",
    }.issubset(features.columns)
    assert features["timestamp"].is_monotonic_increasing


def test_labeler_generates_future_returns_and_classes(
    sample_l2_events: pd.DataFrame, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    features = FeaturePipeline(levels=[1], windows=["1s"]).from_l2_events(sample_l2_events)
    labels = Labeler(horizons=["1s"], thresholds_bps=[1]).apply(features)

    assert "future_return_mid_1s" in labels
    assert "label_udf_1s_1bps" in labels
    assert set(labels["label_udf_1s_1bps"].unique()).issubset({-1, 0, 1})
    assert future_return_mid(features, horizon="1s").notna().any()
    assert up_down_flat(pd.Series([-0.01, 0.0, 0.01]), threshold_bps=1).tolist() == [-1, 0, 1]


def test_future_return_mid_preserves_original_row_alignment() -> None:
    features = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-05-03T12:00:02Z",
                    "2026-05-03T12:00:00Z",
                    "2026-05-03T12:00:01Z",
                ],
                utc=True,
            ),
            "mid": [102.0, 100.0, 101.0],
        }
    )

    returns = future_return_mid(features, horizon="1s")

    assert pd.isna(returns.iloc[0])
    assert np.isclose(returns.iloc[1], np.log(101.0 / 100.0))
    assert np.isclose(returns.iloc[2], np.log(102.0 / 101.0))


def test_replay_reconstructs_book_states(sample_l2_events: pd.DataFrame, tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "events.parquet"
    sample_l2_events.to_parquet(path, index=False)

    states = Replay(path).books(speed="max")

    assert len(states) == len(sample_l2_events)
    assert states[-1].mid is not None
    assert states[-1].imbalance(2) is not None
