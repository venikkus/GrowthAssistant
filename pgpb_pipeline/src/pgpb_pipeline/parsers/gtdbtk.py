"""GTDB-Tk style taxonomy parser."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pgpb_pipeline.io import safe_read_table


def parse_taxonomy_summary(path: str | Path, sample_id: str) -> pd.DataFrame:
    columns = [
        "sample_id",
        "gtdb_classification",
        "genus",
        "species",
        "closest_reference",
        "ani",
        "mash_distance",
        "kraken_top_hit",
    ]
    df = safe_read_table(path, columns=columns)
    if df.empty:
        row = {column: pd.NA for column in columns}
        row["sample_id"] = sample_id
        return pd.DataFrame([row])
    return df.reindex(columns=columns)
