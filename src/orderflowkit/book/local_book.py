"""Deterministic local L2 order-book reconstruction."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Any

import pandas as pd

from orderflowkit.book.levels import Level
from orderflowkit.book.side import Side, normalize_side
from orderflowkit.utils.time import utc_now


class BookStatus(str, Enum):
    """Lifecycle states for a reconstructed local order book."""

    EMPTY = "empty"
    SYNCING = "syncing"
    LIVE = "live"
    OUT_OF_SYNC = "out_of_sync"
    STALE = "stale"
    CROSSED = "crossed"
    CLOSED = "closed"


@dataclass(slots=True)
class LocalBook:
    """Maintain an aggregated L2 book using snapshots and price-level deltas."""

    symbol: str
    depth: int = 100
    exchange: str = "binance"
    stale_after: pd.Timedelta = pd.Timedelta(seconds=5)
    bids: dict[float, float] = field(default_factory=dict)
    asks: dict[float, float] = field(default_factory=dict)
    status: BookStatus = BookStatus.EMPTY
    last_update_id: int | None = None
    last_exchange_ts: pd.Timestamp | None = None
    last_local_ts: pd.Timestamp | None = None
    sequence_gaps: int = 0
    crossed_events: int = 0

    def clear(self) -> None:
        """Remove all levels and return the book to the empty state."""

        self.bids.clear()
        self.asks.clear()
        self.status = BookStatus.EMPTY
        self.last_update_id = None

    @property
    def valid(self) -> bool:
        """Whether the current book can safely emit features."""

        self._refresh_status()
        return self.status == BookStatus.LIVE

    @property
    def best_bid(self) -> float | None:
        """Best bid price, if present."""

        return max(self.bids) if self.bids else None

    @property
    def best_ask(self) -> float | None:
        """Best ask price, if present."""

        return min(self.asks) if self.asks else None

    @property
    def spread(self) -> float | None:
        """Best ask minus best bid."""

        if self.best_bid is None or self.best_ask is None:
            return None
        return self.best_ask - self.best_bid

    @property
    def mid(self) -> float | None:
        """Midprice from the best bid and ask."""

        if self.best_bid is None or self.best_ask is None:
            return None
        return (self.best_bid + self.best_ask) / 2.0

    @property
    def spread_bps(self) -> float | None:
        """Spread in basis points relative to midprice."""

        spread = self.spread
        mid = self.mid
        if spread is None or mid is None or mid == 0:
            return None
        return (spread / mid) * 10_000.0

    @property
    def microprice(self) -> float | None:
        """Top-of-book microprice weighted by opposite-side queue sizes."""

        bid = self.best_bid
        ask = self.best_ask
        if bid is None or ask is None:
            return None
        bid_size = self.bids.get(bid, 0.0)
        ask_size = self.asks.get(ask, 0.0)
        total = bid_size + ask_size
        if total <= 0:
            return self.mid
        return (ask * bid_size + bid * ask_size) / total

    def apply_snapshot(
        self,
        bids: Iterable[tuple[float, float]],
        asks: Iterable[tuple[float, float]],
        *,
        update_id: int | None = None,
        ts_exchange: Any | None = None,
        ts_local: Any | None = None,
    ) -> None:
        """Replace the full local book with a snapshot."""

        self.bids = self._clean_levels(bids)
        self.asks = self._clean_levels(asks)
        self.last_update_id = update_id
        self.last_exchange_ts = _coerce_timestamp(ts_exchange) if ts_exchange is not None else None
        self.last_local_ts = _coerce_timestamp(ts_local) if ts_local is not None else utc_now()
        self.status = BookStatus.LIVE if self.bids and self.asks else BookStatus.SYNCING
        self._trim()
        self._refresh_status()

    def apply_delta(
        self,
        side: str | Side,
        price: float,
        size: float,
        *,
        update_id: int | None = None,
        first_update_id: int | None = None,
        last_update_id: int | None = None,
        ts_exchange: Any | None = None,
        ts_local: Any | None = None,
        strict_sequence: bool = False,
    ) -> None:
        """Apply a price-level delta, removing the level when size is zero."""

        effective_update_id = last_update_id if last_update_id is not None else update_id
        if self._has_sequence_gap(first_update_id, effective_update_id):
            self.sequence_gaps += 1
            self.status = BookStatus.OUT_OF_SYNC
            if strict_sequence:
                return

        normalized_side = normalize_side(side)
        if normalized_side is Side.BID:
            self._set_level(self.bids, price, size)
        else:
            self._set_level(self.asks, price, size)

        if effective_update_id is not None:
            self.last_update_id = max(
                self.last_update_id or effective_update_id, effective_update_id
            )
        self.last_exchange_ts = _coerce_timestamp(ts_exchange) if ts_exchange is not None else None
        self.last_local_ts = _coerce_timestamp(ts_local) if ts_local is not None else utc_now()
        self._trim()
        if self.status != BookStatus.OUT_OF_SYNC:
            self.status = BookStatus.LIVE if self.bids and self.asks else BookStatus.SYNCING
        self._refresh_status()

    def apply(self, event: Mapping[str, Any]) -> None:
        """Apply a normalized L2 event mapping."""

        is_snapshot = bool(event.get("is_snapshot") or event.get("event_type") == "snapshot")
        update_id = _maybe_int(event.get("update_id"))
        first_update_id = _maybe_int(event.get("first_update_id"))
        last_update_id = _maybe_int(event.get("last_update_id"))
        if is_snapshot and update_id is not None and update_id != self.last_update_id:
            self.bids.clear()
            self.asks.clear()
            self.status = BookStatus.SYNCING

        self.apply_delta(
            str(event["side"]),
            float(event["price"]),
            float(event["size"]),
            update_id=update_id,
            first_update_id=first_update_id,
            last_update_id=last_update_id,
            ts_exchange=event.get("ts_exchange"),
            ts_local=event.get("ts_local"),
        )

    def top_n(self, side: str | Side, levels: int | None = None) -> list[Level]:
        """Return the top N levels for a side."""

        normalized_side = normalize_side(side)
        limit = self.depth if levels is None else levels
        source = self.bids if normalized_side is Side.BID else self.asks
        reverse = normalized_side is Side.BID
        return [Level(price, source[price]) for price in sorted(source, reverse=reverse)[:limit]]

    def depth_total(self, side: str | Side, levels: int = 10) -> float:
        """Return cumulative size across the top N levels for a side."""

        return sum(level.size for level in self.top_n(side, levels))

    def depth_notional(self, side: str | Side, levels: int = 10) -> float:
        """Return cumulative notional across the top N levels for a side."""

        return sum(level.price * level.size for level in self.top_n(side, levels))

    def imbalance(self, levels: int = 10) -> float | None:
        """Return top-N order-book imbalance in [-1, 1]."""

        bid_depth = self.depth_total(Side.BID, levels)
        ask_depth = self.depth_total(Side.ASK, levels)
        total = bid_depth + ask_depth
        if total <= 0:
            return None
        return (bid_depth - ask_depth) / total

    def queue_imbalance(self) -> float | None:
        """Return top-of-book queue imbalance."""

        return self.imbalance(levels=1)

    def weighted_mid(self, levels: int = 1) -> float | None:
        """Return a depth-weighted midpoint using top-N depth on both sides."""

        bid_notional = self.depth_notional(Side.BID, levels)
        ask_notional = self.depth_notional(Side.ASK, levels)
        bid_depth = self.depth_total(Side.BID, levels)
        ask_depth = self.depth_total(Side.ASK, levels)
        total_depth = bid_depth + ask_depth
        if total_depth <= 0:
            return self.mid
        return (bid_notional + ask_notional) / total_depth

    def depth_slope(self, side: str | Side, levels: int = 10) -> float | None:
        """Estimate the slope of cumulative depth as price moves away from mid."""

        top = self.top_n(side, levels)
        mid = self.mid
        if mid is None or len(top) < 2:
            return None
        distances = pd.Series([abs(level.price - mid) for level in top], dtype="float64")
        cumulative = pd.Series([level.size for level in top], dtype="float64").cumsum()
        if float(distances.var()) == 0.0:
            return None
        return float(distances.cov(cumulative) / distances.var())

    def liquidity_concentration(self, levels: int = 10) -> float | None:
        """Share of top-level depth relative to top-N depth across both sides."""

        top = self.depth_total(Side.BID, 1) + self.depth_total(Side.ASK, 1)
        total = self.depth_total(Side.BID, levels) + self.depth_total(Side.ASK, levels)
        if total <= 0:
            return None
        return top / total

    def is_crossed(self) -> bool:
        """Return true when best bid is greater than or equal to best ask."""

        return (
            self.best_bid is not None
            and self.best_ask is not None
            and self.best_bid >= self.best_ask
        )

    def is_stale(self, *, now: Any | None = None) -> bool:
        """Return true when the local book has not updated within ``stale_after``."""

        if self.last_local_ts is None:
            return False
        current = _coerce_timestamp(now) if now is not None else utc_now()
        return current - self.last_local_ts > self.stale_after

    def close(self) -> None:
        """Mark the book as closed."""

        self.status = BookStatus.CLOSED

    def snapshot_rows(self, *, levels: int | None = None) -> list[dict[str, object]]:
        """Return book snapshot rows in the public schema."""

        limit = self.depth if levels is None else levels
        bids = self.top_n(Side.BID, limit)
        asks = self.top_n(Side.ASK, limit)
        rows: list[dict[str, object]] = []
        timestamp = self.last_local_ts or utc_now()
        for index in range(limit):
            bid = bids[index] if index < len(bids) else None
            ask = asks[index] if index < len(asks) else None
            rows.append(
                {
                    "ts_exchange": self.last_exchange_ts,
                    "ts_local": timestamp,
                    "exchange": self.exchange,
                    "symbol": self.symbol,
                    "level": index + 1,
                    "bid_price": bid.price if bid is not None else None,
                    "bid_size": bid.size if bid is not None else None,
                    "ask_price": ask.price if ask is not None else None,
                    "ask_size": ask.size if ask is not None else None,
                    "mid": self.mid,
                    "spread": self.spread,
                    "spread_bps": self.spread_bps,
                    "microprice": self.microprice,
                    "valid": self.valid,
                    "status": self.status.value,
                }
            )
        return rows

    @staticmethod
    def _clean_levels(levels: Iterable[tuple[float, float]]) -> dict[float, float]:
        cleaned: dict[float, float] = {}
        for price, size in levels:
            numeric_price = float(price)
            numeric_size = float(size)
            if numeric_size > 0 and isfinite(numeric_price) and isfinite(numeric_size):
                cleaned[numeric_price] = numeric_size
        return cleaned

    @staticmethod
    def _set_level(levels: dict[float, float], price: float, size: float) -> None:
        numeric_price = float(price)
        numeric_size = float(size)
        if numeric_size <= 0:
            levels.pop(numeric_price, None)
            return
        if isfinite(numeric_price) and isfinite(numeric_size):
            levels[numeric_price] = numeric_size

    def _trim(self) -> None:
        bid_keep = set(sorted(self.bids, reverse=True)[: self.depth])
        ask_keep = set(sorted(self.asks)[: self.depth])
        self.bids = {price: size for price, size in self.bids.items() if price in bid_keep}
        self.asks = {price: size for price, size in self.asks.items() if price in ask_keep}

    def _has_sequence_gap(self, first_update_id: int | None, update_id: int | None) -> bool:
        if update_id is None or self.last_update_id is None:
            return False
        if update_id <= self.last_update_id:
            return False
        expected = self.last_update_id + 1
        if first_update_id is not None:
            return first_update_id > expected
        return update_id > expected

    def _refresh_status(self) -> None:
        if self.status in {BookStatus.CLOSED, BookStatus.OUT_OF_SYNC}:
            return
        if not self.bids or not self.asks:
            self.status = (
                BookStatus.EMPTY if not self.bids and not self.asks else BookStatus.SYNCING
            )
            return
        if self.is_crossed():
            self.crossed_events += 1
            self.status = BookStatus.CROSSED
            return
        self.status = BookStatus.LIVE


def _maybe_int(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    return int(value)


def _coerce_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")
