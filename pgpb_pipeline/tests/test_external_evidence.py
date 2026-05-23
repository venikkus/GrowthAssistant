import pandas as pd

from pgpb_pipeline.external_evidence import normalize_plant, summarize_database_evidence


def test_normalize_plant_aliases() -> None:
    assert normalize_plant("Пшеница") == "wheat"
    assert normalize_plant("Томаты (Solanum lycopersicum)") == "tomato"


def test_database_evidence_matches_plant_and_taxon() -> None:
    samples = pd.DataFrame(
        [{"sample_id": "s1", "plant": "wheat", "target_trait": "drought", "condition": "dry"}]
    )
    taxonomy = pd.DataFrame([{"sample_id": "s1", "genus": "Bacillus", "species": "velezensis"}])
    evidence = pd.DataFrame(
        [
            {
                "source": "GloBI",
                "plant": "wheat",
                "bacterium": "Bacillus velezensis",
                "genus": "Bacillus",
                "evidence_score": 1.0,
                "evidence_type": "association",
            },
            {
                "source": "PubMed",
                "plant": "wheat",
                "bacterium": "Bacillus velezensis",
                "genus": "Bacillus",
                "evidence_score": 4.0,
                "evidence_type": "greenhouse",
            },
        ]
    )
    summary = summarize_database_evidence(samples, taxonomy, evidence)
    assert summary.loc[0, "database_evidence_score"] == 5.0
    assert "PubMed" in summary.loc[0, "database_evidence_hits"]

