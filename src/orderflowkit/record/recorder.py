"""Async L2 recorder."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pandas as pd

from orderflowkit.book import LocalBook
from orderflowkit.record.quality import QualityReport
from orderflowkit.record.writers import ParquetBatchWriter, RawJsonlZstWriter
from orderflowkit.utils.time import parse_duration, utc_now


class Recorder:
    """Record normalized async L2 streams to raw, normalized, snapshot, and report files."""

    def __init__(
        self, stream: AsyncIterator[dict[str, Any]] | Any, out_dir: str | Path, *, depth: int = 10
    ) -> None:
        self.stream = stream
        self.out_dir = Path(out_dir)
        self.depth = depth

    async def run(self, duration: str | int | float | pd.Timedelta | None = None) -> QualityReport:
        """Run a recording session for an optional bounded duration."""

        started = utc_now()
        stop_after = parse_duration(duration)
        raw_path = self.out_dir / "raw" / f"{started.date()}.events.jsonl.zst"
        normalized_path = self.out_dir / "normalized" / f"{started.date()}.l2_events.parquet"
        snapshots_path = self.out_dir / "books" / f"{started.date()}.book_snapshots.parquet"
        report_path = self.out_dir / "reports" / f"{started.date()}.quality.json"
        raw_writer = RawJsonlZstWriter(raw_path)
        event_writer = ParquetBatchWriter(normalized_path)
        snapshot_writer = ParquetBatchWriter(snapshots_path)
        book: LocalBook | None = None
        spreads: list[float] = []
        raw_events = 0
        normalized_events = 0
        snapshot_count = 0
        exchange = "unknown"
        symbol = "unknown"
        try:
            async for event in self.stream:
                now = utc_now()
                if stop_after is not None and now - started >= stop_after:
                    break
                row = dict(event)
                raw_writer.write(row)
                event_writer.write(row)
                raw_events += 1
                normalized_events += 1
                exchange = str(row.get("exchange", exchange))
                symbol = str(row.get("symbol", symbol))
                if book is None:
                    book = LocalBook(symbol=symbol, exchange=exchange, depth=self.depth)
                book.apply(row)
                for snapshot in book.snapshot_rows(levels=self.depth):
                    snapshot_writer.write(snapshot)
                    snapshot_count += 1
                if book.spread_bps is not None:
                    spreads.append(book.spread_bps)
        finally:
            raw_writer.close()
            event_writer.close()
            snapshot_writer.close()

        ended = utc_now()
        report = QualityReport(
            exchange=exchange,
            symbol=symbol,
            start_time=started,
            end_time=ended,
            raw_events=raw_events,
            normalized_events=normalized_events,
            book_snapshots=snapshot_count,
            sequence_gaps=book.sequence_gaps if book is not None else 0,
            crossed_book_events=book.crossed_events if book is not None else 0,
            median_spread_bps=float(pd.Series(spreads).median()) if spreads else None,
            max_spread_bps=float(pd.Series(spreads).max()) if spreads else None,
        )
        report.write_json(report_path)
        return report
