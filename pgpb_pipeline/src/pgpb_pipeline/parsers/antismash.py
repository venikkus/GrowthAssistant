"""antiSMASH summary parser."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pgpb_pipeline.io import safe_read_table


def parse_antismash(path: str | Path, sample_id: str) -> pd.DataFrame:
    columns = ["sample_id", "region", "bgc_type", "product", "similarity", "coordinates", "potential_role"]
    df = safe_read_table(path, columns=columns)
    if df.empty:
        return pd.DataFrame(columns=columns)
    df = df.reindex(columns=columns)
    df["sample_id"] = df["sample_id"].fillna(sample_id)
    return df

