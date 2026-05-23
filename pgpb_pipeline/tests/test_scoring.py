import pandas as pd

from pgpb_pipeline.biosafety import taxonomy_risk
from pgpb_pipeline.scoring import (
    compute_plant_trait_match_score,
    compute_qc_score,
    compute_secondary_metabolite_score,
)


def test_qc_rewards_complete_low_contamination_genome() -> None:
    good = pd.Series({"completeness": 98, "contamination": 0.5, "n50": 150000, "num_contigs": 40})
    poor = pd.Series({"completeness": 82, "contamination": 8, "n50": 12000, "num_contigs": 500})
    weights = {"completeness_weight": 0.08, "contamination_weight": 0.6, "n50_good": 100000, "contig_penalty_threshold": 200}
    assert compute_qc_score(good, weights) > compute_qc_score(poor, weights)


def test_target_match_rewards_phosphate_markers() -> None:
    pgp = pd.DataFrame(
        [
            {"gene_or_marker": "gcd", "description": "glucose dehydrogenase", "trait_category": "phosphate_solubilization"},
            {"gene_or_marker": "pqqC", "description": "pqq biosynthesis", "trait_category": "phosphate_solubilization"},
        ]
    )
    cfg = {"target_match": {"phosphate_solubilization": {"markers": ["gcd", "pqq"], "weight": 1.4}}}
    assert compute_plant_trait_match_score(pgp, "phosphate_solubilization", cfg) > 0


def test_secondary_metabolites_reward_siderophore_and_antimicrobial() -> None:
    bgc = pd.DataFrame([{"product": "siderophore antimicrobial peptide", "potential_role": "siderophore"}])
    cfg = {"secondary_metabolites": {"siderophore_bonus": 1.0, "antimicrobial_bonus": 1.2, "lipopeptide_bonus": 1.0}}
    assert compute_secondary_metabolite_score(bgc, cfg) == 2.2


def test_risky_taxonomy_detected() -> None:
    assert taxonomy_risk("Enterobacter", "cloacae") == "high"
    assert taxonomy_risk("Bacillus", "velezensis") == "low"

