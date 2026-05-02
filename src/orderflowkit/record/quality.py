"""Recording quality reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import orjson
import pandas as pd


@dataclass(slots=True)
class QualityReport:
    """Summary quality metrics for one recording session."""

    exchange: str
    symbol: str
    start_time: pd.Timestamp
    end_time: pd.Timestamp
    raw_events: int = 0
    normalized_events: int = 0
    book_snapshots: int = 0
    sequence_gaps: int = 0
    resyncs: int = 0
    crossed_book_events: int = 0
    stale_intervals: int = 0
    invalid_intervals_seconds: float = 0.0
    median_spread_bps: float | None = None
    max_spread_bps: float | None = None

    @property
    def quality_score(self) -> float:
        """Simple bounded quality score in [0, 1]."""

        total_seconds = max((self.end_time - self.start_time).total_seconds(), 1.0)
        invalid_ratio = min(self.invalid_intervals_seconds / total_seconds, 1.0)
        penalties = (
            0.01 * self.sequence_gaps
            + 0.02 * self.crossed_book_events
            + 0.01 * self.stale_intervals
        )
        return max(0.0, min(1.0, 1.0 - invalid_ratio - penalties))

    def as_dict(self) -> dict[str, object]:
        """Serialize report to JSON-friendly values."""

        return {
            "exchange": self.exchange,
            "symbol": self.symbol,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "raw_events": self.raw_events,
            "normalized_events": self.normalized_events,
            "book_snapshots": self.book_snapshots,
            "sequence_gaps": self.sequence_gaps,
            "resyncs": self.resyncs,
            "crossed_book_events": self.crossed_book_events,
            "stale_intervals": self.stale_intervals,
            "invalid_intervals_seconds": self.invalid_intervals_seconds,
            "median_spread_bps": self.median_spread_bps,
            "max_spread_bps": self.max_spread_bps,
            "quality_score": self.quality_score,
        }

    def write_json(self, path: str | Path) -> None:
        """Write the report as pretty JSON."""

        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(orjson.dumps(self.as_dict(), option=orjson.OPT_INDENT_2))
