"""Normalize external plant-bacteria evidence tables from BacDive, PubMed, and GloBI."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from pgpb_pipeline.io import safe_read_table

PLANT_ALIASES = {
    "wheat": {"wheat", "пшеница", "triticum aestivum"},
    "tomato": {"tomato", "tomatoes", "томаты", "томат", "solanum lycopersicum"},
    "soybean": {"soybean", "соя", "glycine max"},
    "potato": {"potato", "картофель", "solanum tuberosum"},
    "sunflower": {"sunflower", "подсолнечник", "helianthus annuus"},
    "rye": {"rye", "рожь", "secale cereale"},
    "pea": {"pea", "горох", "pisum sativum"},
    "rice": {"rice", "рис", "oryza sativa"},
    "barley": {"barley", "ячмень", "hordeum vulgare"},
    "bean": {"bean", "фасоль", "phaseolus vulgaris"},
}

EVIDENCE_SCORES = {
    "field": 5.0,
    "greenhouse": 4.0,
    "pot": 3.0,
    "in vitro": 2.0,
    "in_vitro": 2.0,
    "database": 1.0,
    "association": 1.0,
}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).strip()).lower()


def normalize_plant(value: object) -> str:
    text = normalize_text(value)
    for canonical, aliases in PLANT_ALIASES.items():
        if any(alias in text for alias in aliases):
            return canonical
    return text


def extract_latin_name(value: object) -> str:
    text = str(value)
    match = re.search(r"\(([^)]+)\)", text)
    return match.group(1).strip() if match else ""


def extract_genus(taxon: object) -> str:
    text = str(taxon).strip()
    first = text.split()[0] if text else ""
    return first if re.match(r"^[A-Z][a-zA-Z-]+$", first) else ""


def _empty() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "source",
            "plant",
            "plant_latin",
            "bacterium",
            "genus",
            "evidence_type",
            "evidence_score",
            "condition",
            "mechanism",
            "reference",
            "description",
        ]
    )


def parse_bacdive(path: str | Path) -> pd.DataFrame:
    df = safe_read_table(path)
    if df.empty:
        return _empty()
    rows = []
    for _, row in df.iterrows():
        bacterium = str(row.get("Штамм бактерии", ""))
        rows.append(
            {
                "source": "BacDive",
                "plant": normalize_plant(row.get("Растение (RU)", "")),
                "plant_latin": "",
                "bacterium": bacterium,
                "genus": str(row.get("Род бактерии", "")) or extract_genus(bacterium),
                "evidence_type": "database",
                "evidence_score": 1.0,
                "condition": "",
                "mechanism": "",
                "reference": str(row.get("BacDive ID", "")),
                "description": "; ".join(
                    part
                    for part in [
                        str(row.get("Источник изоляции", "")),
                        f"BSL={row.get('Класс опасности (BSL)', '')}",
                        str(row.get("Источник базы", "")),
                    ]
                    if part and part != "nan"
                ),
            }
        )
    return pd.DataFrame(rows)


def parse_pubmed_pgpr(path: str | Path) -> pd.DataFrame:
    df = safe_read_table(path)
    if df.empty:
        return _empty()
    rows = []
    for _, row in df.iterrows():
        evidence_type = normalize_text(row.get("experimental type", "")) or "database"
        bacterium = str(row.get("bacterial strain", ""))
        rows.append(
            {
                "source": "PubMed",
                "plant": normalize_plant(row.get("plant species", "")),
                "plant_latin": extract_latin_name(row.get("plant species", "")),
                "bacterium": bacterium,
                "genus": extract_genus(bacterium),
                "evidence_type": evidence_type,
                "evidence_score": EVIDENCE_SCORES.get(evidence_type, 1.0),
                "condition": str(row.get("condition", "")),
                "mechanism": str(row.get("mechanism", "")),
                "reference": str(row.get("article DOI", "")),
                "description": str(row.get("effect", "")),
            }
        )
    return pd.DataFrame(rows)


def parse_globi(path: str | Path) -> pd.DataFrame:
    df = safe_read_table(path)
    if df.empty:
        return _empty()
    rows = []
    for _, row in df.iterrows():
        bacterium = str(row.get("Ассоциированная бактерия", ""))
        rows.append(
            {
                "source": "GloBI",
                "plant": normalize_plant(row.get("Растение (RU)", "")),
                "plant_latin": str(row.get("Растение (Latin)", "")),
                "bacterium": bacterium,
                "genus": str(row.get("Род бактерии", "")) or extract_genus(bacterium),
                "evidence_type": "association",
                "evidence_score": 1.0,
                "condition": "",
                "mechanism": str(row.get("Тип связи в базе", "")),
                "reference": str(row.get("Источник данных", "")),
                "description": "plant-bacteria association database record",
            }
        )
    return pd.DataFrame(rows)


def load_external_evidence(data_dir: str | Path) -> pd.DataFrame:
    data_dir = Path(data_dir)
    frames = [
        parse_bacdive(data_dir / "bacdive_bruteforce_strains.tsv"),
        parse_pubmed_pgpr(data_dir / "pubmed_live_pgpr_table.tsv"),
        parse_globi(data_dir / "ready_plant_bacteria_associations.tsv"),
    ]
    combined = pd.concat(frames, ignore_index=True)
    if combined.empty:
        return _empty()
    combined["genus"] = combined["genus"].fillna("").astype(str)
    combined["bacterium"] = combined["bacterium"].fillna("").astype(str)
    return combined


def summarize_database_evidence(
    samples_df: pd.DataFrame,
    taxonomy_df: pd.DataFrame,
    evidence_df: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    if evidence_df.empty:
        for _, sample in samples_df.iterrows():
            rows.append(
                {
                    "sample_id": sample["sample_id"],
                    "database_evidence_score": 0.0,
                    "database_evidence_hits": "",
                }
            )
        return pd.DataFrame(rows)

    for _, sample in samples_df.iterrows():
        sample_id = sample["sample_id"]
        plant = normalize_plant(sample["plant"])
        tax = taxonomy_df[taxonomy_df["sample_id"] == sample_id]
        genus = str(tax.iloc[0].get("genus", "")) if not tax.empty else ""
        species = str(tax.iloc[0].get("species", "")) if not tax.empty else ""
        taxon = " ".join(part for part in [genus, species] if part and part != "nan").lower()
        matched = evidence_df[
            (evidence_df["plant"] == plant)
            & (
                evidence_df["genus"].str.lower().eq(genus.lower())
                | evidence_df["bacterium"].str.lower().str.contains(re.escape(taxon), na=False)
            )
        ].copy()
        if matched.empty:
            rows.append(
                {
                    "sample_id": sample_id,
                    "database_evidence_score": 0.0,
                    "database_evidence_hits": "",
                }
            )
            continue
        source_bonus = matched.groupby("source")["evidence_score"].max().sum()
        score = min(float(source_bonus), 5.0)
        hits = matched.sort_values("evidence_score", ascending=False).head(5)
        hit_text = "; ".join(
            f"{row.source}:{row.bacterium}({row.evidence_type})" for row in hits.itertuples(index=False)
        )
        rows.append(
            {
                "sample_id": sample_id,
                "database_evidence_score": round(score, 3),
                "database_evidence_hits": hit_text,
            }
        )
    return pd.DataFrame(rows)

