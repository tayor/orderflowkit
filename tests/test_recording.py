from __future__ import annotations

import pandas as pd
import pytest

from orderflowkit.record import Recorder


class FiniteAsyncStream:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows

    async def __aiter__(self):  # type: ignore[no-untyped-def]
        for row in self.rows:
            yield row


@pytest.mark.asyncio()
async def test_recorder_writes_outputs(sample_l2_events: pd.DataFrame, tmp_path) -> None:  # type: ignore[no-untyped-def]
    stream = FiniteAsyncStream(sample_l2_events.to_dict(orient="records"))
    report = await Recorder(stream, tmp_path / "BTCUSDT", depth=2).run()

    assert report.raw_events == len(sample_l2_events)
    assert report.normalized_events == len(sample_l2_events)
    assert report.book_snapshots > 0
    assert 0 <= report.quality_score <= 1
    assert list((tmp_path / "BTCUSDT" / "normalized").glob("*.parquet"))
    assert list((tmp_path / "BTCUSDT" / "books").glob("*.parquet"))
    assert list((tmp_path / "BTCUSDT" / "reports").glob("*.json"))
