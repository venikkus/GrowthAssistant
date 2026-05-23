#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from pgpb_pipeline.workflow_api import aggregate_results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--samples", default="config/samples.tsv")
    parser.add_argument("--results", default="results")
    args = parser.parse_args()
    aggregate_results(Path(args.config), Path(args.samples), Path(args.results))


if __name__ == "__main__":
    main()

