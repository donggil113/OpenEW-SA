#!/usr/bin/env python
"""Aggregate baseline metric JSON/CSV files into a paper-ready table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def load_metrics(path: Path) -> dict:
    if path.suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    if path.suffix == ".csv":
        return pd.read_csv(path).iloc[0].to_dict()
    raise ValueError(f"Unsupported metrics file: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create baseline performance table.")
    parser.add_argument("metrics_files", nargs="+", help="Metric JSON/CSV files.")
    parser.add_argument("--output", default="tables/baseline_performance.csv", help="Output CSV path.")
    args = parser.parse_args()
    rows = [load_metrics(Path(path)) for path in args.metrics_files]
    table = pd.DataFrame(rows)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
