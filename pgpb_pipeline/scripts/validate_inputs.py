#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from pgpb_pipeline.io import load_samples_df, read_yaml


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--samples", default="config/samples.tsv")
    args = parser.parse_args()
    cfg = read_yaml(args.config)
    samples = load_samples_df(args.samples)
    required = {"sample_id", "fasta", "plant", "target_trait", "condition"}
    missing = required - set(samples.columns)
    if missing:
        raise SystemExit(f"Missing samples.tsv columns: {sorted(missing)}")
    base = Path(args.samples).resolve().parent.parent
    missing_fastas = [fasta for fasta in samples["fasta"] if not (base / fasta).exists()]
    if missing_fastas:
        raise SystemExit(f"Missing FASTA files: {missing_fastas}")
    print(f"Config OK. mode={cfg.get('mode', 'full')}; samples={len(samples)}")
