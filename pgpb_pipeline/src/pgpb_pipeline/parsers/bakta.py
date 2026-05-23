"""Bakta summary parser."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pgpb_pipeline.io import safe_read_table


def parse_bakta_summary(path: str | Path, sample_id: str) -> pd.DataFrame:
    columns = ["sample_id", "cds", "rrna", "trna", "ncrna", "pseudogenes", "gff_path", "gbk_path", "faa_path"]
    df = safe_read_table(path, columns=columns)
    if df.empty:
        row = {column: pd.NA for column in columns}
        row["sample_id"] = sample_id
        return pd.DataFrame([row])
    return df.reindex(columns=columns)


def parse_annotation_features(path: str | Path, sample_id: str) -> pd.DataFrame:
    """Parse Bakta/Prokka feature TSV or simple GFF attributes into gene/product rows."""
    path = Path(path)
    columns = ["sample_id", "gene_id", "product"]
    if not path.exists():
        return pd.DataFrame(columns=columns)
    if path.suffix.lower() in {".tsv", ".csv"}:
        df = safe_read_table(path)
        if df.empty:
            return pd.DataFrame(columns=columns)
        lower = {str(col).lower(): col for col in df.columns}
        gene_col = lower.get("gene") or lower.get("locus_tag") or lower.get("id") or lower.get("gene_id")
        product_col = lower.get("product") or lower.get("function") or lower.get("description")
        if product_col is None:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame(
            {
                "sample_id": sample_id,
                "gene_id": df[gene_col].astype(str) if gene_col else df.index.astype(str),
                "product": df[product_col].astype(str),
            }
        )
    rows: list[dict[str, str]] = []
    if path.suffix.lower() in {".gff", ".gff3"}:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 9:
                continue
            attrs = dict(
                item.split("=", 1) for item in parts[8].split(";") if "=" in item
            )
            product = attrs.get("product") or attrs.get("Name") or attrs.get("gene")
            if product:
                rows.append(
                    {
                        "sample_id": sample_id,
                        "gene_id": attrs.get("ID", attrs.get("locus_tag", "")),
                        "product": product.replace("%20", " "),
                    }
                )
    return pd.DataFrame(rows, columns=columns)


def summarize_annotation_features(features_df: pd.DataFrame, sample_id: str, source_dir: str | Path) -> pd.DataFrame:
    """Create a compact annotation summary when no explicit summary table exists."""
    row = {
        "sample_id": sample_id,
        "cds": len(features_df) if not features_df.empty else pd.NA,
        "rrna": pd.NA,
        "trna": pd.NA,
        "ncrna": pd.NA,
        "pseudogenes": pd.NA,
        "gff_path": "",
        "gbk_path": "",
        "faa_path": "",
    }
    source_dir = Path(source_dir)
    for suffix, key in [(".gff3", "gff_path"), (".gff", "gff_path"), (".gbk", "gbk_path"), (".faa", "faa_path")]:
        matches = list(source_dir.glob(f"*{suffix}"))
        if matches and not row[key]:
            row[key] = str(matches[0])
    return pd.DataFrame([row])
