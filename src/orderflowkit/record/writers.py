"""Storage writers for raw and normalized market data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson
import pandas as pd
import zstandard as zstd


class RawJsonlZstWriter:
    """Append raw event dictionaries to a compressed JSONL file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("wb")
        self._stream = zstd.ZstdCompressor().stream_writer(self._file)

    def write(self, row: dict[str, Any]) -> None:
        """Write one row."""

        self._stream.write(orjson.dumps(row, default=str) + b"\n")

    def close(self) -> None:
        """Flush and close the compressed stream."""

        self._stream.flush(zstd.FLUSH_FRAME)
        self._stream.close()
        self._file.close()

    def __enter__(self) -> RawJsonlZstWriter:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()


class ParquetBatchWriter:
    """Collect rows in memory and write a compact Parquet file on close."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.rows: list[dict[str, Any]] = []

    def write(self, row: dict[str, Any]) -> None:
        """Buffer one row."""

        self.rows.append(row)

    def close(self) -> None:
        """Write all buffered rows to Parquet."""

        pd.DataFrame(self.rows).to_parquet(self.path, index=False)

    def __enter__(self) -> ParquetBatchWriter:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()
