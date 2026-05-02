from __future__ import annotations

from orderflowkit.feeders import BinanceRestFeeder
from orderflowkit.streams import normalize_binance_depth_message


def test_binance_depth_message_normalizer() -> None:
    rows = normalize_binance_depth_message(
        {
            "E": 1_777_808_000_000,
            "U": 10,
            "u": 11,
            "b": [["100.0", "1.0"]],
            "a": [["101.0", "2.0"]],
        },
        symbol="btcusdt",
    )

    assert len(rows) == 2
    assert rows[0]["symbol"] == "BTCUSDT"
    assert rows[0]["side"] == "bid"
    assert rows[1]["side"] == "ask"
    assert rows[0]["first_update_id"] == 10
    assert rows[0]["last_update_id"] == 11


def test_binance_rest_feeder_normalizes_klines_and_trades(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    feeder = BinanceRestFeeder(base_url="https://example.test")

    def fake_get_json(
        path: str, *, params: dict[str, object]
    ) -> list[list[object]] | list[dict[str, object]]:
        if path.endswith("klines"):
            return [
                [
                    1_777_808_000_000,
                    "100",
                    "101",
                    "99",
                    "100.5",
                    "10",
                    1_777_808_060_000,
                    "1005",
                    5,
                    "5",
                    "500",
                    "0",
                ]
            ]
        return [{"a": 1, "p": "100.5", "q": "0.25", "T": 1_777_808_000_000, "m": False}]

    monkeypatch.setattr(feeder, "_get_json", fake_get_json)

    bars = feeder.fetch_klines("btcusdt", start="2026-05-03", end="2026-05-04")
    trades = feeder.fetch_trades("btcusdt", start="2026-05-03", end="2026-05-04")

    assert bars.loc[0, "symbol"] == "BTCUSDT"
    assert bars.loc[0, "dollar_volume"] == 1005.0
    assert trades.loc[0, "side"] == "buy"
    assert trades.loc[0, "notional"] == 25.125
