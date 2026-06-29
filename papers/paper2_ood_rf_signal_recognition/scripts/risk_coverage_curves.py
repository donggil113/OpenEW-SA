#!/usr/bin/env python
"""Create selective-prediction risk-coverage curves from prediction CSV files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Generate risk-coverage CSV data from predictions and confidence scores.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--predictions", required=True, type=Path, help="Prediction CSV path.")
    parser.add_argument("--true-label-column", default="true_label", help="Ground-truth label column.")
    parser.add_argument("--predicted-label-column", default="predicted_label", help="Predicted label column.")
    parser.add_argument("--confidence-column", default="confidence", help="Confidence column.")
    parser.add_argument("--output", required=True, type=Path, help="Output risk-coverage CSV path.")
    parser.add_argument("--summary-output", type=Path, help="Optional JSON summary output path.")
    parser.add_argument("--figure", type=Path, help="Optional PNG figure path.")
    return parser.parse_args()


def main() -> None:
    """Run risk-coverage curve generation."""

    args = parse_args()
    predictions = pd.read_csv(args.predictions)
    curve, summary = compute_risk_coverage_curve(
        predictions=predictions,
        true_label_column=args.true_label_column,
        predicted_label_column=args.predicted_label_column,
        confidence_column=args.confidence_column,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    curve.to_csv(args.output, index=False)
    if args.summary_output is not None:
        _write_summary(summary, args.summary_output)
    if args.figure is not None:
        _write_figure(curve, args.figure)
    print(json.dumps(summary, indent=2, sort_keys=True))


def compute_risk_coverage_curve(
    predictions: pd.DataFrame,
    true_label_column: str = "true_label",
    predicted_label_column: str = "predicted_label",
    confidence_column: str = "confidence",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return a risk-coverage curve and summary from prediction correctness and confidence."""

    _require_columns(predictions, [true_label_column, predicted_label_column, confidence_column])
    true_labels = predictions[true_label_column].fillna("").astype(str)
    predicted_labels = predictions[predicted_label_column].fillna("").astype(str)
    confidence = predictions[confidence_column].astype(float).clip(0.0, 1.0)

    frame = pd.DataFrame(
        {
            "true_label": true_labels,
            "predicted_label": predicted_labels,
            "confidence": confidence,
            "error": (true_labels != predicted_labels).astype(float),
        }
    ).sort_values("confidence", ascending=False, kind="mergesort")

    n_rows = len(frame)
    if n_rows == 0:
        raise ValueError("Prediction CSV is empty.")

    retained = np.arange(1, n_rows + 1)
    cumulative_errors = frame["error"].to_numpy().cumsum()
    coverage = retained / n_rows
    risk = cumulative_errors / retained
    curve = pd.DataFrame(
        {
            "n_retained": retained,
            "coverage": coverage,
            "risk": risk,
            "selective_accuracy": 1.0 - risk,
            "confidence_threshold": frame["confidence"].to_numpy(),
        }
    )
    aurc = float(np.trapz(curve["risk"].to_numpy(), curve["coverage"].to_numpy()))
    summary = {
        "n_samples": int(n_rows),
        "base_risk": float(frame["error"].mean()),
        "base_accuracy": float(1.0 - frame["error"].mean()),
        "aurc": aurc,
        "risk_at_50_coverage": _risk_at_coverage(curve, 0.50),
        "risk_at_80_coverage": _risk_at_coverage(curve, 0.80),
        "risk_at_95_coverage": _risk_at_coverage(curve, 0.95),
    }
    return curve, summary


def _risk_at_coverage(curve: pd.DataFrame, target_coverage: float) -> float:
    eligible = curve.loc[curve["coverage"] >= target_coverage]
    if eligible.empty:
        return float(curve["risk"].iloc[-1])
    return float(eligible.iloc[0]["risk"])


def _write_summary(summary: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_figure(curve: pd.DataFrame, output: Path) -> None:
    import matplotlib.pyplot as plt

    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5.0, 3.2))
    ax.plot(curve["coverage"], curve["risk"], linewidth=2.0)
    ax.set_xlabel("Coverage")
    ax.set_ylabel("Risk")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(bottom=0.0)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def _require_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")


if __name__ == "__main__":
    main()
