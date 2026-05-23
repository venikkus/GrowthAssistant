"""Input helpers for demo and imported result tables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _read_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as handle:
            data: Any = json.load(handle)
        return pd.DataFrame(data)
    if path.suffix.lower() in {".tsv", ".tab"}:
        return pd.read_csv(path, sep="\t")
    return pd.read_csv(path)


def load_strains(path: str | Path) -> pd.DataFrame:
    return _read_table(path)


def load_pgp_traits(path: str | Path) -> pd.DataFrame:
    return _read_table(path)


def load_biosafety(path: str | Path) -> pd.DataFrame:
    return _read_table(path)


def load_literature_evidence(path: str | Path) -> pd.DataFrame:
    return _read_table(path)


def load_plant_profiles(path: str | Path) -> pd.DataFrame:
    df = _read_table(path)
    for column in [
        "target_stresses",
        "target_pathogens",
        "target_nutrient_limits",
    ]:
        if column in df.columns:
            df[column] = df[column].fillna("").map(
                lambda value: [item.strip() for item in str(value).split(";") if item.strip()]
            )
    return df


def load_demo_dataset(data_dir: str | Path) -> dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)
    return {
        "strains": load_strains(data_dir / "strains.csv"),
        "pgp_traits": load_pgp_traits(data_dir / "pgp_traits.csv"),
        "biosafety": load_biosafety(data_dir / "biosafety.csv"),
        "literature_evidence": load_literature_evidence(data_dir / "literature_evidence.csv"),
        "plant_profiles": load_plant_profiles(data_dir / "plant_profiles.csv"),
    }

