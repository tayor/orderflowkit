"""Future-return labels."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from orderflowkit.labels.classification import up_down_flat
from orderflowkit.utils.validators import require_columns


def future_return_mid(features: pd.DataFrame, horizon: str = "5s") -> pd.Series:
    """Return future log mid returns using only observations after each timestamp."""

    require_columns(features, ["timestamp", "mid"])
    frame = features[["timestamp", "mid"]].copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["_row_order"] = np.arange(len(frame))
    frame = frame.sort_values(["timestamp", "_row_order"])
    future_time = frame["timestamp"] + pd.Timedelta(horizon)
    right = frame.rename(columns={"timestamp": "future_timestamp", "mid": "future_mid"})
    merged = pd.merge_asof(
        pd.DataFrame({"future_time": future_time}),
        right,
        left_on="future_time",
        right_on="future_timestamp",
        direction="forward",
    )
    returns = np.log(
        merged["future_mid"].to_numpy(dtype=float) / frame["mid"].to_numpy(dtype=float)
    )
    result = pd.Series(returns, index=frame.index, name=f"future_return_mid_{horizon}")
    return result.reindex(features.index)


@dataclass(slots=True)
class Labeler:
    """Apply regression and classification labels to feature tables."""

    target: str = "mid_return"
    horizons: list[str] = field(default_factory=lambda: ["1s", "5s", "30s"])
    thresholds_bps: list[float] = field(default_factory=lambda: [1.0, 2.0, 5.0])

    def apply(self, features: pd.DataFrame) -> pd.DataFrame:
        """Return a copy of features with future-return and up/down/flat labels."""

        result = features.copy()
        for horizon in self.horizons:
            return_column = f"future_return_mid_{horizon}"
            result[return_column] = future_return_mid(result, horizon=horizon)
            for threshold in self.thresholds_bps:
                result[f"label_udf_{horizon}_{threshold:g}bps"] = up_down_flat(
                    result[return_column], threshold_bps=threshold
                )
        if "valid_book" in result.columns:
            result = result[result["valid_book"].fillna(False)].reset_index(drop=True)
        return result
