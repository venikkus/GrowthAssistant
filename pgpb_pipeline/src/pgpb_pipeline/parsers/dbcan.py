"""dbCAN parser."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pgpb_pipeline.io import safe_read_table


def parse_dbcan(path: str | Path, sample_id: str) -> pd.DataFrame:
    columns = ["sample_id", "family", "substrate_hint"]
    df = safe_read_table(path, columns=columns)
    if df.empty:
        return pd.DataFrame(columns=columns)
    df = df.reindex(columns=columns)
    df["sample_id"] = df["sample_id"].fillna(sample_id)
    return df

