#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from pgpb_pipeline.report import write_reports


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results")
    args = parser.parse_args()
    write_reports(Path(args.results))


if __name__ == "__main__":
    main()

