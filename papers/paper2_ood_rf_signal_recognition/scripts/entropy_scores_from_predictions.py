#!/usr/bin/env python
"""Generate higher-is-OOD entropy scores directly from calibrated predictions."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from baseline_ood_scores import build_ood_scores


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate entropy score CSVs from calibrated prediction CSVs.")
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--probability-prefix", default="prob_")
    parser.add_argument("--sample-id-column", default="sample_id")
    parser.add_argument("--true-label-column", default="true_label")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    frame = pd.read_csv(args.predictions, dtype=str, keep_default_na=False)
    if frame[args.sample_id_column].duplicated().any():
        raise ValueError("Prediction CSV contains duplicate sample IDs.")
    scores = build_ood_scores(
        frame, "entropy", probability_prefix=args.probability_prefix,
        sample_id_column=args.sample_id_column, true_label_column=args.true_label_column, seed=args.seed,
    )
    # ID-only validation predictions need no OOD annotation.
    if "ood_label" not in frame.columns:
        scores = scores.drop(columns="ood_label")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(args.output, index=False)
    print(f"Wrote {len(scores)} entropy scores to {args.output}")


if __name__ == "__main__":
    main()
