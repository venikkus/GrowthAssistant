"""QUAST parser."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pgpb_pipeline.io import safe_read_table


def parse_quast_report(path: str | Path, sample_id: str) -> pd.DataFrame:
    df = safe_read_table(path)
    if df.empty:
        return pd.DataFrame(
            [{"sample_id": sample_id, "total_length": pd.NA, "num_contigs": pd.NA, "n50": pd.NA, "gc": pd.NA}]
        )
    row = df.iloc[0].to_dict()
    return pd.DataFrame(
        [
            {
                "sample_id": sample_id,
                "total_length": row.get("total_length") or row.get("Total length"),
                "num_contigs": row.get("num_contigs") or row.get("# contigs"),
                "n50": row.get("N50"),
                "gc": row.get("GC") or row.get("GC (%)"),
            }
        ]
    )

