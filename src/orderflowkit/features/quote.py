"""Quote feature helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_quote_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add log mid, mid returns, and quote cleanliness columns."""

    result = frame.copy()
    if "mid" in result.columns:
        result["log_mid"] = np.log(pd.to_numeric(result["mid"], errors="coerce"))
        result["mid_return_1"] = result["log_mid"].diff()
    if "valid" in result.columns and "valid_book" not in result.columns:
        result["valid_book"] = result["valid"].astype(bool)
    if "status" in result.columns and "quality_flag" not in result.columns:
        result["quality_flag"] = result["status"].astype(str)
    return result
