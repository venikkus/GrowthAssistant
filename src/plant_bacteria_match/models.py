"""Pydantic data models for PlantBacteriaMatch."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PlantProfile(BaseModel):
    plant_name: str
    scientific_name: str
    crop_group: str
    target_stresses: list[str] = Field(default_factory=list)
    target_pathogens: list[str] = Field(default_factory=list)
    target_nutrient_limits: list[str] = Field(default_factory=list)
    region: str | None = None
    soil_pH: float | None = None
    notes: str | None = None


class BacterialStrain(BaseModel):
    strain_id: str
    genus: str
    species: str
    strain_name: str
    isolation_source: str | None = None
    host_plant: str | None = None
    genome_accession: str | None = None
    taxonomy_confidence: float = 0.0
    formulation_notes: str | None = None
    is_spore_former: bool = False
    notes: str | None = None


class PGPTraitProfile(BaseModel):
    strain_id: str
    nitrogen_fixation_score: float = 0.0
    phosphate_solubilization_score: float = 0.0
    siderophore_score: float = 0.0
    iaa_score: float = 0.0
    acc_deaminase_score: float = 0.0
    biocontrol_score: float = 0.0
    stress_tolerance_score: float = 0.0
    colonization_score: float = 0.0
    secondary_metabolite_score: float = 0.0
    raw_features: dict[str, Any] = Field(default_factory=dict)


class BiosafetyProfile(BaseModel):
    strain_id: str
    amr_gene_count: int = 0
    virulence_gene_count: int = 0
    pathogen_flag: bool = False
    risky_genus_flag: bool = False
    plasmid_amr_flag: bool = False
    biosafety_notes: str | None = None
    biosafety_penalty: float = 0.0


class LiteratureEvidence(BaseModel):
    evidence_id: str
    plant_name: str
    strain_id: str
    bacterial_taxon: str
    effect_type: str
    stress_or_pathogen: str
    experimental_level: Literal[
        "field",
        "greenhouse",
        "pot",
        "in_vitro",
        "genome_only",
        "review",
    ]
    effect_direction: Literal["positive", "neutral", "negative", "mixed"]
    effect_size: float | None = None
    mechanism: str | None = None
    citation: str
    confidence_score: float = 0.0


class Recommendation(BaseModel):
    strain_id: str
    final_score: float
    evidence_level: str
    recommendation_class: Literal["A", "B", "C", "D", "E"]
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    suggested_validation_tests: list[str] = Field(default_factory=list)
    explanation: str

