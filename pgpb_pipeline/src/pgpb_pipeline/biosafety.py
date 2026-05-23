"""Biosafety risk scoring and flags."""

from __future__ import annotations

import pandas as pd

from pgpb_pipeline.schemas import RISKY_TAXA


def taxonomy_risk(genus: str | float | None, species: str | float | None) -> str:
    genus_norm = str(genus or "").lower()
    species_norm = str(species or "").lower()
    if genus_norm in RISKY_TAXA:
        return "high"
    if genus_norm == "pseudomonas" and "aeruginosa" in species_norm:
        return "high"
    if genus_norm in {"pseudomonas", "burkholderia"} and not species_norm:
        return "medium"
    return "low"


def build_biosafety_summary(
    samples_df: pd.DataFrame,
    taxonomy_df: pd.DataFrame,
    amr_df: pd.DataFrame,
    virulence_df: pd.DataFrame,
    plasmid_df: pd.DataFrame,
    weights: dict,
) -> pd.DataFrame:
    rows = []
    for sample_id in samples_df["sample_id"]:
        tax = taxonomy_df[taxonomy_df["sample_id"] == sample_id]
        genus = tax.iloc[0].get("genus") if not tax.empty else None
        species = tax.iloc[0].get("species") if not tax.empty else None
        risk = taxonomy_risk(genus, species)
        amr_count = len(amr_df[amr_df["sample_id"] == sample_id]) if not amr_df.empty else 0
        vir_count = len(virulence_df[virulence_df["sample_id"] == sample_id]) if not virulence_df.empty else 0
        plasmids = plasmid_df[plasmid_df["sample_id"] == sample_id] if not plasmid_df.empty else pd.DataFrame()
        mobile_amr = bool(
            not plasmids.empty
            and plasmids.get("amr_near_mobile", pd.Series(dtype=str)).astype(str).str.lower().isin(["true", "1", "yes"]).any()
        )
        penalty = amr_count * weights["amr_gene_penalty"] + vir_count * weights["virulence_penalty"]
        if risk == "high":
            penalty += weights["high_risk_taxonomy_penalty"]
        elif risk == "medium":
            penalty += weights["medium_risk_taxonomy_penalty"]
        if mobile_amr:
            penalty += weights["mobile_amr_penalty"]
        rows.append(
            {
                "sample_id": sample_id,
                "amr_gene_count": amr_count,
                "virulence_factor_count": vir_count,
                "taxonomy_risk": risk,
                "mobile_amr": mobile_amr,
                "biosafety_penalty": round(float(penalty), 3),
            }
        )
    return pd.DataFrame(rows)


def top_risk_evidence(sample_id: str, biosafety_df: pd.DataFrame) -> str:
    row = biosafety_df[biosafety_df["sample_id"] == sample_id]
    if row.empty:
        return "Missing biosafety summary"
    data = row.iloc[0]
    risks: list[str] = []
    if data["amr_gene_count"] > 0:
        risks.append("AMR genes")
    if data["virulence_factor_count"] > 0:
        risks.append("virulence factors")
    if data["taxonomy_risk"] in {"high", "medium"}:
        risks.append(f"{data['taxonomy_risk']} risk taxonomy")
    if data["mobile_amr"]:
        risks.append("mobile AMR")
    return "; ".join(risks) if risks else "No major mock biosafety risks"

