# PGPB Pipeline

Snakemake-based MVP pipeline for bacterial genome analysis in a plant growth-promoting bacteria candidate selection workflow.

Current MVP uses plant profiles, BacDive-derived plant-associated bacterial strain candidates, local genome availability, Prodigal protein prediction status, and rule-based genus-level PGPR priors.

Functional annotation with Bakta/eggNOG, secondary metabolite mining with antiSMASH, and AMR screening are planned next layers.

The pipeline starts from bacterial genome FASTA files and produces QC, taxonomy, annotation, functional, PGP/PGPR trait, secondary metabolite, CAZyme, AMR/virulence, plasmid/mobile element, CRISPR/phage summaries, and a final ranking table.

This is a prototype. It does **not** make final biological or agronomic recommendations. Candidate strains require biosafety review plus laboratory, greenhouse, and field validation.

## Install

```bash
pip install -r requirements.txt
pip install -e .
```

For full production runs, install external tools and databases through conda/mamba using the environment YAML files under `workflow/envs/`.

## Modes

The pipeline has two practical modes:

- `mock`: default demo mode. It does not run heavy external tools. It reads prepared fake outputs from `mock_outputs/`, then generates parsed tables, `final_ranking.tsv`, and HTML reports.
- `real`: runs Snakemake rules for QUAST, BUSCO, Bakta, eggNOG-mapper, antiSMASH, AMRFinderPlus, and lightweight placeholder/adapter rules. If a required command or database is missing, the rule exits with a clear message and suggests `mode=mock`.

Set the mode in `config/config.yaml` or on the command line with `--config mode=mock` / `--config mode=real`.

## Quick Mock Run

The repository includes two fake bacterial genomes and mock tool outputs, so the MVP can run without heavy databases:

```bash
snakemake --cores 2 --config mode=mock
```

For real tool execution:

```bash
snakemake --use-conda --cores 8 --config mode=real
```

You can also run the Python steps directly:

```bash
PYTHONPATH=src python scripts/validate_inputs.py --config config/config.yaml --samples config/samples.tsv
PYTHONPATH=src python scripts/aggregate_results.py --config config/config.yaml --samples config/samples.tsv --results results
PYTHONPATH=src python scripts/score_strains.py --config config/config.yaml --samples config/samples.tsv --results results
PYTHONPATH=src python scripts/make_report.py --results results
```

CLI after editable install:

```bash
pgpb-pipeline validate-config --config config/config.yaml --samples config/samples.tsv
pgpb-pipeline aggregate --config config/config.yaml --samples config/samples.tsv --results results/
pgpb-pipeline score --config config/config.yaml --samples config/samples.tsv --results results/
pgpb-pipeline report --config config/config.yaml --samples config/samples.tsv --results results/
```

## Input Format

`config/samples.tsv`:

```text
sample_id    fasta    plant    target_trait    condition
strain_001   data/genomes/strain_001.fna   wheat   drought,phosphate_solubilization   dry_soil
strain_002   data/genomes/strain_002.fna   tomato   biocontrol   Fusarium
```

`config/config.yaml` controls module enablement, database paths, threads, and mode (`mock` or `real`).

`config/scoring.yaml` controls scoring weights.

## Output

Key outputs:

- `results/tables/qc_summary.tsv`
- `results/tables/taxonomy_summary.tsv`
- `results/tables/annotation_summary.tsv`
- `results/tables/functional_summary.tsv`
- `results/tables/pgp_traits_long.tsv`
- `results/tables/pgp_traits_matrix.tsv`
- `results/tables/pgp_trait_summary.tsv`
- `results/tables/bgc_summary.tsv`
- `results/tables/cazy_summary.tsv`
- `results/tables/amr_summary.tsv`
- `results/tables/virulence_summary.tsv`
- `results/tables/biosafety_summary.tsv`
- `results/tables/external_database_evidence.tsv`
- `results/tables/database_evidence_summary.tsv`
- `results/tables/plasmid_summary.tsv`
- `results/tables/crispr_summary.tsv`
- `results/tables/phage_summary.tsv`
- `results/tables/final_ranking.tsv`
- `results/reports/final_report.html`

Optional database evidence from BacDive/PubMed/GloBI-style tables is stored as TSV under `data/external/`. These files are treated as supporting evidence only: they can raise `database_evidence_score` when plant and taxon/genus match, but they do not override genome QC or biosafety penalties.

Optional PGPT-Pred/PLaBAse imports can be added under `data/external/pgpt_pred/{sample_id}.tsv`. The pipeline does not submit data to the PGPT-Pred web form automatically; upload proteins manually, download the result table, and place it there. Missing files are allowed and simply add no PGPT-Pred evidence.

## Pipeline Modules

External tools are optional/configurable. In `mode=mock`, fake outputs and mock-compatible parsers let the pipeline run locally.

- QC: QUAST, CheckM, BUSCO
- Taxonomy: GTDB-Tk, Kraken2, Mash, FastANI
- Structural annotation: Bakta by default, Prokka fallback, NCBI PGAP manual placeholder
- Functional annotation: eggNOG-mapper, InterProScan placeholder, KOfamScan-compatible placeholder
- PGP traits: PLaBAse / PGPT-Pred import plus internal marker/keyword detection
- Secondary metabolites: antiSMASH, BAGEL
- CAZymes: dbCAN
- Biosafety: AMRFinderPlus, CARD/RGI placeholder, ResFinder placeholder, VFDB placeholder, PathogenFinder placeholder
- Mobile elements: PlasmidFinder, MOB-suite
- CRISPR/phage: CRISPRCasFinder, PHASTER

## Scoring

Final score:

```text
final_score =
    qc_score
  + taxonomy_confidence_score
  + pgp_trait_score
  + plant_trait_match_score
  + biocontrol_score
  + stress_tolerance_score
  + secondary_metabolite_score
  + formulation_score
  - biosafety_penalty
  - uncertainty_penalty
```

The MVP currently folds biocontrol/stress evidence into PGP and plant-trait matching components while keeping the formula transparent in `src/pgpb_pipeline/scoring.py`.

Risky/opportunistic groups are penalized, including `Klebsiella`, `Enterobacter`, `Serratia`, `Burkholderia`, `Pseudomonas aeruginosa group`, `Stenotrophomonas`, and `Acinetobacter`.

Recommended status values:

- `strong_candidate`
- `promising_candidate`
- `weak_candidate`
- `risky_candidate`
- `reject_or_manual_review`

Confidence levels:

- `A`: good genome, multiple PGP traits, low biosafety risk
- `B`: good genome, some PGP traits, low/medium risk
- `C`: partial evidence or poorer genome
- `D`: mostly speculative
- `E`: risky or rejected

## PGP Marker Extension

Add markers in `src/pgpb_pipeline/schemas.py` under `PGP_MARKERS`, or adjust target-specific marker weights in `config/scoring.yaml`.

Examples:

- nitrogen fixation: `nifH`, `nifD`, `nifK`, `nifE`, `nifN`, `vnf`, `anf`
- phosphate solubilization: `gcd`, `pqqA-G`, `pho`, acid/alkaline phosphatases
- IAA: `ipdC`, `iaaM`, `iaaH`, tryptophan metabolism
- ACC deaminase: `acdS`
- siderophores, EPS/biofilm, osmoprotectants, motility, colonization, chitinases, glucanases, proteases

## Caveats

- Gene presence does not prove expression, phenotype, plant compatibility, or field efficacy.
- CAZyme and virulence-like functions must be interpreted carefully.
- AMR, virulence, plasmid, and taxonomy screening is mandatory before any applied work.
- The output is a ranking for prioritizing validation, not a deployment recommendation.
