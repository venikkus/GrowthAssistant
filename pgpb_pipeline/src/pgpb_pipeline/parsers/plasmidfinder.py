"""PlasmidFinder parser."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pgpb_pipeline.io import safe_read_table


def parse_plasmidfinder(path: str | Path, sample_id: str) -> pd.DataFrame:
    columns = ["sample_id", "replicon", "mobility_type", "conjugative", "amr_near_mobile"]
    df = safe_read_table(path, columns=columns).reindex(columns=columns)
    if df.empty:
        return pd.DataFrame(columns=columns)
    df["sample_id"] = df["sample_id"].fillna(sample_id)
    return df[df["replicon"].notna() & (df["replicon"].astype(str).str.strip() != "")]

