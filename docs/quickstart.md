# Quickstart

Install from a local checkout:

```bash
uv sync --extra dev --extra stream --extra viz --extra bars
```

Compute classical OHLCV metrics:

```python
from orderflowkit import MicrostructurePipeline

result = MicrostructurePipeline(bars).add_roll_spread().add_amihud_illiquidity().run()
```

Reconstruct an order book:

```python
from orderflowkit.book import LocalBook

book = LocalBook("BTCUSDT")
book.apply_snapshot([(100, 1)], [(101, 1)], update_id=1)
```
