"""Reusable workflow actions used by CLI and wrapper scripts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pgpb_pipeline.biosafety import build_biosafety_summary
from pgpb_pipeline.external_evidence import load_external_evidence, summarize_database_evidence
from pgpb_pipeline.io import load_samples_df, read_yaml, write_table
from pgpb_pipeline.parsers.amrfinder import parse_amrfinder
from pgpb_pipeline.parsers.antismash import parse_antismash
from pgpb_pipeline.parsers.bakta import (
    parse_annotation_features,
    parse_bakta_summary,
    summarize_annotation_features,
)
from pgpb_pipeline.parsers.busco import parse_busco_summary
from pgpb_pipeline.parsers.checkm import parse_checkm
from pgpb_pipeline.parsers.crisprcasfinder import parse_crisprcasfinder
from pgpb_pipeline.parsers.dbcan import parse_dbcan
from pgpb_pipeline.parsers.eggnog import parse_eggnog
from pgpb_pipeline.parsers.gtdbtk import parse_taxonomy_summary
from pgpb_pipeline.parsers.phaster import parse_phaster
from pgpb_pipeline.parsers.plasmidfinder import parse_plasmidfinder
from pgpb_pipeline.parsers.quast import parse_quast_report
from pgpb_pipeline.parsers.vfdb import parse_vfdb
from pgpb_pipeline.pgp_traits import (
    detect_pgp_traits,
    make_trait_matrix,
    parse_pgpt_pred_results,
    summarize_pgp_traits,
)
from pgpb_pipeline.scoring import score_samples


def _base_dir(config_path: Path) -> Path:
    return config_path.resolve().parent.parent


def _mock_path(base: Path, sample_id: str, filename: str) -> Path:
    return base / "mock_outputs" / sample_id / filename


def _first_existing(paths: list[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


def _first_glob(directory: Path, patterns: list[str], fallback_name: str) -> Path:
    for pattern in patterns:
        matches = sorted(directory.glob(pattern))
        if matches:
            return matches[0]
    return directory / fallback_name


def aggregate_results(config: str | Path, samples: str | Path, results: str | Path) -> None:
    config_path = Path(config)
    base = _base_dir(config_path)
    cfg = read_yaml(config_path)
    mode = cfg.get("mode", "mock")
    results = Path(results)
    samples_df = load_samples_df(samples)
    scoring_cfg = read_yaml(base / "config" / "scoring.yaml")

    qc_tables = []
    taxonomy_tables = []
    annotation_tables = []
    functional_tables = []
    bgc_tables = []
    amr_tables = []
    virulence_tables = []
    plasmid_tables = []
    crispr_tables = []
    phage_tables = []
    cazy_tables = []
    pgp_tables = []

    for sample_id in samples_df["sample_id"]:
        if mode == "mock":
            quast_path = _mock_path(base, sample_id, "quast_report.tsv")
            checkm_path = _mock_path(base, sample_id, "checkm.tsv")
            busco_path = _mock_path(base, sample_id, "busco_short_summary.txt")
            taxonomy_path = _mock_path(base, sample_id, "taxonomy.tsv")
            annotation_path = _mock_path(base, sample_id, "annotation_summary.tsv")
            annotation_dir = annotation_path.parent
            functional_path = _mock_path(base, sample_id, "eggnog.tsv")
            bgc_path = _mock_path(base, sample_id, "antismash.tsv")
            amr_path = _mock_path(base, sample_id, "amrfinder.tsv")
            virulence_path = _mock_path(base, sample_id, "virulence.tsv")
            plasmid_path = _mock_path(base, sample_id, "plasmid.tsv")
            crispr_path = _mock_path(base, sample_id, "crispr.tsv")
            phage_path = _mock_path(base, sample_id, "phage.tsv")
            cazy_path = _mock_path(base, sample_id, "dbcan.tsv")
        else:
            quast_dir = results / "qc" / sample_id / "quast"
            busco_dir = results / "qc" / sample_id / "busco"
            annotation_dir = results / "annotation" / sample_id / "bakta"
            eggnog_dir = results / "functional" / sample_id / "eggnog"
            antismash_dir = results / "secondary_metabolites" / sample_id / "antismash"
            amrfinder_dir = results / "biosafety" / sample_id / "amrfinder"
            quast_path = _first_glob(quast_dir, ["report.tsv", "transposed_report.tsv"], "report.tsv")
            checkm_path = results / "qc" / sample_id / "checkm" / "checkm.tsv"
            busco_path = _first_glob(busco_dir, ["short_summary*.txt", "**/short_summary*.txt"], "short_summary.txt")
            taxonomy_path = results / "taxonomy" / sample_id / "taxonomy.tsv"
            annotation_path = _first_glob(annotation_dir, ["*summary*.tsv"], "annotation_summary.tsv")
            functional_path = _first_glob(eggnog_dir, ["*.annotations", "*.tsv"], "eggnog.tsv")
            bgc_path = _first_glob(antismash_dir, ["*summary*.tsv", "*.tsv"], "antismash.tsv")
            amr_path = _first_glob(amrfinder_dir, ["*.amrfinder.tsv", "*.tsv"], f"{sample_id}.amrfinder.tsv")
            virulence_path = results / "biosafety" / sample_id / "vfdb" / "virulence.tsv"
            plasmid_path = results / "mobile_elements" / sample_id / "plasmidfinder" / "plasmid.tsv"
            crispr_path = results / "crispr_phage" / sample_id / "crisprcasfinder" / "crispr.tsv"
            phage_path = results / "crispr_phage" / sample_id / "phaster" / "phage.tsv"
            cazy_path = results / "cazy" / sample_id / "dbcan.tsv"
        pgpt_dir = base / cfg.get("paths", {}).get("pgpt_pred", "data/external/pgpt_pred")
        pgpt_path = pgpt_dir / f"{sample_id}.tsv"

        quast = parse_quast_report(quast_path, sample_id)
        checkm = parse_checkm(checkm_path, sample_id)
        busco = parse_busco_summary(busco_path, sample_id)
        qc_tables.append(quast.merge(checkm, on="sample_id", how="outer").merge(busco, on="sample_id", how="outer"))

        taxonomy = parse_taxonomy_summary(taxonomy_path, sample_id)
        annotation_features = parse_annotation_features(
            _first_glob(annotation_dir, ["*.tsv", "*.gff3", "*.gff"], "features.tsv"),
            sample_id,
        )
        annotation = parse_bakta_summary(annotation_path, sample_id)
        if annotation["cds"].isna().all() and not annotation_features.empty:
            annotation = summarize_annotation_features(annotation_features, sample_id, annotation_dir)
        functional = parse_eggnog(functional_path, sample_id)
        functional_for_pgp = functional if not functional.empty else annotation_features
        bgc = parse_antismash(bgc_path, sample_id)
        amr = parse_amrfinder(amr_path, sample_id)
        virulence = parse_vfdb(virulence_path, sample_id)
        plasmid = parse_plasmidfinder(plasmid_path, sample_id)
        crispr = parse_crisprcasfinder(crispr_path, sample_id)
        phage = parse_phaster(phage_path, sample_id)
        cazy = parse_dbcan(cazy_path, sample_id)
        pgpt_import = parse_pgpt_pred_results(pgpt_path, sample_id)
        pgp = detect_pgp_traits(sample_id, functional_for_pgp, bgc, external_pgp_df=pgpt_import)

        taxonomy_tables.append(taxonomy)
        annotation_tables.append(annotation)
        functional_tables.append(functional)
        bgc_tables.append(bgc)
        amr_tables.append(amr)
        virulence_tables.append(virulence)
        plasmid_tables.append(plasmid)
        crispr_tables.append(crispr)
        phage_tables.append(phage)
        cazy_tables.append(cazy)
        pgp_tables.append(pgp)

    tables = results / "tables"
    qc_df = pd.concat(qc_tables, ignore_index=True)
    taxonomy_df = pd.concat(taxonomy_tables, ignore_index=True)
    annotation_df = pd.concat(annotation_tables, ignore_index=True)
    functional_df = pd.concat(functional_tables, ignore_index=True)
    bgc_df = pd.concat(bgc_tables, ignore_index=True)
    amr_df = pd.concat(amr_tables, ignore_index=True)
    virulence_df = pd.concat(virulence_tables, ignore_index=True)
    plasmid_df = pd.concat(plasmid_tables, ignore_index=True)
    crispr_df = pd.concat(crispr_tables, ignore_index=True)
    phage_df = pd.concat(phage_tables, ignore_index=True)
    cazy_df = pd.concat(cazy_tables, ignore_index=True)
    pgp_df = pd.concat(pgp_tables, ignore_index=True)
    external_dir = base / cfg.get("paths", {}).get("external_evidence", "data/external")
    external_evidence_df = load_external_evidence(external_dir)
    database_evidence_df = summarize_database_evidence(samples_df, taxonomy_df, external_evidence_df)
    biosafety_df = build_biosafety_summary(
        samples_df, taxonomy_df, amr_df, virulence_df, plasmid_df, scoring_cfg["biosafety"]
    )

    write_table(qc_df, tables / "qc_summary.tsv")
    write_table(taxonomy_df, tables / "taxonomy_summary.tsv")
    write_table(annotation_df, tables / "annotation_summary.tsv")
    write_table(functional_df, tables / "functional_summary.tsv")
    write_table(pd.DataFrame(columns=["sample_id", "orthogroup", "gene_id"]), tables / "orthologs.tsv")
    write_table(pgp_df, tables / "pgp_traits_long.tsv")
    write_table(make_trait_matrix(pgp_df), tables / "pgp_traits_matrix.tsv")
    write_table(summarize_pgp_traits(pgp_df), tables / "pgp_trait_summary.tsv")
    write_table(bgc_df, tables / "bgc_summary.tsv")
    write_table(pd.DataFrame(columns=["sample_id", "bacteriocin", "confidence"]), tables / "bacteriocin_summary.tsv")
    write_table(cazy_df, tables / "cazy_summary.tsv")
    write_table(amr_df, tables / "amr_summary.tsv")
    write_table(virulence_df, tables / "virulence_summary.tsv")
    write_table(biosafety_df, tables / "biosafety_summary.tsv")
    write_table(external_evidence_df, tables / "external_database_evidence.tsv")
    write_table(database_evidence_df, tables / "database_evidence_summary.tsv")
    write_table(plasmid_df, tables / "plasmid_summary.tsv")
    write_table(plasmid_df, tables / "mobility_summary.tsv")
    write_table(crispr_df, tables / "crispr_summary.tsv")
    write_table(phage_df, tables / "phage_summary.tsv")


def score_results(config: str | Path, samples: str | Path, results: str | Path) -> None:
    config_path = Path(config)
    base = _base_dir(config_path)
    results = Path(results)
    tables = results / "tables"
    scoring_cfg = read_yaml(base / "config" / "scoring.yaml")
    samples_df = load_samples_df(samples)
    ranking = score_samples(
        samples_df=samples_df,
        qc_df=pd.read_csv(tables / "qc_summary.tsv", sep="\t"),
        taxonomy_df=pd.read_csv(tables / "taxonomy_summary.tsv", sep="\t"),
        annotation_df=pd.read_csv(tables / "annotation_summary.tsv", sep="\t"),
        pgp_df=pd.read_csv(tables / "pgp_traits_long.tsv", sep="\t"),
        bgc_df=pd.read_csv(tables / "bgc_summary.tsv", sep="\t"),
        biosafety_df=pd.read_csv(tables / "biosafety_summary.tsv", sep="\t"),
        database_evidence_df=pd.read_csv(tables / "database_evidence_summary.tsv", sep="\t"),
        scoring_config=scoring_cfg,
    )
    write_table(ranking, tables / "final_ranking.tsv")
