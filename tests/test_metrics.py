from __future__ import annotations

import numpy as np
import pandas as pd

from orderflowkit.metrics.efficiency import hurst_exponent, rolling_variance_ratio, variance_ratio
from orderflowkit.metrics.liquidity import amihud_illiquidity, kyle_lambda, vwap, vwap_deviation
from orderflowkit.metrics.order_flow import bulk_volume_classify, order_imbalance, tick_rule
from orderflowkit.metrics.spread import corwin_schultz_spread, high_low_spread, roll_spread
from orderflowkit.metrics.volatility import (
    garman_klass_vol,
    parkinson_vol,
    realized_vol,
    yang_zhang_vol,
)


def test_spread_estimators_are_non_negative(sample_bars: pd.DataFrame) -> None:
    roll = roll_spread(sample_bars["close"], window=5)
    corwin = corwin_schultz_spread(sample_bars["high"], sample_bars["low"])
    high_low = high_low_spread(sample_bars["high"], sample_bars["low"], sample_bars["close"])

    assert (roll.dropna() >= 0).all()
    assert (corwin.dropna() >= 0).all()
    assert (high_low.dropna() >= 0).all()


def test_liquidity_metrics_handle_zero_volume(sample_bars: pd.DataFrame) -> None:
    bars = sample_bars.copy()
    bars.loc[5, "volume"] = 0
    amihud = amihud_illiquidity(bars["close"], bars["volume"], window=5)
    kyle = kyle_lambda(bars["close"], bars["volume"], window=5)
    vwap_values = vwap(bars["high"], bars["low"], bars["close"], bars["volume"])
    deviation = vwap_deviation(bars["close"], vwap_values)

    assert np.isfinite(vwap_values.dropna()).all()
    assert np.isfinite(deviation.dropna()).all()
    assert amihud.name == "amihud_illiquidity"
    assert kyle.name == "kyle_lambda"


def test_tick_rule_and_bvc_conserve_volume(sample_bars: pd.DataFrame) -> None:
    prices = pd.Series([100.0, 101.0, 101.0, 100.5, 100.5])
    signs = tick_rule(prices)
    assert signs.tolist() == [0, 1, 1, -1, -1]

    classified = bulk_volume_classify(
        sample_bars["open"],
        sample_bars["high"],
        sample_bars["low"],
        sample_bars["close"],
        sample_bars["volume"],
        window=5,
    )
    reconstructed = classified["buy_volume"] + classified["sell_volume"]
    assert np.allclose(reconstructed, sample_bars["volume"])

    imbalance = order_imbalance.from_signed_volume(classified["signed_volume"], window=5)
    assert ((imbalance.dropna() >= -1) & (imbalance.dropna() <= 1)).all()


def test_volatility_and_efficiency_metrics(sample_bars: pd.DataFrame) -> None:
    assert (parkinson_vol(sample_bars["high"], sample_bars["low"], window=5).dropna() >= 0).all()
    assert (
        garman_klass_vol(
            sample_bars["open"],
            sample_bars["high"],
            sample_bars["low"],
            sample_bars["close"],
            window=5,
        )
        .dropna()
        .ge(0)
        .all()
    )
    assert (
        yang_zhang_vol(
            sample_bars["open"],
            sample_bars["high"],
            sample_bars["low"],
            sample_bars["close"],
            window=5,
        )
        .dropna()
        .ge(0)
        .all()
    )
    assert (realized_vol(sample_bars["close"], window=5).dropna() >= 0).all()

    ratio = variance_ratio(sample_bars["close"], lag=5)
    rolling = rolling_variance_ratio(sample_bars["close"], lag=5, window=20)
    hurst = hurst_exponent(sample_bars["close"], min_lag=2, max_lag=20)

    assert ratio["observations"] > 5
    assert rolling.notna().any()
    assert np.isfinite(hurst)
