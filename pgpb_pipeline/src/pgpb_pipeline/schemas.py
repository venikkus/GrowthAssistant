"""Lightweight schemas and constants for pipeline tables."""

from __future__ import annotations

from dataclasses import dataclass


RISKY_TAXA = {
    "klebsiella",
    "enterobacter",
    "serratia",
    "burkholderia",
    "stenotrophomonas",
    "acinetobacter",
}


@dataclass(frozen=True)
class Sample:
    sample_id: str
    fasta: str
    plant: str
    target_trait: str
    condition: str


PGP_MARKERS: dict[str, list[str]] = {
    "nitrogen_fixation": ["nifH", "nifD", "nifK", "nifE", "nifN", "vnf", "anf"],
    "phosphate_solubilization": ["gcd", "pqq", "pho", "phosphatase"],
    "iaa_biosynthesis": ["ipdC", "iaaM", "iaaH", "tryptophan", "indole-3-acetic"],
    "acc_deaminase": ["acdS", "ACC deaminase"],
    "siderophores": ["siderophore", "enterobactin", "pyoverdine"],
    "eps_biofilm": ["eps", "biofilm", "pel", "psl", "cellulose"],
    "stress_tolerance": ["osmoprotectant", "trehalose", "glycine betaine", "cold-shock"],
    "motility_colonization": ["flagell", "chemotaxis", "pili", "pilus", "motility"],
    "biocontrol": ["chitinase", "glucanase", "protease", "lipopeptide", "antimicrobial"],
}

