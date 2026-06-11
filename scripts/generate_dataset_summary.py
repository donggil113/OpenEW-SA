#!/usr/bin/env python
"""Generate a dataset summary table from converted artifact directories."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def summarize(artifact_dirs: list[str]) -> pd.DataFrame:
    rows = []
    for artifact_dir in artifact_dirs:
        path = Path(artifact_dir)
        metadata = pd.read_csv(path / "metadata.csv")
        rows.append(
            {
                "dataset_source": ", ".join(sorted(metadata["dataset_source"].dropna().astype(str).unique())),
                "num_samples": len(metadata),
                "input_types": ", ".join(sorted(metadata["input_type"].dropna().astype(str).unique())),
                "domains": metadata["domain_id"].nunique(dropna=True),
                "frequency_bands": metadata["frequency_band"].nunique(dropna=True),
                "artifact_dir": str(path),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create dataset summary table.")
    parser.add_argument("artifact_dirs", nargs="+", help="Converted artifact directories.")
    parser.add_argument("--output", default="tables/dataset_summary.csv", help="Output CSV path.")
    args = parser.parse_args()
    table = summarize(args.artifact_dirs)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
