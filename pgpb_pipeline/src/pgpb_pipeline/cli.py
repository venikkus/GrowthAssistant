"""Argparse command line interface for the PGPB pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from pgpb_pipeline.io import load_samples_df, read_yaml


def validate_config(config: Path, samples: Path) -> None:
    cfg = read_yaml(config)
    samples_df = load_samples_df(samples)
    required = {"sample_id", "fasta", "plant", "target_trait", "condition"}
    missing = required - set(samples_df.columns)
    if missing:
        raise SystemExit(f"samples.tsv missing columns: {sorted(missing)}")
    base = samples.resolve().parent.parent
    for fasta in samples_df["fasta"]:
        fasta_path = Path(fasta) if Path(fasta).is_absolute() else base / fasta
        if not fasta_path.exists():
            raise SystemExit(f"FASTA not found: {fasta}")
    print(f"Config OK. mode={cfg.get('mode', 'full')}; samples={len(samples_df)}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="pgpb-pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--config", default="config/config.yaml")
        subparser.add_argument("--samples", default="config/samples.tsv")
        subparser.add_argument("--results", default="results")

    validate_parser = subparsers.add_parser("validate-config")
    validate_parser.add_argument("--config", default="config/config.yaml")
    validate_parser.add_argument("--samples", default="config/samples.tsv")

    aggregate_parser = subparsers.add_parser("aggregate")
    add_common(aggregate_parser)

    score_parser = subparsers.add_parser("score")
    add_common(score_parser)

    report_parser = subparsers.add_parser("report")
    add_common(report_parser)

    args = parser.parse_args()
    config = Path(getattr(args, "config", "config/config.yaml"))
    samples = Path(getattr(args, "samples", "config/samples.tsv"))
    results = Path(getattr(args, "results", "results"))

    if args.command == "validate-config":
        validate_config(config, samples)
    elif args.command == "aggregate":
        from pgpb_pipeline.workflow_api import aggregate_results

        aggregate_results(config, samples, results)
        print(f"Aggregated tables written to {results / 'tables'}")
    elif args.command == "score":
        from pgpb_pipeline.workflow_api import score_results

        score_results(config, samples, results)
        print(f"Final ranking written to {results / 'tables' / 'final_ranking.tsv'}")
    elif args.command == "report":
        from pgpb_pipeline.report import write_reports

        write_reports(results)
        print(f"Reports written to {results / 'reports'}")


if __name__ == "__main__":
    main()

