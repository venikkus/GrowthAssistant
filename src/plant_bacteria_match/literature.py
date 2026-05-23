"""Literature-mining stubs for the MVP."""

from __future__ import annotations

import re

from plant_bacteria_match.models import LiteratureEvidence


def normalize_plant_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def extract_evidence_stub(text: str) -> LiteratureEvidence:
    """Return a deterministic placeholder extraction for demos/tests.

    TODO: PubMed/EuropePMC/Semantic Scholar search -> abstract retrieval ->
    LLM extraction -> curated evidence table with confidence calibration.
    """
    return LiteratureEvidence(
        evidence_id="stub-001",
        plant_name="unknown",
        strain_id="unknown",
        bacterial_taxon="unknown bacterium",
        effect_type="growth_promotion",
        stress_or_pathogen="unknown",
        experimental_level="review",
        effect_direction="mixed",
        effect_size=None,
        mechanism="stub extraction from supplied text",
        citation=text[:120] if text else "manual stub",
        confidence_score=0.2,
    )


def build_literature_query(plant_name: str, problem: str) -> str:
    terms = {
        "drought": "drought OR water deficit",
        "salinity": "salinity OR salt stress",
        "phosphorus_deficiency": "phosphate solubilization OR phosphorus deficiency",
        "nitrogen_limitation": "nitrogen fixation OR diazotroph",
        "pathogen_pressure": "biocontrol OR pathogen suppression",
        "cold_stress": "cold stress",
        "heavy_metals": "heavy metal tolerance OR phytoremediation",
    }
    return f'("{plant_name}" AND bacteria AND ({terms.get(problem, problem)}))'

