#!/usr/bin/env python
"""Generate frozen Paper 3 pilot tables, figures, and verdict data."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from openew.paper3.static_relational.analysis import summarize_run_root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/paper3/static_relational/pilot.yaml"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--analysis-root", type=Path)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    analysis_root = args.analysis_root or Path(config["output_roots"]["analysis"])
    print(summarize_run_root(args.run_root, analysis_root, config))


if __name__ == "__main__":
    main()
