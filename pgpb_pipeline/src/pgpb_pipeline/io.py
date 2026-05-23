"""I/O helpers used by CLI scripts and Snakemake rules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from pgpb_pipeline.schemas import Sample


def read_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def read_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as handle:
            return pd.DataFrame(json.load(handle))
    sep = "\t" if path.suffix.lower() in {".tsv", ".tab"} else ","
    return pd.read_csv(path, sep=sep)


def safe_read_table(path: str | Path, columns: list[str] | None = None) -> pd.DataFrame:
    try:
        df = read_table(path)
    except Exception:
        df = pd.DataFrame()
    if df.empty and columns:
        return pd.DataFrame(columns=columns)
    return df


def write_table(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, sep="\t", index=False)


def load_samples(path: str | Path) -> list[Sample]:
    df = read_table(path)
    return [Sample(**row.to_dict()) for _, row in df.iterrows()]


def load_samples_df(path: str | Path) -> pd.DataFrame:
    return read_table(path)

