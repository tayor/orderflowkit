# OrderFlowKit

**OrderFlowKit** is a Python library for free-data market microstructure analytics, order-flow features, L2 order-book capture, replay, and ML-ready dataset generation.

It is built for independent quant researchers, educators, ML researchers, and crypto market-data projects that need a reproducible research pipeline without paid feeds or private trading credentials.

## What It Does

OrderFlowKit turns OHLCV bars, trades, and public crypto L2 depth streams into clean, testable research artifacts:

- Bar and trade microstructure metrics such as Roll spread, Corwin-Schultz spread, Amihud illiquidity, VWAP deviation, tick rule signs, BVC volume splits, Parkinson volatility, realized volatility, variance ratio, and Hurst exponent.
- Binance REST klines and aggregate trade ingestion with normalized pandas outputs.
- Binance Spot WebSocket depth ingestion for public L2 streams.
- Deterministic local order-book reconstruction with sequence-gap, crossed-book, and stale-book detection.
- Quote, depth, imbalance, flow, volatility, and label generation for ML workflows.
- Parquet, compressed JSONL, quality-report, replay, plotting, and CLI utilities.

OrderFlowKit is a research toolkit. It does not execute orders, manage portfolios, claim manipulation detection, or model private exchange queues.

## Install

From PyPI after release:

```bash
uv pip install OrderFlowKit
```

For local development:

```bash
git clone https://github.com/tayor/orderflowkit.git
cd orderflowkit
uv venv
uv sync --extra dev --extra stream --extra viz --extra bars
```

The import name is lowercase:

```python
import orderflowkit as ofk
```

The command-line entry point is:

```bash
ofk --help
```

## Quickstart: OHLCV Metrics

```python
from orderflowkit import MicrostructurePipeline
from orderflowkit.feeders import YFinanceFeeder

feeder = YFinanceFeeder()
bars = feeder.fetch("SPY", start="2024-01-01", end="2024-12-31", interval="1d")

result = (
    MicrostructurePipeline(bars)
    .add_roll_spread(window=20)
    .add_corwin_schultz_spread()
    .add_amihud_illiquidity(window=20)
    .add_vwap_deviation()
    .add_parkinson_vol(window=20)
    .add_realized_vol(window=20)
    .run()
)

print(result.metrics.tail())
print(result.summary())
```

## Quickstart: Binance REST Trades

```python
from orderflowkit.feeders import BinanceRestFeeder
from orderflowkit.metrics.order_flow import order_imbalance, tick_rule

feeder = BinanceRestFeeder()
trades = feeder.fetch_trades("BTCUSDT", start="2026-05-01", end="2026-05-02")

trades["sign"] = tick_rule(trades["price"])
trades["signed_volume"] = trades["sign"] * trades["quantity"]
imbalance = order_imbalance.from_signed_volume(trades["signed_volume"])
```

## Quickstart: Local Book Reconstruction

```python
from orderflowkit.book import LocalBook

book = LocalBook(symbol="BTCUSDT", depth=10)

book.apply_snapshot(
    bids=[(100.0, 2.0), (99.5, 1.0)],
    asks=[(100.5, 1.5), (101.0, 3.0)],
    update_id=1,
)
book.apply_delta(side="bid", price=100.0, size=3.0, update_id=2)

print(book.mid)
print(book.spread_bps)
print(book.imbalance(levels=2))
```

## Quickstart: Binance L2 Recording

```python
import asyncio

from orderflowkit.record import Recorder
from orderflowkit.streams import BinanceDepthStream


async def main() -> None:
    stream = BinanceDepthStream(symbol="BTCUSDT", depth=100)
    recorder = Recorder(stream, out_dir="./data/BTCUSDT")
    await recorder.run(duration="1m")


asyncio.run(main())
```

This writes raw compressed JSONL, normalized Parquet events, book snapshots, and a quality report.

## CLI Examples

Fetch bars:

```bash
ofk fetch bars AAPL --source yfinance --start 2024-01-01 --end 2024-12-31 --interval 1d --out data/AAPL.bars.parquet
```

Compute bar metrics:

```bash
ofk metrics bars data/AAPL.bars.parquet --preset academic --out metrics/AAPL.metrics.parquet
```

Build L2 features from normalized events:

```bash
ofk features l2 data/BTCUSDT/normalized/2026-05-03.l2_events.parquet --levels 1,5,10 --out features/BTCUSDT.features.parquet
```

Generate labels:

```bash
ofk labels features/BTCUSDT.features.parquet --horizons 1s,5s,30s --threshold-bps 2 --out datasets/BTCUSDT.ml.parquet
```

Replay a local event file:

```bash
ofk replay data/BTCUSDT/normalized/2026-05-03.l2_events.parquet --speed max
```

## Data Schemas

OrderFlowKit normalizes data around stable pandas/Parquet schemas:

- Bars: `timestamp`, `symbol`, `source`, `open`, `high`, `low`, `close`, `volume`, `dollar_volume`, `interval`
- Trades: `timestamp`, `symbol`, `source`, `trade_id`, `price`, `quantity`, `side`, `is_buyer_maker`, `notional`
- L2 events: `ts_exchange`, `ts_local`, `exchange`, `symbol`, `event_type`, `side`, `price`, `size`, `update_id`, `first_update_id`, `last_update_id`, `sequence`, `is_snapshot`, `raw_payload`
- Book snapshots: `ts_exchange`, `ts_local`, `exchange`, `symbol`, `level`, `bid_price`, `bid_size`, `ask_price`, `ask_size`, `mid`, `spread`, `spread_bps`, `microprice`, `valid`, `status`

## Feature Presets

- `academic`: bar-data metrics for classical market microstructure research.
- `crypto_l2`: book-derived quote, depth, spread, microprice, imbalance, and volatility features.
- `ml_default`: lagged returns, depth ratios, order-flow windows, volatility windows, and quality flags.

## Testing

The test suite is designed to run in minutes and does not require network access:

```bash
uv run pytest
uv run ruff check .
uv run mypy
uv run python -m build
uv run twine check dist/*
```

## Data-Source Notes

Free data sources have limits, gaps, symbol restrictions, and outages. OrderFlowKit preserves raw exchange payloads where possible, emits data-quality reports, and surfaces invalid book intervals so downstream research can filter or label them.

## License

OrderFlowKit is MIT licensed.
