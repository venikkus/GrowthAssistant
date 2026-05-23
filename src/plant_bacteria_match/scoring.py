"""Transparent recommendation scoring."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from plant_bacteria_match.biosafety import compute_biosafety_penalty
from plant_bacteria_match.models import BacterialStrain, BiosafetyProfile, PGPTraitProfile

EVIDENCE_LEVEL_SCORES = {
    "field": 5.0,
    "greenhouse": 4.0,
    "pot": 3.0,
    "in_vitro": 2.0,
    "genome_only": 1.0,
    "review": 1.0,
}

TRAIT_COLUMNS = [
    "nitrogen_fixation_score",
    "phosphate_solubilization_score",
    "siderophore_score",
    "iaa_score",
    "acc_deaminase_score",
    "biocontrol_score",
    "stress_tolerance_score",
    "colonization_score",
    "secondary_metabolite_score",
]


def _matches_problem(value: Any, selected_problem: str) -> bool:
    value_norm = str(value or "").lower()
    problem_norm = selected_problem.lower()
    aliases = {
        "pathogen_pressure": ["pathogen", "fusarium", "sclerotinia", "biocontrol"],
        "phosphorus_deficiency": ["phosphorus", "phosphate"],
        "nitrogen_limitation": ["nitrogen"],
        "drought": ["drought"],
        "salinity": ["salinity", "salt"],
        "cold_stress": ["cold"],
        "heavy_metals": ["metal", "cadmium", "arsenic"],
    }
    terms = aliases.get(problem_norm, [problem_norm])
    return any(term in value_norm for term in terms)


def compute_evidence_score(
    evidence_df: pd.DataFrame,
    strain_id: str,
    plant_name: str,
    selected_problem: str,
) -> float:
    if evidence_df.empty:
        return 0.0
    rows = evidence_df[evidence_df["strain_id"] == strain_id].copy()
    if rows.empty:
        return 0.0
    plant_norm = plant_name.lower()
    rows["base"] = rows["experimental_level"].map(EVIDENCE_LEVEL_SCORES).fillna(0.0)
    rows["direction_weight"] = rows["effect_direction"].map(
        {"positive": 1.0, "mixed": 0.45, "neutral": 0.15, "negative": -1.0}
    ).fillna(0.0)
    rows["plant_bonus"] = rows["plant_name"].str.lower().eq(plant_norm).map({True: 1.0, False: 0.0})
    rows["problem_bonus"] = rows["stress_or_pathogen"].map(
        lambda value: 1.0 if _matches_problem(value, selected_problem) else 0.0
    )
    rows["weighted"] = (
        rows["base"] * rows["direction_weight"] + rows["plant_bonus"] + rows["problem_bonus"]
    ) * rows["confidence_score"].fillna(0.7)
    return round(float(rows["weighted"].max()), 3)


def compute_plant_match_score(
    strain: BacterialStrain,
    evidence_df: pd.DataFrame,
    plant_name: str,
) -> float:
    score = 0.0
    if (strain.host_plant or "").strip().lower() == plant_name.strip().lower():
        score += 3.0
    if not evidence_df.empty:
        rows = evidence_df[
            (evidence_df["strain_id"] == strain.strain_id)
            & (evidence_df["plant_name"].str.lower() == plant_name.lower())
        ]
        if not rows.empty:
            score += 2.0
    return score


def compute_pgp_trait_score(trait_profile: PGPTraitProfile | None) -> float:
    if trait_profile is None:
        return 0.0
    values = [getattr(trait_profile, column) for column in TRAIT_COLUMNS]
    return round(float(sum(values) / len(values) * 5.0), 3)


def compute_stress_specific_score(
    trait_profile: PGPTraitProfile | None,
    selected_problem: str,
) -> float:
    if trait_profile is None:
        return 0.0
    problem = selected_problem.lower()
    if problem == "drought":
        value = (
            0.35 * trait_profile.acc_deaminase_score
            + 0.40 * trait_profile.stress_tolerance_score
            + 0.25 * trait_profile.colonization_score
        )
    elif problem == "salinity":
        value = 0.65 * trait_profile.stress_tolerance_score + 0.35 * trait_profile.acc_deaminase_score
    elif problem == "phosphorus_deficiency":
        value = trait_profile.phosphate_solubilization_score
    elif problem == "nitrogen_limitation":
        value = trait_profile.nitrogen_fixation_score
    elif problem == "pathogen_pressure":
        value = (
            0.4 * trait_profile.biocontrol_score
            + 0.25 * trait_profile.siderophore_score
            + 0.35 * trait_profile.secondary_metabolite_score
        )
    elif problem == "cold_stress":
        value = 0.75 * trait_profile.stress_tolerance_score + 0.25 * trait_profile.colonization_score
    elif problem == "heavy_metals":
        value = 0.8 * trait_profile.stress_tolerance_score + 0.2 * trait_profile.siderophore_score
    else:
        value = trait_profile.stress_tolerance_score
    return round(float(value * 5.0), 3)


def compute_formulation_score(strain: BacterialStrain) -> float:
    score = 0.0
    if strain.genus.lower() in {"bacillus", "paenibacillus"}:
        score += 1.0
    if strain.is_spore_former:
        score += 1.0
    if strain.formulation_notes and "stable" in strain.formulation_notes.lower():
        score += 0.5
    return score


def compute_uncertainty_penalty(
    strain: BacterialStrain,
    trait_profile: PGPTraitProfile | None,
    biosafety_profile: BiosafetyProfile | None,
    evidence_rows: pd.DataFrame,
) -> float:
    penalty = 0.0
    if not strain.genome_accession or str(strain.genome_accession).lower() == "nan":
        penalty += 1.5
    if trait_profile is None:
        penalty += 2.0
    if biosafety_profile is None:
        penalty += 3.0
    if evidence_rows.empty:
        penalty += 1.5
    if math.isnan(float(strain.taxonomy_confidence)):
        penalty += 1.0
    elif strain.taxonomy_confidence < 0.85:
        penalty += 1.0
    return round(penalty, 3)


def classify_recommendation(
    final_score: float,
    biosafety_profile: BiosafetyProfile | None,
    evidence_score: float,
) -> str:
    if biosafety_profile is None:
        return "D" if final_score >= 8 else "E"
    high_risk = (
        biosafety_profile.pathogen_flag
        or biosafety_profile.virulence_gene_count >= 3
        or biosafety_profile.biosafety_penalty >= 8
    )
    moderate_risk = biosafety_profile.risky_genus_flag or biosafety_profile.virulence_gene_count > 0
    if high_risk:
        return "E" if final_score < 12 else "D"
    if final_score >= 17 and evidence_score >= 4 and not moderate_risk:
        return "A"
    if final_score >= 12 and evidence_score >= 2 and biosafety_profile.biosafety_penalty < 6:
        return "B" if not moderate_risk else "C"
    if final_score >= 8:
        return "C"
    if final_score >= 4:
        return "D"
    return "E"


def score_strain(
    strain: BacterialStrain,
    trait_profile: PGPTraitProfile | None,
    biosafety_profile: BiosafetyProfile | None,
    evidence_df: pd.DataFrame,
    plant_name: str,
    selected_problem: str,
    strictness: str = "medium",
) -> dict[str, float | str]:
    evidence_rows = evidence_df[evidence_df["strain_id"] == strain.strain_id]
    evidence_score = compute_evidence_score(evidence_df, strain.strain_id, plant_name, selected_problem)
    plant_match_score = compute_plant_match_score(strain, evidence_df, plant_name)
    pgp_trait_score = compute_pgp_trait_score(trait_profile)
    stress_specific_score = compute_stress_specific_score(trait_profile, selected_problem)
    colonization_score = (trait_profile.colonization_score * 3.0) if trait_profile else 0.0
    formulation_score = compute_formulation_score(strain)
    uncertainty_penalty = compute_uncertainty_penalty(
        strain, trait_profile, biosafety_profile, evidence_rows
    )
    biosafety_penalty = 0.0
    if biosafety_profile:
        biosafety_penalty = compute_biosafety_penalty(
            biosafety_profile.amr_gene_count,
            biosafety_profile.virulence_gene_count,
            biosafety_profile.pathogen_flag,
            biosafety_profile.risky_genus_flag,
            biosafety_profile.plasmid_amr_flag,
            strictness,
        )
        biosafety_profile.biosafety_penalty = biosafety_penalty
    final_score = (
        plant_match_score
        + evidence_score
        + pgp_trait_score
        + stress_specific_score
        + colonization_score
        + formulation_score
        - biosafety_penalty
        - uncertainty_penalty
    )
    return {
        "final_score": round(final_score, 3),
        "evidence_score": evidence_score,
        "plant_match_score": plant_match_score,
        "pgp_trait_score": pgp_trait_score,
        "stress_specific_score": stress_specific_score,
        "colonization_score": round(colonization_score, 3),
        "formulation_score": formulation_score,
        "biosafety_penalty": biosafety_penalty,
        "uncertainty_penalty": uncertainty_penalty,
        "recommendation_class": classify_recommendation(final_score, biosafety_profile, evidence_score),
    }

