"""PHASTER parser."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pgpb_pipeline.io import safe_read_table


def parse_phaster(path: str | Path, sample_id: str) -> pd.DataFrame:
    columns = ["sample_id", "region_count", "intact_count"]
    df = safe_read_table(path, columns=columns)
    if df.empty:
        return pd.DataFrame([{"sample_id": sample_id, "region_count": pd.NA, "intact_count": pd.NA}])
    return df.reindex(columns=columns)

