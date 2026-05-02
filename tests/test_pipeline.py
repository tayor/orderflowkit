from __future__ import annotations

import pandas as pd

from orderflowkit import MicrostructurePipeline


def test_microstructure_pipeline_adds_expected_columns(sample_bars: pd.DataFrame) -> None:
    result = (
        MicrostructurePipeline(sample_bars)
        .add_roll_spread(window=5)
        .add_corwin_schultz_spread()
        .add_amihud_illiquidity(window=5)
        .add_kyle_lambda(window=5)
        .add_vwap_deviation()
        .add_bvc(window=5)
        .add_order_imbalance(window=5)
        .add_parkinson_vol(window=5)
        .add_realized_vol(window=5)
        .add_variance_ratio(lag=3, window=20)
        .add_hurst_exponent(window=30)
        .run()
    )

    metrics = result.metrics
    assert "roll_spread_5" in metrics
    assert "corwin_schultz_spread" in metrics
    assert "amihud_illiquidity_5" in metrics
    assert "bvc_buy_volume" in metrics
    assert "order_imbalance_5" in metrics
    assert "realized_vol_5" in metrics
    assert not result.summary().empty
