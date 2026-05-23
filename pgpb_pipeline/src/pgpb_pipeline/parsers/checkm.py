"""CheckM parser."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pgpb_pipeline.io import safe_read_table


def parse_checkm(path: str | Path, sample_id: str) -> pd.DataFrame:
    df = safe_read_table(path)
    if df.empty:
        return pd.DataFrame([{"sample_id": sample_id, "completeness": pd.NA, "contamination": pd.NA}])
    row = df.iloc[0].to_dict()
    return pd.DataFrame(
        [
            {
                "sample_id": sample_id,
                "completeness": row.get("completeness") or row.get("Completeness"),
                "contamination": row.get("contamination") or row.get("Contamination"),
            }
        ]
    )

