"""Recommendation orchestration and explanation generation."""

from __future__ import annotations

from typing import Any

import pandas as pd

from plant_bacteria_match.biosafety import generate_biosafety_warnings
from plant_bacteria_match.models import (
    BacterialStrain,
    BiosafetyProfile,
    PGPTraitProfile,
    PlantProfile,
    Recommendation,
)
from plant_bacteria_match.scoring import score_strain


def _clean_optional(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def _row_to_strain(row: pd.Series) -> BacterialStrain:
    data = {key: _clean_optional(value) for key, value in row.to_dict().items()}
    return BacterialStrain(**data)


def _row_to_trait(row: pd.Series | None) -> PGPTraitProfile | None:
    if row is None:
        return None
    data = {key: _clean_optional(value) for key, value in row.to_dict().items()}
    raw_features = data.get("raw_features") or {}
    if isinstance(raw_features, str):
        raw_features = {"summary": raw_features}
    data["raw_features"] = raw_features
    return PGPTraitProfile(**data)


def _row_to_biosafety(row: pd.Series | None) -> BiosafetyProfile | None:
    if row is None:
        return None
    data = {key: _clean_optional(value) for key, value in row.to_dict().items()}
    return BiosafetyProfile(**data)


def _top_evidence_level(evidence_rows: pd.DataFrame) -> str:
    if evidence_rows.empty:
        return "none"
    order = ["field", "greenhouse", "pot", "in_vitro", "genome_only", "review"]
    levels = evidence_rows["experimental_level"].tolist()
    return min(levels, key=lambda level: order.index(level) if level in order else len(order))


def _strengths(
    strain: BacterialStrain,
    trait_profile: PGPTraitProfile | None,
    evidence_rows: pd.DataFrame,
    selected_problem: str,
) -> list[str]:
    strengths: list[str] = []
    if not evidence_rows.empty:
        strengths.append(f"{_top_evidence_level(evidence_rows)} literature/demo evidence available")
    if strain.is_spore_former:
        strengths.append("spore-former/formulation-friendly candidate")
    if trait_profile is None:
        return strengths
    trait_map = {
        "nitrogen_fixation_score": "nitrogen fixation potential",
        "phosphate_solubilization_score": "phosphate solubilization potential",
        "siderophore_score": "siderophore production potential",
        "iaa_score": "IAA/auxin pathway potential",
        "acc_deaminase_score": "ACC deaminase stress mitigation potential",
        "biocontrol_score": "biocontrol trait profile",
        "stress_tolerance_score": "stress tolerance trait profile",
        "colonization_score": "root colonization traits",
        "secondary_metabolite_score": "secondary metabolite/BGC signal",
    }
    for column, label in trait_map.items():
        if getattr(trait_profile, column) >= 0.75:
            strengths.append(label)
    if selected_problem == "drought" and trait_profile.acc_deaminase_score >= 0.7:
        strengths.append("problem-specific drought support via ACC/stress traits")
    return strengths[:8]


def _missing_data(
    strain: BacterialStrain,
    trait_profile: PGPTraitProfile | None,
    biosafety_profile: BiosafetyProfile | None,
    evidence_rows: pd.DataFrame,
) -> list[str]:
    missing: list[str] = []
    if not strain.genome_accession:
        missing.append("genome accession")
    if trait_profile is None:
        missing.append("PGP trait profile")
    if biosafety_profile is None:
        missing.append("biosafety screening")
    if evidence_rows.empty:
        missing.append("plant/problem-specific literature evidence")
    return missing


def generate_explanation(
    strain: BacterialStrain,
    selected_problem: str,
    score_parts: dict[str, float | str],
    evidence_rows: pd.DataFrame,
    biosafety_profile: BiosafetyProfile | None,
) -> str:
    evidence_level = _top_evidence_level(evidence_rows)
    risk_text = "biosafety profile is missing"
    if biosafety_profile is not None:
        risk_text = f"biosafety penalty {biosafety_profile.biosafety_penalty:.1f}"
    return (
        f"{strain.genus} {strain.species} {strain.strain_name} scored "
        f"{score_parts['final_score']:.1f} for {selected_problem}. "
        f"Main drivers: evidence={score_parts['evidence_score']:.1f}, "
        f"PGP={score_parts['pgp_trait_score']:.1f}, "
        f"problem-specific={score_parts['stress_specific_score']:.1f}, "
        f"plant match={score_parts['plant_match_score']:.1f}; "
        f"top evidence level is {evidence_level}; {risk_text}."
    )


def suggest_validation_tests(
    selected_problem: str,
    trait_profile: PGPTraitProfile | None,
    biosafety_profile: BiosafetyProfile | None,
) -> list[str]:
    tests = ["Confirm taxonomy with GTDB-Tk/FastANI and check culture purity."]
    if selected_problem == "drought":
        tests.extend(["ACC deaminase assay", "EPS/osmotic stress assay", "greenhouse drought trial"])
    elif selected_problem == "salinity":
        tests.extend(["salt tolerance growth curve", "ACC deaminase assay", "greenhouse salinity trial"])
    elif selected_problem == "phosphorus_deficiency":
        tests.extend(["NBRIP/Pikovskaya phosphate solubilization assay", "organic acid profiling"])
    elif selected_problem == "nitrogen_limitation":
        tests.extend(["acetylene reduction or 15N assay", "nifH PCR/annotation review"])
    elif selected_problem == "pathogen_pressure":
        tests.extend(["dual-culture antagonism assay", "siderophore CAS assay", "pathogen challenge trial"])
    elif selected_problem == "cold_stress":
        tests.extend(["low-temperature growth assay", "cold-stress seedling assay"])
    elif selected_problem == "heavy_metals":
        tests.extend(["metal tolerance assay", "metal mobilization/immobilization assay"])
    if trait_profile and trait_profile.colonization_score >= 0.65:
        tests.append("root colonization microscopy/qPCR assay")
    if biosafety_profile is None or biosafety_profile.biosafety_penalty > 0:
        tests.append("AMR/virulence rescreening with AMRFinderPlus/CARD/VFDB before any plant trials")
    return tests


def recommend_strains(
    plant_profile: PlantProfile,
    selected_problem: str,
    strains_df: pd.DataFrame,
    traits_df: pd.DataFrame,
    biosafety_df: pd.DataFrame,
    literature_df: pd.DataFrame,
    strictness: str = "medium",
) -> list[Recommendation]:
    recommendations: list[Recommendation] = []
    traits_by_id = {row["strain_id"]: row for _, row in traits_df.iterrows()}
    biosafety_by_id = {row["strain_id"]: row for _, row in biosafety_df.iterrows()}

    for _, strain_row in strains_df.iterrows():
        strain = _row_to_strain(strain_row)
        trait_profile = _row_to_trait(traits_by_id.get(strain.strain_id))
        biosafety_profile = _row_to_biosafety(biosafety_by_id.get(strain.strain_id))
        evidence_rows = literature_df[literature_df["strain_id"] == strain.strain_id]
        score_parts = score_strain(
            strain,
            trait_profile,
            biosafety_profile,
            literature_df,
            plant_profile.plant_name,
            selected_problem,
            strictness,
        )
        risks = generate_biosafety_warnings(biosafety_profile)
        recommendation = Recommendation(
            strain_id=strain.strain_id,
            final_score=float(score_parts["final_score"]),
            evidence_level=_top_evidence_level(evidence_rows),
            recommendation_class=str(score_parts["recommendation_class"]),
            strengths=_strengths(strain, trait_profile, evidence_rows, selected_problem),
            risks=risks,
            missing_data=_missing_data(strain, trait_profile, biosafety_profile, evidence_rows),
            suggested_validation_tests=suggest_validation_tests(
                selected_problem, trait_profile, biosafety_profile
            ),
            explanation=generate_explanation(
                strain, selected_problem, score_parts, evidence_rows, biosafety_profile
            ),
        )
        recommendations.append(recommendation)

    return sorted(recommendations, key=lambda item: item.final_score, reverse=True)

