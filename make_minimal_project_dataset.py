from pathlib import Path
import re
import pandas as pd

DATA_DIR = Path("data/demo")
PRODIGAL_DIR = Path("results/prodigal")

DATA_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_STRAINS = DATA_DIR / "strains.csv"
PLANTS = DATA_DIR / "plant_profiles.csv"

if not SOURCE_STRAINS.exists():
    raise SystemExit(f"Missing {SOURCE_STRAINS}")

if not PLANTS.exists():
    raise SystemExit(f"Missing {PLANTS}")


def clean_text(x: object) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip()


def normalize_species(x: object) -> str:
    s = clean_text(x).lower()
    s = s.replace("_", " ")
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_crop(x: object) -> str:
    s = clean_text(x).lower()
    mapping = {
        "bean": "common_bean",
        "common bean": "common_bean",
        "wheat": "wheat",
        "barley": "barley",
        "rice": "rice",
        "potato": "potato",
        "tomato": "tomato",
        "soybean": "soybean",
        "pea": "pea",
        "tobacco": "tobacco",
        "sunflower": "sunflower",
    }
    return mapping.get(s, s)


def count_fasta_records(path: Path) -> int:
    try:
        with path.open() as fh:
            return sum(1 for line in fh if line.startswith(">"))
    except Exception:
        return 0


def parse_genome_sample(sample: str) -> dict:
    """
    Example:
    pseudomonas_rhizosphaerae__GCF_000761155.1
    """
    if "__" in sample:
        taxon_part, accession = sample.split("__", 1)
    else:
        taxon_part, accession = sample, ""

    parts = taxon_part.split("_")
    genus = parts[0].capitalize() if parts else "Unknown"
    species = parts[1] if len(parts) > 1 else "sp."

    return {
        "sample_id": sample,
        "genus": genus,
        "species": species,
        "taxon_key": f"{genus.lower()} {species.lower()}",
        "genome_accession": accession,
    }


def build_prodigal_index() -> dict:
    genome_rows = []

    for faa in sorted(PRODIGAL_DIR.glob("*/*.faa")):
        sample = faa.stem
        parsed = parse_genome_sample(sample)
        parsed["faa"] = str(faa)
        parsed["n_proteins"] = count_fasta_records(faa)
        genome_rows.append(parsed)

    if not genome_rows:
        return {}

    df = pd.DataFrame(genome_rows)

    # For each genus species keep the genome with the largest protein count
    df = df.sort_values("n_proteins", ascending=False)
    best = df.drop_duplicates("taxon_key", keep="first")

    return best.set_index("taxon_key").to_dict(orient="index")


def is_spore_former(genus: str, source_value: object) -> bool:
    val = clean_text(source_value).lower()
    if val in {"true", "1", "yes", "y"}:
        return True
    if val in {"false", "0", "no", "n"}:
        return False
    return genus.lower() in {"bacillus", "paenibacillus"}


def pgp_prior(genus: str, species: str) -> dict:
    g = genus.lower()
    s = species.lower()

    scores = {
        "nitrogen_fixation_score": 0.0,
        "phosphate_solubilization_score": 0.0,
        "siderophore_score": 0.0,
        "iaa_score": 0.0,
        "acc_deaminase_score": 0.0,
        "biocontrol_score": 0.0,
        "stress_tolerance_score": 0.0,
        "colonization_score": 0.0,
        "secondary_metabolite_score": 0.0,
    }

    if g == "azospirillum":
        scores.update({
            "nitrogen_fixation_score": 0.8,
            "iaa_score": 0.6,
            "acc_deaminase_score": 0.3,
            "stress_tolerance_score": 0.5,
            "colonization_score": 0.6,
        })

    elif g in {"rhizobium", "bradyrhizobium", "sinorhizobium", "ensifer"}:
        scores.update({
            "nitrogen_fixation_score": 0.9,
            "colonization_score": 0.6,
            "iaa_score": 0.3,
        })

    elif g == "bacillus":
        scores.update({
            "phosphate_solubilization_score": 0.5,
            "siderophore_score": 0.3,
            "iaa_score": 0.3,
            "biocontrol_score": 0.8,
            "stress_tolerance_score": 0.5,
            "colonization_score": 0.4,
            "secondary_metabolite_score": 0.7,
        })

        if s in {"velezensis", "amyloliquefaciens", "subtilis", "siamensis"}:
            scores["biocontrol_score"] = 0.9
            scores["secondary_metabolite_score"] = 0.8

    elif g == "pseudomonas":
        scores.update({
            "siderophore_score": 0.8,
            "iaa_score": 0.3,
            "biocontrol_score": 0.6,
            "stress_tolerance_score": 0.4,
            "colonization_score": 0.6,
            "secondary_metabolite_score": 0.5,
        })

        if s in {"chlororaphis", "protegens", "fluorescens", "putida", "brassicacearum"}:
            scores["biocontrol_score"] = 0.8
            scores["siderophore_score"] = 0.9

    elif g in {"paenibacillus"}:
        scores.update({
            "nitrogen_fixation_score": 0.4,
            "phosphate_solubilization_score": 0.5,
            "biocontrol_score": 0.5,
            "stress_tolerance_score": 0.4,
            "colonization_score": 0.4,
        })

    elif g in {"streptomyces"}:
        scores.update({
            "biocontrol_score": 0.9,
            "secondary_metabolite_score": 0.9,
            "siderophore_score": 0.4,
        })

    else:
        scores["stress_tolerance_score"] = 0.1

    return scores


def biosafety_flags(genus: str, species: str) -> dict:
    g = genus.lower()
    s = species.lower()
    taxon = f"{g} {s}"

    risky_genera = {
        "klebsiella",
        "enterobacter",
        "serratia",
        "burkholderia",
        "stenotrophomonas",
        "acinetobacter",
    }

    strict_review_taxa = {
        "pseudomonas aeruginosa",
        "pseudomonas syringae",
        "pseudomonas savastanoi",
        "pseudomonas cichorii",
        "bacillus cereus",
        "bacillus cytotoxicus",
        "bacillus anthracis",
        "bacillus thuringiensis",
        "burkholderia cepacia",
        "burkholderia gladioli",
        "enterobacter hormaechei",
        "stenotrophomonas maltophilia",
        "klebsiella pneumoniae",
    }

    pathogen_flag = taxon in strict_review_taxa
    risky_genus_flag = g in risky_genera

    # Pseudomonas as a genus is not rejected, but several species are manual review.
    penalty = 0.0
    notes = []

    if risky_genus_flag:
        penalty += 5.0
        notes.append("risky/opportunistic genus; manual biosafety review required")

    if pathogen_flag:
        penalty += 8.0
        notes.append("species-level warning; not recommended without strict biosafety validation")

    if g == "pseudomonas" and s in {"aeruginosa", "syringae", "savastanoi", "cichorii"}:
        penalty += 6.0
        notes.append("plant/human pathogenic Pseudomonas group warning")

    if g == "bacillus" and s in {"cereus", "cytotoxicus", "anthracis"}:
        penalty += 8.0
        notes.append("Bacillus cereus/anthracis group warning")

    if not notes:
        notes.append("low-risk rule-based profile; AMRFinder/virulence screening still required")

    return {
        "pathogen_flag": pathogen_flag,
        "risky_genus_flag": risky_genus_flag,
        "plasmid_amr_flag": False,
        "amr_gene_count": 0,
        "virulence_gene_count": 0,
        "biosafety_penalty": penalty,
        "biosafety_notes": "; ".join(notes),
    }


# Load current strain table
raw = pd.read_csv(SOURCE_STRAINS, dtype=str).fillna("")
genome_index = build_prodigal_index()

# Normalize input column names
id_col = "strain_id" if "strain_id" in raw.columns else "id"
name_col = "strain_name" if "strain_name" in raw.columns else "strain"

required = ["genus", "species"]
for col in required:
    if col not in raw.columns:
        raise SystemExit(f"Missing required column in strain table: {col}")

strain_rows = []
pgp_rows = []
biosafety_rows = []
lit_rows = []

for _, row in raw.iterrows():
    old_id = clean_text(row.get(id_col, ""))
    genus = clean_text(row.get("genus", "Unknown")).capitalize()
    species = clean_text(row.get("species", "sp.")).lower()
    strain_code = clean_text(row.get(name_col, ""))

    if not old_id:
        continue

    taxon_key = f"{genus.lower()} {species.lower()}"
    genome_match = genome_index.get(taxon_key)

    has_prodigal = genome_match is not None
    genome_accession = ""
    matched_genome_sample = ""
    n_proteins = 0

    if genome_match:
        genome_accession = genome_match.get("genome_accession", "")
        matched_genome_sample = genome_match.get("sample_id", "")
        n_proteins = int(genome_match.get("n_proteins", 0) or 0)

    source_accession = clean_text(row.get("genome_accession", ""))
    if source_accession and source_accession != "none_found":
        genome_accession = source_accession

    strain_name = f"{genus} {species} {strain_code}".strip()

    taxonomy_conf = clean_text(row.get("taxonomy_confidence", "0.8"))
    try:
        taxonomy_conf = float(taxonomy_conf)
    except Exception:
        taxonomy_conf = 0.8

    niche = clean_text(row.get("niche", "unknown"))
    target_crop = normalize_crop(row.get("target_crop", "unknown"))
    formulation = clean_text(row.get("formulation_notes", ""))

    strain_rows.append({
        "strain_id": old_id,
        "strain_name": strain_name,
        "genus": genus,
        "species": species,
        "taxonomy_confidence": taxonomy_conf,
        "source": "BacDive-derived plant-associated strain table",
        "is_spore_former": is_spore_former(genus, row.get("is_spore_former", "")),
        "isolation_source": niche,
        "host_plant": target_crop,
        "region": "unknown",
        "genome_accession": genome_accession if genome_accession else "not_matched",
        "notes": (
            f"{clean_text(row.get('notes', ''))}; "
            f"formulation={formulation}; "
            f"matched_prodigal_genome={matched_genome_sample or 'none'}; "
            f"n_proteins={n_proteins}"
        ),
    })

    pgp = pgp_prior(genus, species)
    pgp["strain_id"] = old_id
    pgp["raw_features"] = (
        f"genus_level_prior; niche={niche}; target_crop={target_crop}; "
        f"has_prodigal_faa={has_prodigal}; n_proteins={n_proteins}; "
        "functional genes not yet annotated"
    )
    pgp_rows.append(pgp)

    bio = biosafety_flags(genus, species)
    bio["strain_id"] = old_id
    biosafety_rows.append(bio)

    evidence_level = "genome_only" if has_prodigal else "association_only"
    effect = (
        "Plant-associated candidate with local Prodigal protein prediction available"
        if has_prodigal
        else "Plant-associated candidate from strain table; genome not matched yet"
    )

    lit_rows.append({
        "strain_id": old_id,
        "plant_name": target_crop,
        "evidence_level": evidence_level,
        "effect": effect,
        "source": "BacDive-derived table + local Prodigal status",
        "notes": (
            f"{strain_name}; niche={niche}; target_crop={target_crop}; "
            f"matched_genome={matched_genome_sample or 'none'}"
        ),
    })

strains = pd.DataFrame(strain_rows)
pgp_traits = pd.DataFrame(pgp_rows)
biosafety = pd.DataFrame(biosafety_rows)
literature = pd.DataFrame(lit_rows)

strains.to_csv(DATA_DIR / "strains.csv", index=False)
pgp_traits.to_csv(DATA_DIR / "pgp_traits.csv", index=False)
biosafety.to_csv(DATA_DIR / "biosafety.csv", index=False)
literature.to_csv(DATA_DIR / "literature_evidence.csv", index=False)

print("Generated simplified MVP dataset:")
print("strains:", strains.shape)
print("pgp_traits:", pgp_traits.shape)
print("biosafety:", biosafety.shape)
print("literature_evidence:", literature.shape)
print("Prodigal genome matches:", strains["notes"].str.contains("matched_prodigal_genome=", regex=False).sum())
print("Non-empty genome accessions:", (strains["genome_accession"] != "not_matched").sum())

print("\nTop rows:")
print(strains.head().to_string(index=False))
