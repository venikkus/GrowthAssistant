"""VFDB parser."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pgpb_pipeline.io import safe_read_table


def parse_vfdb(path: str | Path, sample_id: str) -> pd.DataFrame:
    columns = ["sample_id", "virulence_factor", "source_database", "risk_level"]
    df = safe_read_table(path, columns=columns).reindex(columns=columns)
    if df.empty:
        return pd.DataFrame(columns=columns)
    df["sample_id"] = df["sample_id"].fillna(sample_id)
    return df[df["virulence_factor"].notna() & (df["virulence_factor"].astype(str).str.strip() != "")]

