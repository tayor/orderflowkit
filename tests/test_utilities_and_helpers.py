from __future__ import annotations

import pandas as pd
import pytest

from orderflowkit.book import LocalBook
from orderflowkit.book.checksum import crc32_checksum
from orderflowkit.book.sync import has_sequence_gap
from orderflowkit.book.validators import has_both_sides, is_crossed
from orderflowkit.features import FeaturePipeline
from orderflowkit.feeders import AlphaVantageFeeder, FredFeeder, StooqFeeder
from orderflowkit.labels import liquidity_drop_event, spread_widening_event, volatility_burst_event
from orderflowkit.metrics.liquidity import depth_ratio, liquidity_percentile
from orderflowkit.metrics.order_flow.imbalance import imbalance_ratio
from orderflowkit.metrics.order_flow.ofi import order_flow_imbalance
from orderflowkit.metrics.order_flow.order_imbalance import calculate
from orderflowkit.metrics.spread import effective_spread
from orderflowkit.replay.sampler import take_every
from orderflowkit.schemas.books import BookSnapshot
from orderflowkit.utils.exceptions import DataValidationError, OptionalDependencyError
from orderflowkit.utils.resample import time_resample_last
from orderflowkit.utils.time import datetime_from_milliseconds, ensure_utc, parse_duration
from orderflowkit.utils.validators import require_columns, require_non_negative


def test_small_book_helpers() -> None:
    book = LocalBook("BTCUSDT")
    assert not has_both_sides(book)
    book.apply_snapshot([(100.0, 1.0)], [(101.0, 1.0)], update_id=1)

    assert has_both_sides(book)
    assert not is_crossed(book)
    assert crc32_checksum(["100", "1", "101", "2"]) > 0
    assert has_sequence_gap(last_update_id=1, first_update_id=3, update_id=3)
    assert not has_sequence_gap(last_update_id=1, first_update_id=2, update_id=2)


def test_liquidity_order_flow_and_spread_helpers(sample_l2_events: pd.DataFrame) -> None:
    ratio = depth_ratio(pd.Series([2.0, 4.0]), pd.Series([1.0, 2.0]))
    percentile = liquidity_percentile(pd.Series([1.0, 3.0, 2.0]), window=2)
    imbalance = imbalance_ratio(pd.Series([3.0]), pd.Series([1.0]))
    module_imbalance = calculate(pd.Series([3.0]), pd.Series([1.0]))
    spread = effective_spread(pd.Series([101.0]), pd.Series([100.0]))
    ofi = order_flow_imbalance(sample_l2_events, window="2s")

    assert ratio.tolist() == [2.0, 2.0]
    assert percentile.notna().all()
    assert imbalance.iloc[0] == 0.5
    assert module_imbalance.iloc[0] == 0.5
    assert spread.iloc[0] == 2.0
    assert ofi.notna().any()


def test_order_flow_imbalance_uses_level_size_deltas() -> None:
    events = pd.DataFrame(
        {
            "ts_local": pd.to_datetime(
                [
                    "2026-05-03T12:00:02Z",
                    "2026-05-03T12:00:00Z",
                    "2026-05-03T12:00:06Z",
                    "2026-05-03T12:00:04Z",
                ],
                utc=True,
            ),
            "exchange": "binance",
            "symbol": "BTCUSDT",
            "side": ["ask", "ask", "bid", "bid"],
            "price": [101.0, 101.0, 100.0, 100.0],
            "size": [4.0, 5.0, 0.0, 2.0],
        }
    )

    ofi = order_flow_imbalance(events, window="1s")

    assert ofi.index.is_monotonic_increasing
    assert ofi.tolist() == pytest.approx([-5.0, 1.0, 2.0, -2.0])


def test_labels_and_resampling_helpers() -> None:
    assert spread_widening_event(pd.Series([1.0, 6.0]), threshold_bps=5).tolist() == [0, 1]
    assert liquidity_drop_event(pd.Series([10.0, 3.0]), threshold_pct=50).tolist() == [0, 1]
    assert volatility_burst_event(pd.Series([1.0, 3.0]), percentile=90).tolist() == [1, 1]

    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z"]),
            "value": [1, 2],
        }
    )
    resampled = time_resample_last(frame, "1s")
    assert resampled["value"].tolist() == [1, 2]


def test_schema_and_feature_snapshot_helpers() -> None:
    book = LocalBook("BTCUSDT")
    book.apply_snapshot([(100.0, 2.0)], [(101.0, 1.0)], update_id=1)
    snapshots = pd.DataFrame(book.snapshot_rows(levels=1))
    features = FeaturePipeline(levels=[1], windows=["1s"]).from_book_snapshots(snapshots)
    snapshot = BookSnapshot(
        ts_local=pd.Timestamp("2026-05-03T12:00:00Z").to_pydatetime(),
        exchange="binance",
        symbol="BTCUSDT",
        level=1,
        valid=True,
        status="live",
    )

    assert features.loc[0, "imbalance_1"] == pytest.approx(1 / 3)
    assert snapshot.as_row()["level"] == 1


def test_time_and_validation_helpers() -> None:
    assert ensure_utc("2026-05-03").tzinfo is not None
    assert parse_duration("2s") == pd.Timedelta(seconds=2)
    assert datetime_from_milliseconds(1_777_808_000_000).tzinfo is not None

    with pytest.raises(DataValidationError):
        require_columns(pd.DataFrame({"a": [1]}), ["missing"])
    with pytest.raises(DataValidationError):
        require_non_negative(pd.Series([1, -1]), name="x")


def test_placeholder_feeders_raise_clear_errors() -> None:
    for feeder in [AlphaVantageFeeder(), StooqFeeder(), FredFeeder()]:
        with pytest.raises(OptionalDependencyError):
            feeder.fetch("SPY", "2026-01-01", "2026-01-02")


def test_sampler_helper() -> None:
    assert take_every([1, 2, 3, 4, 5], 2) == [1, 3, 5]
