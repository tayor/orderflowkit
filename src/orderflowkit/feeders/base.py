"""Base feeder protocol."""

from __future__ import annotations

from typing import Protocol

import pandas as pd


class BaseFeeder(Protocol):
    """Protocol for historical market-data feeders."""

    def fetch(self, symbol: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        """Fetch market data for a symbol."""
