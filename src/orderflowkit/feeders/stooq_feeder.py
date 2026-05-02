"""Stooq CSV feeder placeholder."""

from __future__ import annotations

import pandas as pd

from orderflowkit.utils.exceptions import OptionalDependencyError


class StooqFeeder:
    """Stooq adapter reserved for a post-alpha implementation."""

    def fetch(self, symbol: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        """Raise a clear message for the not-yet-implemented adapter."""

        raise OptionalDependencyError("StooqFeeder is planned but not implemented in 0.1.0")
