"""Yahoo Finance feeder via optional yfinance dependency."""

from __future__ import annotations

import pandas as pd

from orderflowkit.schemas import normalize_bars
from orderflowkit.utils.exceptions import OptionalDependencyError


class YFinanceFeeder:
    """Fetch OHLCV bars from Yahoo Finance using yfinance."""

    source = "yfinance"

    def fetch(self, symbol: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        """Fetch and normalize OHLCV bars."""

        try:
            import yfinance as yf
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise OptionalDependencyError(
                "Install OrderFlowKit[bars] to use YFinanceFeeder"
            ) from exc
        frame = yf.download(
            symbol, start=start, end=end, interval=interval, auto_adjust=False, progress=False
        )
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)
        return normalize_bars(
            frame.reset_index(names="timestamp"),
            symbol=symbol,
            source=self.source,
            interval=interval,
        )
