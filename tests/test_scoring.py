import pandas as pd

from plant_bacteria_match.models import BacterialStrain, BiosafetyProfile, PGPTraitProfile
from plant_bacteria_match.scoring import (
    classify_recommendation,
    compute_evidence_score,
    compute_stress_specific_score,
    compute_uncertainty_penalty,
    score_strain,
)


def test_pathogen_flag_prevents_a_b_recommendation() -> None:
    profile = BiosafetyProfile(
        strain_id="x",
        pathogen_flag=True,
        virulence_gene_count=1,
        biosafety_penalty=12,
    )
    assert classify_recommendation(30, profile, 5) not in {"A", "B"}


def test_high_pgp_but_high_biosafety_risk_becomes_e_or_d() -> None:
    strain = BacterialStrain(
        strain_id="x",
        genus="Serratia",
        species="marcescens",
        strain_name="SM",
        genome_accession="GCF_X",
        taxonomy_confidence=0.95,
    )
    trait = PGPTraitProfile(
        strain_id="x",
        nitrogen_fixation_score=1,
        phosphate_solubilization_score=1,
        siderophore_score=1,
        iaa_score=1,
        acc_deaminase_score=1,
        biocontrol_score=1,
        stress_tolerance_score=1,
        colonization_score=1,
        secondary_metabolite_score=1,
    )
    biosafety = BiosafetyProfile(
        strain_id="x",
        amr_gene_count=5,
        virulence_gene_count=5,
        pathogen_flag=True,
        risky_genus_flag=True,
        plasmid_amr_flag=True,
    )
    evidence = pd.DataFrame(
        [
            {
                "strain_id": "x",
                "plant_name": "wheat",
                "experimental_level": "field",
                "effect_direction": "positive",
                "stress_or_pathogen": "drought",
                "confidence_score": 1.0,
            }
        ]
    )
    score = score_strain(strain, trait, biosafety, evidence, "wheat", "drought")
    assert score["recommendation_class"] in {"D", "E"}


def test_field_evidence_gives_higher_score_than_genome_only() -> None:
    evidence = pd.DataFrame(
        [
            {
                "strain_id": "field",
                "plant_name": "wheat",
                "experimental_level": "field",
                "effect_direction": "positive",
                "stress_or_pathogen": "drought",
                "confidence_score": 1.0,
            },
            {
                "strain_id": "genome",
                "plant_name": "wheat",
                "experimental_level": "genome_only",
                "effect_direction": "positive",
                "stress_or_pathogen": "drought",
                "confidence_score": 1.0,
            },
        ]
    )
    assert compute_evidence_score(evidence, "field", "wheat", "drought") > compute_evidence_score(
        evidence, "genome", "wheat", "drought"
    )


def test_drought_stress_boosts_acc_stress_colonization_traits() -> None:
    high = PGPTraitProfile(
        strain_id="high",
        acc_deaminase_score=0.9,
        stress_tolerance_score=0.9,
        colonization_score=0.9,
    )
    low = PGPTraitProfile(
        strain_id="low",
        acc_deaminase_score=0.1,
        stress_tolerance_score=0.1,
        colonization_score=0.1,
    )
    assert compute_stress_specific_score(high, "drought") > compute_stress_specific_score(
        low, "drought"
    )


def test_missing_genome_literature_biosafety_increases_uncertainty_penalty() -> None:
    strain_missing = BacterialStrain(
        strain_id="x",
        genus="Bacillus",
        species="subtilis",
        strain_name="BS",
        taxonomy_confidence=0.7,
    )
    strain_complete = BacterialStrain(
        strain_id="y",
        genus="Bacillus",
        species="subtilis",
        strain_name="BS",
        genome_accession="GCF_Y",
        taxonomy_confidence=0.99,
    )
    trait = PGPTraitProfile(strain_id="y")
    biosafety = BiosafetyProfile(strain_id="y")
    evidence = pd.DataFrame([{"strain_id": "y"}])
    assert compute_uncertainty_penalty(strain_missing, None, None, pd.DataFrame()) > (
        compute_uncertainty_penalty(strain_complete, trait, biosafety, evidence)
    )

