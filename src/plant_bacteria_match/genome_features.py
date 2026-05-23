"""Import adapters for external genome-feature tools."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from plant_bacteria_match.io import load_pgp_traits


def parse_pgpt_pred_results(path: str | Path) -> pd.DataFrame:
    return load_pgp_traits(path)


def parse_antismash_summary(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t" if str(path).endswith(".tsv") else ",")


def parse_amrfinder_results(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t" if str(path).endswith(".tsv") else ",")


def merge_genome_features(*tables: pd.DataFrame) -> pd.DataFrame:
    """Merge imported feature tables on strain_id.

    TODO: Wire this to Snakemake outputs from Bakta/Prokka, PGPT-Pred/PLaBAse,
    antiSMASH, BAGEL, AMRFinderPlus/CARD/ResFinder, VFDB/PathogenFinder,
    eggNOG/KEGG/Pfam/InterPro, GTDB-Tk/Mash/FastANI.
    """
    if not tables:
        return pd.DataFrame()
    merged = tables[0].copy()
    for table in tables[1:]:
        merged = merged.merge(table, on="strain_id", how="outer")
    return merged

