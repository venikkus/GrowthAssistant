"""Biosafety screening utilities."""

from __future__ import annotations

from plant_bacteria_match.models import BiosafetyProfile

RISKY_GENERA = {
    "klebsiella",
    "enterobacter",
    "serratia",
    "burkholderia",
    "stenotrophomonas",
    "acinetobacter",
}


def detect_risky_genus(genus: str, species: str) -> bool:
    genus_norm = (genus or "").strip().lower()
    species_norm = (species or "").strip().lower()
    if genus_norm in RISKY_GENERA:
        return True
    return genus_norm == "pseudomonas" and "aeruginosa" in species_norm


def compute_biosafety_penalty(
    amr_gene_count: int,
    virulence_gene_count: int,
    pathogen_flag: bool,
    risky_genus_flag: bool,
    plasmid_amr_flag: bool,
    strictness: str = "medium",
) -> float:
    multipliers = {"low": 0.8, "medium": 1.0, "high": 1.35}
    multiplier = multipliers.get(strictness, 1.0)
    penalty = 0.7 * amr_gene_count + 1.2 * virulence_gene_count
    if pathogen_flag:
        penalty += 8.0
    if risky_genus_flag:
        penalty += 2.5
    if plasmid_amr_flag:
        penalty += 3.0
    return round(penalty * multiplier, 3)


def generate_biosafety_warnings(profile: BiosafetyProfile | None) -> list[str]:
    if profile is None:
        return ["No biosafety profile available; mandatory screening is missing."]

    warnings: list[str] = []
    if profile.pathogen_flag:
        warnings.append("Pathogen flag is set; do not advance without expert review.")
    if profile.risky_genus_flag:
        warnings.append("Taxon belongs to a genus/group requiring stricter biosafety review.")
    if profile.virulence_gene_count >= 3:
        warnings.append(f"High virulence marker count: {profile.virulence_gene_count}.")
    elif profile.virulence_gene_count > 0:
        warnings.append(f"Virulence markers detected: {profile.virulence_gene_count}.")
    if profile.amr_gene_count >= 3:
        warnings.append(f"Multiple AMR markers detected: {profile.amr_gene_count}.")
    elif profile.amr_gene_count > 0:
        warnings.append(f"AMR markers detected: {profile.amr_gene_count}.")
    if profile.plasmid_amr_flag:
        warnings.append("AMR markers may be plasmid-associated.")
    if profile.biosafety_notes:
        warnings.append(profile.biosafety_notes)
    return warnings

