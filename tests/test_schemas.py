from __future__ import annotations

import pandas as pd

from orderflowkit.schemas import (
    BAR_COLUMNS,
    TRADE_COLUMNS,
    L2Event,
    normalize_bars,
    normalize_trades,
)


def test_normalize_bars_and_trades() -> None:
    bars = normalize_bars(
        pd.DataFrame(
            {
                "timestamp": ["2026-05-03"],
                "open": [100],
                "high": [101],
                "low": [99],
                "close": [100.5],
                "volume": [10],
            }
        ),
        symbol="ABC",
        source="fixture",
        interval="1d",
    )
    trades = normalize_trades(
        pd.DataFrame(
            {"timestamp": ["2026-05-03"], "trade_id": ["1"], "price": [100.0], "quantity": [2.0]}
        ),
        symbol="ABC",
        source="fixture",
    )

    assert bars.columns.tolist() == BAR_COLUMNS
    assert trades.columns.tolist() == TRADE_COLUMNS
    assert bars.loc[0, "dollar_volume"] == 1005.0
    assert trades.loc[0, "notional"] == 200.0


def test_l2_event_schema_row() -> None:
    event = L2Event(
        ts_local=pd.Timestamp("2026-05-03T12:00:00Z").to_pydatetime(),
        exchange="binance",
        symbol="BTCUSDT",
        side="bid",
        price=100.0,
        size=1.0,
    )
    row = event.as_row()
    assert row["symbol"] == "BTCUSDT"
    assert row["event_type"] == "delta"
