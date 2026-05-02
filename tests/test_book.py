from __future__ import annotations

import pandas as pd

from orderflowkit.book import BookStatus, LocalBook, Side


def test_local_book_applies_snapshot_update_and_delete() -> None:
    book = LocalBook("BTCUSDT", depth=3)
    book.apply_snapshot(
        bids=[(100.0, 2.0), (99.5, 1.0)], asks=[(100.5, 1.5), (101.0, 3.0)], update_id=1
    )

    assert book.valid
    assert book.best_bid == 100.0
    assert book.best_ask == 100.5
    assert book.mid == 100.25
    assert book.spread_bps is not None

    book.apply_delta(Side.BID, 100.0, 3.0, update_id=2)
    assert book.bids[100.0] == 3.0

    book.apply_delta("ask", 100.5, 0.0, update_id=3)
    assert book.best_ask == 101.0

    rows = book.snapshot_rows(levels=2)
    assert len(rows) == 2
    assert rows[0]["valid"] is True


def test_local_book_detects_sequence_gap() -> None:
    book = LocalBook("BTCUSDT")
    book.apply_snapshot([(100.0, 1.0)], [(101.0, 1.0)], update_id=10)
    book.apply_delta("bid", 100.5, 1.0, update_id=12)

    assert book.sequence_gaps == 1
    assert book.status == BookStatus.OUT_OF_SYNC
    assert not book.valid


def test_local_book_detects_crossed_and_stale_conditions() -> None:
    timestamp = pd.Timestamp("2026-05-03T12:00:00Z")
    book = LocalBook("BTCUSDT", stale_after=pd.Timedelta(seconds=5))
    book.apply_snapshot([(101.0, 1.0)], [(100.0, 1.0)], update_id=1, ts_local=timestamp)

    assert book.status == BookStatus.CROSSED
    assert book.is_crossed()
    assert book.is_stale(now=timestamp + pd.Timedelta(seconds=10))

    healthy = LocalBook("BTCUSDT")
    healthy.apply_snapshot([(100.0, 1.0)], [(101.0, 1.0)], update_id=1, ts_local=timestamp)
    assert healthy.valid


def test_book_metrics_are_bounded() -> None:
    book = LocalBook("BTCUSDT")
    book.apply_snapshot([(100.0, 2.0), (99.0, 1.0)], [(101.0, 1.0), (102.0, 2.0)], update_id=1)

    assert -1 <= book.imbalance(levels=2) <= 1
    assert -1 <= book.queue_imbalance() <= 1
    assert book.depth_total("bid", levels=2) == 3.0
    assert book.weighted_mid(levels=2) is not None
    assert book.liquidity_concentration(levels=2) is not None
