"""Feature pipeline for L2 event and book-snapshot data."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from orderflowkit.book import LocalBook, Side
from orderflowkit.features.depth import add_depth_features
from orderflowkit.features.flow import add_flow_features
from orderflowkit.features.imbalance import add_imbalance_features
from orderflowkit.features.quote import add_quote_features
from orderflowkit.features.volatility import add_volatility_features


@dataclass(slots=True)
class FeaturePipeline:
    """Generate ML-ready features from normalized L2 events or book snapshots."""

    levels: list[int] = field(default_factory=lambda: [1, 5, 10])
    windows: list[str] = field(default_factory=lambda: ["1s", "5s"])
    include: list[str] = field(
        default_factory=lambda: ["quotes", "depth", "imbalance", "order_flow", "volatility"]
    )

    def from_l2_events(self, path_or_frame: str | Path | pd.DataFrame) -> pd.DataFrame:
        """Reconstruct a local book from normalized L2 events and emit feature rows."""

        events = _read_frame(path_or_frame)
        if events.empty:
            return pd.DataFrame()
        events = events.sort_values("ts_local").reset_index(drop=True)
        first = events.iloc[0]
        book = LocalBook(
            symbol=str(first["symbol"]), exchange=str(first["exchange"]), depth=max(self.levels)
        )
        rows: list[dict[str, Any]] = []
        for event in events.to_dict(orient="records"):
            book.apply(event)
            if book.mid is None:
                continue
            rows.append(self._row_from_book(book))
        return self._finalize(pd.DataFrame(rows))

    def from_book_snapshots(self, path_or_frame: str | Path | pd.DataFrame) -> pd.DataFrame:
        """Generate features from book snapshot rows."""

        snapshots = _read_frame(path_or_frame)
        if snapshots.empty:
            return snapshots
        rows: list[dict[str, Any]] = []
        for timestamp, group in snapshots.groupby("ts_local", sort=True):
            group = group.sort_values("level")
            row: dict[str, Any] = {
                "timestamp": pd.Timestamp(str(timestamp)),
                "exchange": group["exchange"].iloc[0],
                "symbol": group["symbol"].iloc[0],
                "mid": group["mid"].iloc[0],
                "spread": group["spread"].iloc[0],
                "spread_bps": group["spread_bps"].iloc[0],
                "microprice": group["microprice"].iloc[0],
                "weighted_mid": group["mid"].iloc[0],
                "valid_book": bool(group["valid"].iloc[0]),
                "quality_flag": str(group["status"].iloc[0]),
            }
            for level in self.levels:
                top = group[group["level"] <= level]
                bid_depth = pd.to_numeric(top["bid_size"], errors="coerce").fillna(0.0).sum()
                ask_depth = pd.to_numeric(top["ask_size"], errors="coerce").fillna(0.0).sum()
                row[f"bid_depth_{level}"] = bid_depth
                row[f"ask_depth_{level}"] = ask_depth
            rows.append(row)
        return self._finalize(pd.DataFrame(rows))

    def _row_from_book(self, book: LocalBook) -> dict[str, Any]:
        row: dict[str, Any] = {
            "timestamp": book.last_local_ts,
            "exchange": book.exchange,
            "symbol": book.symbol,
            "mid": book.mid,
            "spread": book.spread,
            "spread_bps": book.spread_bps,
            "microprice": book.microprice,
            "weighted_mid": book.weighted_mid(levels=1),
            "valid_book": book.valid,
            "quality_flag": book.status.value,
        }
        for level in self.levels:
            row[f"imbalance_{level}"] = book.imbalance(levels=level)
            row[f"bid_depth_{level}"] = book.depth_total(Side.BID, levels=level)
            row[f"ask_depth_{level}"] = book.depth_total(Side.ASK, levels=level)
            row[f"depth_slope_bid_{level}"] = book.depth_slope(Side.BID, levels=level)
            row[f"depth_slope_ask_{level}"] = book.depth_slope(Side.ASK, levels=level)
        return row

    def _finalize(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return frame
        result = frame.sort_values("timestamp").reset_index(drop=True)
        if "quotes" in self.include:
            result = add_quote_features(result)
        if "imbalance" in self.include:
            result = add_imbalance_features(result, self.levels)
        if "depth" in self.include:
            result = add_depth_features(result, self.levels)
        if "order_flow" in self.include:
            result = add_flow_features(result, self.windows)
        if "volatility" in self.include:
            result = add_volatility_features(result, self.windows)
        return result


def _read_frame(path_or_frame: str | Path | pd.DataFrame) -> pd.DataFrame:
    if isinstance(path_or_frame, pd.DataFrame):
        return path_or_frame.copy()
    return pd.read_parquet(path_or_frame)
