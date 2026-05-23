"""Transparent strain ranking logic."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from pgpb_pipeline.biosafety import top_risk_evidence


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def compute_qc_score(qc_row: pd.Series, weights: dict) -> float:
    completeness = _num(qc_row.get("completeness"))
    contamination = _num(qc_row.get("contamination"))
    n50 = _num(qc_row.get("n50"))
    contigs = _num(qc_row.get("num_contigs"))
    score = completeness * weights["completeness_weight"] - contamination * weights["contamination_weight"]
    if n50 >= weights["n50_good"]:
        score += 2
    if contigs > weights["contig_penalty_threshold"]:
        score -= 2
    return round(max(score, -5.0), 3)


def compute_taxonomy_confidence_score(tax_row: pd.Series, weights: dict) -> float:
    ani = _num(tax_row.get("ani"))
    score = max(0.0, (ani - 90.0) * weights["ani_weight"])
    genus = str(tax_row.get("genus", ""))
    kraken = str(tax_row.get("kraken_top_hit", ""))
    if genus and genus.lower() in kraken.lower():
        score += weights["consensus_bonus"]
    return round(score, 3)


def compute_pgp_trait_score(pgp_df: pd.DataFrame, scoring_config: dict) -> float:
    if pgp_df.empty:
        return 0.0
    weights = scoring_config["pgp_traits"]
    confidence_weight = {
        "high": weights["high_confidence"],
        "medium": weights["medium_confidence"],
        "low": weights["low_confidence"],
    }
    grouped = pgp_df.assign(
        hit_score=pgp_df["confidence"].map(confidence_weight).fillna(weights["low_confidence"])
    ).groupby("trait_category")["hit_score"].sum()
    capped = grouped.clip(upper=weights["category_cap"])
    return round(float(capped.sum()), 3)


def compute_plant_trait_match_score(
    pgp_df: pd.DataFrame,
    target_trait: str,
    scoring_config: dict,
) -> float:
    if pgp_df.empty:
        return 0.0
    text = " ".join(
        pgp_df[["gene_or_marker", "description", "trait_category"]].fillna("").astype(str).agg(" ".join, axis=1)
    ).lower()
    total = 0.0
    targets = [item.strip().lower() for item in str(target_trait).split(",") if item.strip()]
    for target in targets:
        cfg = scoring_config["target_match"].get(target)
        if not cfg:
            continue
        hits = sum(1 for marker in cfg["markers"] if marker.lower() in text)
        total += min(hits * cfg["weight"], 5.0)
    return round(total, 3)


def compute_secondary_metabolite_score(bgc_df: pd.DataFrame, scoring_config: dict) -> float:
    if bgc_df.empty:
        return 0.0
    weights = scoring_config["secondary_metabolites"]
    score = 0.0
    text = " ".join(bgc_df.fillna("").astype(str).agg(" ".join, axis=1)).lower()
    if "siderophore" in text:
        score += weights["siderophore_bonus"]
    if "antimicrobial" in text or "bacteriocin" in text:
        score += weights["antimicrobial_bonus"]
    if "lipopeptide" in text:
        score += weights["lipopeptide_bonus"]
    return round(score, 3)


def compute_uncertainty_penalty(
    qc_row: pd.Series | None,
    tax_row: pd.Series | None,
    annotation_row: pd.Series | None,
    pgp_df: pd.DataFrame,
    scoring_config: dict,
) -> float:
    weights = scoring_config["uncertainty"]
    penalty = 0.0
    if qc_row is None or _num(qc_row.get("completeness")) < 90 or _num(qc_row.get("contamination")) > 5:
        penalty += weights["poor_qc_penalty"]
    if tax_row is None or not str(tax_row.get("genus", "")).strip():
        penalty += weights["no_taxonomy_consensus_penalty"]
    if annotation_row is None or pd.isna(annotation_row.get("cds")):
        penalty += weights["missing_table_penalty"]
    if pgp_df.empty:
        penalty += weights["missing_table_penalty"]
    else:
        penalty += int((pgp_df["confidence"] == "low").sum()) * weights["low_confidence_hit_penalty"]
    return round(float(penalty), 3)


def validation_tests(target_trait: str, pgp_df: pd.DataFrame, risky: bool) -> str:
    tests: list[str] = []
    target = str(target_trait).lower()
    text = " ".join(pgp_df.fillna("").astype(str).agg(" ".join, axis=1)).lower() if not pgp_df.empty else ""
    if "phosphate" in target or "gcd" in text or "pqq" in text:
        tests.append("phosphate solubilization assay")
    if "iaa" in text or "tryptophan" in text:
        tests.append("Salkowski IAA assay")
    if "drought" in target or "acds" in text:
        tests.append("ACC deaminase assay")
    if "siderophore" in text:
        tests.append("CAS siderophore assay")
    if "biocontrol" in target:
        tests.append("dual culture assay against target pathogen")
    if "drought" in target or "salinity" in target:
        tests.append("plant pot experiment under stress")
    if "flagell" in text or "chemotaxis" in text:
        tests.append("colonization assay by re-isolation/qPCR/GFP-tagging")
    if risky:
        tests.append("mandatory biosafety review before any plant assay")
    tests.append("lab/greenhouse validation before field use")
    return "; ".join(dict.fromkeys(tests))


def _top_positive_evidence(pgp_df: pd.DataFrame) -> str:
    if pgp_df.empty:
        return "No PGP markers detected"
    values = [
        str(value)
        for value in pgp_df["gene_or_marker"].dropna().tolist()
        if str(value).strip() and str(value).lower() != "nan"
    ]
    return ";".join(dict.fromkeys(values).keys()) or "No PGP markers detected"


def classify(final_score: float, biosafety_penalty: float, qc_score: float, pgp_score: float) -> tuple[str, str]:
    if biosafety_penalty >= 12:
        return "E", "reject_or_manual_review"
    if biosafety_penalty >= 8:
        return "E", "risky_candidate"
    if final_score >= 24 and qc_score >= 7 and pgp_score >= 5:
        return "A", "strong_candidate"
    if final_score >= 14:
        return "B", "promising_candidate"
    if final_score >= 6:
        return "C", "weak_candidate"
    return "D", "weak_candidate"


def score_samples(
    samples_df: pd.DataFrame,
    qc_df: pd.DataFrame,
    taxonomy_df: pd.DataFrame,
    annotation_df: pd.DataFrame,
    pgp_df: pd.DataFrame,
    bgc_df: pd.DataFrame,
    biosafety_df: pd.DataFrame,
    database_evidence_df: pd.DataFrame | None,
    scoring_config: dict,
) -> pd.DataFrame:
    rows = []
    for _, sample in samples_df.iterrows():
        sample_id = sample["sample_id"]
        qc_row = qc_df[qc_df["sample_id"] == sample_id].iloc[0] if not qc_df[qc_df["sample_id"] == sample_id].empty else None
        tax_row = taxonomy_df[taxonomy_df["sample_id"] == sample_id].iloc[0] if not taxonomy_df[taxonomy_df["sample_id"] == sample_id].empty else None
        ann_row = annotation_df[annotation_df["sample_id"] == sample_id].iloc[0] if not annotation_df[annotation_df["sample_id"] == sample_id].empty else None
        pgp_sub = pgp_df[pgp_df["sample_id"] == sample_id] if not pgp_df.empty else pd.DataFrame()
        bgc_sub = bgc_df[bgc_df["sample_id"] == sample_id] if not bgc_df.empty else pd.DataFrame()
        bio_row = biosafety_df[biosafety_df["sample_id"] == sample_id].iloc[0]
        db_row = None
        if database_evidence_df is not None and not database_evidence_df.empty:
            db_matches = database_evidence_df[database_evidence_df["sample_id"] == sample_id]
            db_row = db_matches.iloc[0] if not db_matches.empty else None

        qc_score = compute_qc_score(qc_row if qc_row is not None else pd.Series(), scoring_config["qc"])
        tax_score = compute_taxonomy_confidence_score(tax_row if tax_row is not None else pd.Series(), scoring_config["taxonomy"])
        pgp_score = compute_pgp_trait_score(pgp_sub, scoring_config)
        match_score = compute_plant_trait_match_score(pgp_sub, sample["target_trait"], scoring_config)
        bgc_score = compute_secondary_metabolite_score(bgc_sub, scoring_config)
        formulation_score = 1.0 if tax_row is not None and str(tax_row.get("genus", "")).lower() in {"bacillus", "paenibacillus"} else 0.0
        uncertainty = compute_uncertainty_penalty(qc_row, tax_row, ann_row, pgp_sub, scoring_config)
        biosafety_penalty = _num(bio_row["biosafety_penalty"])
        database_evidence_score = _num(db_row.get("database_evidence_score")) if db_row is not None else 0.0
        database_evidence_hits = ""
        if db_row is not None and not pd.isna(db_row.get("database_evidence_hits")):
            database_evidence_hits = str(db_row.get("database_evidence_hits", ""))
        final_score = (
            qc_score
            + tax_score
            + pgp_score
            + match_score
            + bgc_score
            + formulation_score
            + database_evidence_score
            - biosafety_penalty
            - uncertainty
        )
        confidence, status = classify(final_score, biosafety_penalty, qc_score, pgp_score)
        taxonomy = " ".join(
            part for part in [str(tax_row.get("genus", "")) if tax_row is not None else "", str(tax_row.get("species", "")) if tax_row is not None else ""] if part and part != "nan"
        )
        rows.append(
            {
                "sample_id": sample_id,
                "plant": sample["plant"],
                "target_trait": sample["target_trait"],
                "taxonomy": taxonomy or "NA",
                "qc_score": qc_score,
                "pgp_trait_score": pgp_score,
                "plant_trait_match_score": match_score,
                "secondary_metabolite_score": bgc_score,
                "database_evidence_score": database_evidence_score,
                "biosafety_penalty": biosafety_penalty,
                "uncertainty_penalty": uncertainty,
                "final_score": round(float(final_score), 3),
                "confidence_level": confidence,
                "recommended_status": status,
                "top_positive_evidence": _top_positive_evidence(pgp_sub),
                "database_evidence_hits": database_evidence_hits,
                "top_risk_evidence": top_risk_evidence(sample_id, biosafety_df),
                "recommended_validation_tests": validation_tests(sample["target_trait"], pgp_sub, biosafety_penalty >= 8),
            }
        )
    return pd.DataFrame(rows).sort_values("final_score", ascending=False)
