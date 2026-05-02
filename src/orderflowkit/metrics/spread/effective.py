"""Trade-level effective spread."""

from __future__ import annotations

import pandas as pd


def effective_spread(
    price: pd.Series, mid: pd.Series, side_sign: pd.Series | None = None
) -> pd.Series:
    """Compute effective spread from trade prices and contemporaneous midpoint prices."""

    trade_price = pd.to_numeric(price, errors="coerce")
    midpoint = pd.to_numeric(mid, errors="coerce")
    if side_sign is None:
        spread = 2.0 * (trade_price - midpoint).abs()
    else:
        spread = 2.0 * pd.to_numeric(side_sign, errors="coerce") * (trade_price - midpoint)
    return pd.Series(spread, index=price.index, name="effective_spread")
