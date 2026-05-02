"""Minimal local quickstart for bar-based metrics."""

from __future__ import annotations

import pandas as pd

from orderflowkit import MicrostructurePipeline


def main() -> None:
    dates = pd.date_range("2026-01-01", periods=40, freq="D", tz="UTC")
    close = pd.Series([100 + index * 0.25 for index in range(len(dates))])
    bars = pd.DataFrame(
        {
            "timestamp": dates,
            "open": close - 0.1,
            "high": close + 0.8,
            "low": close - 0.8,
            "close": close,
            "volume": 1_000_000,
        }
    )

    result = (
        MicrostructurePipeline(bars)
        .add_roll_spread(window=5)
        .add_amihud_illiquidity(window=5)
        .add_vwap_deviation()
        .add_realized_vol(window=5)
        .run()
    )
    print(result.metrics.tail())


if __name__ == "__main__":
    main()
