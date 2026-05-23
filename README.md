# PlantBacteriaMatch

PlantBacteriaMatch is an MVP assistant for ranking potentially useful bacterial strains for plant-associated applications. It combines synthetic literature evidence, PGP/PGPR trait profiles, genome-derived feature summaries, formulation hints, and mandatory biosafety penalties into an explainable candidate list.

The tool does **not** prescribe bacteria as ready agronomic solutions. It narrows the search space for wet-lab, greenhouse, and field validation.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

For tests:

```bash
PYTHONPATH=src pytest
```

## Data

All files in `data/demo` are synthetic demo data for prototype and hackathon use only. They are realistic enough to exercise the scoring logic, but they are not curated biological claims and must not be used for agronomic decisions.

Main tables:

- `strains.csv`: strain metadata, taxonomy, host/isolation source, genome accession, formulation notes.
- `pgp_traits.csv`: normalized 0-1 PGP trait scores from mocked PGPT-Pred/PLaBAse-style outputs.
- `biosafety.csv`: mocked AMR, virulence, pathogen, plasmid AMR, and biosafety penalty fields.
- `literature_evidence.csv`: mocked evidence rows with experimental level and confidence.
- `plant_profiles.csv`: demo crop profiles and target problems.

## External Tool Architecture

The MVP imports ready-made TSV/CSV/JSON tables and can later be connected to Snakemake outputs. Planned tool adapters include:

- Bakta or Prokka for bacterial genome annotation
- PLaBAse / PGPT-Pred for plant growth-promoting traits
- antiSMASH for biosynthetic gene clusters
- BAGEL for bacteriocins
- AMRFinderPlus / CARD / ResFinder for antibiotic resistance
- VFDB / PathogenFinder for virulence and pathogenicity screening
- eggNOG-mapper / KEGG / Pfam / InterPro for functional annotation
- GTDB-Tk / Mash / FastANI for taxonomy
- PubMed / Europe PMC / Semantic Scholar for literature mining and future RAG extraction

See `workflows/Snakefile` for placeholder rules showing where real commands can be wired.

## Scoring

The transparent score is:

```text
final_score =
  plant_match_score
+ evidence_score
+ pgp_trait_score
+ stress_specific_score
+ colonization_score
+ formulation_score
- biosafety_penalty
- uncertainty_penalty
```

Biosafety is a hard design constraint. A pathogen flag or high virulence burden prevents A/B recommendations even if PGP traits are strong.

## Limitations

- Gene presence does not imply expression, phenotype, compatibility with the plant, or field efficacy.
- Recommendations require wet-lab, greenhouse, and field validation.
- Biosafety screening is mandatory before any applied work.
- This MVP does not replace agronomic, microbiological, regulatory, or biosafety expertise.

