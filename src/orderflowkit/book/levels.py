"""Lightweight order-book level types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Level:
    """A price level in an aggregated L2 order book."""

    price: float
    size: float
