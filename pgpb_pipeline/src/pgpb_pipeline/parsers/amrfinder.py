"""AMRFinderPlus parser."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pgpb_pipeline.io import safe_read_table


def parse_amrfinder(path: str | Path, sample_id: str) -> pd.DataFrame:
    columns = ["sample_id", "gene", "drug_class", "identity", "coverage"]
    raw = safe_read_table(path, columns=columns)
    if not raw.empty and not set(columns).issubset(raw.columns):
        lower = {str(col).lower(): col for col in raw.columns}
        raw = pd.DataFrame(
            {
                "sample_id": sample_id,
                "gene": raw.get(lower.get("gene symbol", ""), raw.get(lower.get("gene", ""), "")),
                "drug_class": raw.get(lower.get("class", ""), raw.get(lower.get("subclass", ""), "")),
                "identity": raw.get(lower.get("% identity", ""), raw.get(lower.get("identity", ""), "")),
                "coverage": raw.get(lower.get("% coverage of reference sequence", ""), raw.get(lower.get("coverage", ""), "")),
            }
        )
    df = raw.reindex(columns=columns)
    if df.empty:
        return pd.DataFrame(columns=columns)
    df["sample_id"] = df["sample_id"].fillna(sample_id)
    return df[df["gene"].notna() & (df["gene"].astype(str).str.strip() != "")]
