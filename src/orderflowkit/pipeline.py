"""Fluent pandas-first microstructure pipeline."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd

from orderflowkit.metrics.efficiency import rolling_hurst, rolling_variance_ratio
from orderflowkit.metrics.liquidity import amihud_illiquidity, kyle_lambda, vwap, vwap_deviation
from orderflowkit.metrics.order_flow import bulk_volume_classify, tick_rule
from orderflowkit.metrics.order_flow.imbalance import from_signed_volume
from orderflowkit.metrics.spread import corwin_schultz_spread, roll_spread
from orderflowkit.metrics.volatility import parkinson_vol, realized_vol
from orderflowkit.utils.validators import require_columns

Operation = Callable[[pd.DataFrame], pd.DataFrame]


@dataclass(slots=True)
class PipelineResult:
    """Result returned by ``MicrostructurePipeline.run``."""

    metrics: pd.DataFrame

    def summary(self) -> pd.DataFrame:
        """Return summary statistics for numeric metric columns."""

        return self.metrics.select_dtypes(include="number").describe().transpose()


@dataclass(slots=True)
class MicrostructurePipeline:
    """Chain classical microstructure metrics over a bar/trade DataFrame."""

    data: pd.DataFrame
    _operations: list[Operation] = field(default_factory=list)

    def add_roll_spread(self, window: int = 20) -> MicrostructurePipeline:
        """Add Roll spread."""

        def operation(frame: pd.DataFrame) -> pd.DataFrame:
            require_columns(frame, ["close"])
            frame[f"roll_spread_{window}"] = roll_spread(frame["close"], window=window)
            return frame

        self._operations.append(operation)
        return self

    def add_corwin_schultz_spread(self) -> MicrostructurePipeline:
        """Add Corwin-Schultz spread."""

        def operation(frame: pd.DataFrame) -> pd.DataFrame:
            require_columns(frame, ["high", "low"])
            frame["corwin_schultz_spread"] = corwin_schultz_spread(frame["high"], frame["low"])
            return frame

        self._operations.append(operation)
        return self

    def add_amihud_illiquidity(self, window: int = 20) -> MicrostructurePipeline:
        """Add Amihud illiquidity."""

        def operation(frame: pd.DataFrame) -> pd.DataFrame:
            require_columns(frame, ["close", "volume"])
            frame[f"amihud_illiquidity_{window}"] = amihud_illiquidity(
                frame["close"], frame["volume"], window=window
            )
            return frame

        self._operations.append(operation)
        return self

    def add_kyle_lambda(self, window: int = 20) -> MicrostructurePipeline:
        """Add Kyle lambda proxy."""

        def operation(frame: pd.DataFrame) -> pd.DataFrame:
            require_columns(frame, ["close", "volume"])
            frame[f"kyle_lambda_{window}"] = kyle_lambda(
                frame["close"], frame["volume"], window=window
            )
            return frame

        self._operations.append(operation)
        return self

    def add_vwap_deviation(self) -> MicrostructurePipeline:
        """Add VWAP and close-to-VWAP deviation."""

        def operation(frame: pd.DataFrame) -> pd.DataFrame:
            require_columns(frame, ["high", "low", "close", "volume"])
            frame["vwap"] = vwap(frame["high"], frame["low"], frame["close"], frame["volume"])
            frame["vwap_deviation"] = vwap_deviation(frame["close"], frame["vwap"])
            return frame

        self._operations.append(operation)
        return self

    def add_bvc(self, window: int = 20) -> MicrostructurePipeline:
        """Add bulk volume classification columns."""

        def operation(frame: pd.DataFrame) -> pd.DataFrame:
            require_columns(frame, ["open", "high", "low", "close", "volume"])
            bvc = bulk_volume_classify(
                frame["open"],
                frame["high"],
                frame["low"],
                frame["close"],
                frame["volume"],
                window=window,
            )
            return frame.join(bvc.add_prefix("bvc_"))

        self._operations.append(operation)
        return self

    def add_tick_rule(self) -> MicrostructurePipeline:
        """Add tick-rule signs from close prices."""

        def operation(frame: pd.DataFrame) -> pd.DataFrame:
            require_columns(frame, ["close"])
            frame["tick_sign"] = tick_rule(frame["close"])
            return frame

        self._operations.append(operation)
        return self

    def add_order_imbalance(self, window: int | None = None) -> MicrostructurePipeline:
        """Add order imbalance from signed volume, deriving it when necessary."""

        def operation(frame: pd.DataFrame) -> pd.DataFrame:
            if "bvc_signed_volume" in frame.columns:
                signed_volume = frame["bvc_signed_volume"]
            else:
                require_columns(frame, ["close", "volume"])
                signed_volume = tick_rule(frame["close"]) * frame["volume"]
            suffix = "cumulative" if window is None else str(window)
            frame[f"order_imbalance_{suffix}"] = from_signed_volume(signed_volume, window=window)
            return frame

        self._operations.append(operation)
        return self

    def add_parkinson_vol(self, window: int = 20) -> MicrostructurePipeline:
        """Add Parkinson volatility."""

        def operation(frame: pd.DataFrame) -> pd.DataFrame:
            require_columns(frame, ["high", "low"])
            frame[f"parkinson_vol_{window}"] = parkinson_vol(
                frame["high"], frame["low"], window=window
            )
            return frame

        self._operations.append(operation)
        return self

    def add_realized_vol(self, window: int = 20) -> MicrostructurePipeline:
        """Add realized volatility."""

        def operation(frame: pd.DataFrame) -> pd.DataFrame:
            require_columns(frame, ["close"])
            frame[f"realized_vol_{window}"] = realized_vol(frame["close"], window=window)
            return frame

        self._operations.append(operation)
        return self

    def add_variance_ratio(self, lag: int = 5, window: int = 120) -> MicrostructurePipeline:
        """Add rolling variance ratio."""

        def operation(frame: pd.DataFrame) -> pd.DataFrame:
            require_columns(frame, ["close"])
            frame[f"variance_ratio_{lag}"] = rolling_variance_ratio(
                frame["close"], lag=lag, window=window
            )
            return frame

        self._operations.append(operation)
        return self

    def add_hurst_exponent(self, window: int = 252) -> MicrostructurePipeline:
        """Add rolling Hurst exponent."""

        def operation(frame: pd.DataFrame) -> pd.DataFrame:
            require_columns(frame, ["close"])
            frame[f"hurst_{window}"] = rolling_hurst(frame["close"], window=window)
            return frame

        self._operations.append(operation)
        return self

    def add_academic_preset(self) -> MicrostructurePipeline:
        """Add the default academic OHLCV preset."""

        return (
            self.add_roll_spread()
            .add_corwin_schultz_spread()
            .add_amihud_illiquidity()
            .add_kyle_lambda()
            .add_vwap_deviation()
            .add_parkinson_vol()
            .add_realized_vol()
            .add_variance_ratio()
            .add_hurst_exponent()
        )

    def run(self) -> PipelineResult:
        """Execute all queued operations and return a result object."""

        frame = self.data.copy()
        for operation in self._operations:
            frame = operation(frame)
        return PipelineResult(metrics=frame)
