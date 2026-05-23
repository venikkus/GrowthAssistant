"""BUSCO short summary parser."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


def parse_busco_summary(path: str | Path, sample_id: str) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        text = ""
    else:
        text = path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(r"C:(?P<c>[\d.]+)%\[S:(?P<s>[\d.]+)%,D:(?P<d>[\d.]+)%\],F:(?P<f>[\d.]+)%,M:(?P<m>[\d.]+)%")
    match = pattern.search(text)
    if not match:
        values = {"c": pd.NA, "s": pd.NA, "d": pd.NA, "f": pd.NA, "m": pd.NA}
    else:
        values = match.groupdict()
    return pd.DataFrame(
        [
            {
                "sample_id": sample_id,
                "busco_complete": values["c"],
                "busco_single": values["s"],
                "busco_duplicated": values["d"],
                "busco_fragmented": values["f"],
                "busco_missing": values["m"],
            }
        ]
    )

