#!/usr/bin/env python
"""Fit temperature scaling for Paper 2 baseline classifier prediction CSVs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

SYMBOLIC_STRING_COLUMNS = ["sample_id", "true_label", "predicted_label", "ood_label"]
EPSILON = 1e-12


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Fit scalar temperature scaling on validation predictions and calibrate test predictions.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--val-predictions", required=True, type=Path, help="Validation prediction CSV.")
    parser.add_argument("--test-id-predictions", required=True, type=Path, help="ID test prediction CSV.")
    parser.add_argument("--test-ood-predictions", required=True, type=Path, help="OOD test prediction CSV.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for calibrated predictions.")
    parser.add_argument("--probability-prefix", default="prob_", help="Class probability column prefix.")
    parser.add_argument("--true-label-column", default="true_label", help="Ground-truth label column.")
    parser.add_argument("--sample-id-column", default="sample_id", help="Sample identifier column.")
    parser.add_argument("--temperature-min", type=float, default=0.05, help="Minimum temperature to evaluate.")
    parser.add_argument("--temperature-max", type=float, default=10.0, help="Maximum temperature to evaluate.")
    parser.add_argument("--num-grid", type=int, default=200, help="Number of temperature grid values.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed recorded for reproducibility.")
    return parser.parse_args()


def main() -> None:
    """Fit temperature scaling and write calibrated Paper 2 prediction CSVs."""

    args = parse_args()
    val_predictions = _read_predictions(args.val_predictions)
    test_id_predictions = _read_predictions(args.test_id_predictions)
    test_ood_predictions = _read_predictions(args.test_ood_predictions)

    probability_columns = _probability_columns(val_predictions, args.probability_prefix)
    class_labels = [_strip_prefix(column, args.probability_prefix) for column in probability_columns]
    for name, frame in [
        ("test-id", test_id_predictions),
        ("test-ood", test_ood_predictions),
    ]:
        _require_columns(frame, [args.sample_id_column, args.true_label_column, *probability_columns], name)

    val_probabilities = _normalized_probabilities(val_predictions, probability_columns)
    true_indices = _true_label_indices(
        val_predictions[args.true_label_column].fillna("").astype(str).to_numpy(),
        class_labels,
    )
    valid = true_indices >= 0
    if not valid.any():
        raise ValueError(
            "No validation labels matched probability-column suffixes. "
            "Check --true-label-column and --probability-prefix."
        )

    temperatures = _temperature_grid(args.temperature_min, args.temperature_max, args.num_grid)
    selected_temperature, validation_nll_before, validation_nll_after = _fit_temperature(
        val_probabilities,
        true_indices,
        valid,
        temperatures,
    )

    calibrated_val = _calibrated_output_frame(
        val_predictions,
        probability_columns=probability_columns,
        class_labels=class_labels,
        temperature=selected_temperature,
        true_label_column=args.true_label_column,
        sample_id_column=args.sample_id_column,
    )
    calibrated_test_id = _calibrated_output_frame(
        test_id_predictions,
        probability_columns=probability_columns,
        class_labels=class_labels,
        temperature=selected_temperature,
        true_label_column=args.true_label_column,
        sample_id_column=args.sample_id_column,
    )
    calibrated_test_ood = _calibrated_output_frame(
        test_ood_predictions,
        probability_columns=probability_columns,
        class_labels=class_labels,
        temperature=selected_temperature,
        true_label_column=args.true_label_column,
        sample_id_column=args.sample_id_column,
    )
    calibrated_all = pd.concat([calibrated_test_id, calibrated_test_ood], ignore_index=True)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    calibrated_val.to_csv(args.output_dir / "predictions_val_calibrated.csv", index=False)
    calibrated_test_id.to_csv(args.output_dir / "predictions_test_id_calibrated.csv", index=False)
    calibrated_test_ood.to_csv(args.output_dir / "predictions_test_ood_calibrated.csv", index=False)
    calibrated_all.to_csv(args.output_dir / "predictions_all_calibrated.csv", index=False)

    validation_ece_before = _ece_from_probabilities(val_probabilities[valid], true_indices[valid])
    validation_ece_after = _ece_from_probabilities(
        _apply_temperature(val_probabilities, selected_temperature)[valid],
        true_indices[valid],
    )
    summary = {
        "selected_temperature": selected_temperature,
        "validation_nll_before": validation_nll_before,
        "validation_nll_after": validation_nll_after,
        "validation_ece_before": validation_ece_before,
        "validation_ece_after": validation_ece_after,
        "n_validation_rows": int(len(val_predictions)),
        "valid_probability_rows": int(valid.sum()),
        "temperature_min": float(args.temperature_min),
        "temperature_max": float(args.temperature_max),
        "num_grid": int(args.num_grid),
        "n_temperature_candidates": int(len(temperatures)),
        "seed": int(args.seed),
        "probability_prefix": args.probability_prefix,
        "probability_columns": probability_columns,
        "class_labels": class_labels,
    }
    with (args.output_dir / "temperature_scaling_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(
        "Wrote calibrated predictions to "
        f"{args.output_dir} (T={selected_temperature:.6g}, "
        f"validation NLL {validation_nll_before:.6g}->{validation_nll_after:.6g})"
    )


def _read_predictions(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Prediction CSV not found: {path}")
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    if frame.empty:
        raise ValueError(f"Prediction CSV is empty: {path}")
    return _preserve_string_columns(frame)


def _preserve_string_columns(frame: pd.DataFrame) -> pd.DataFrame:
    preserved = frame.copy()
    for column in SYMBOLIC_STRING_COLUMNS:
        if column in preserved.columns:
            preserved[column] = preserved[column].fillna("").astype(str)
    return preserved


def _probability_columns(frame: pd.DataFrame, prefix: str) -> list[str]:
    if not prefix:
        raise ValueError("--probability-prefix cannot be empty.")
    columns = [column for column in frame.columns if column.startswith(prefix) and len(column) > len(prefix)]
    if not columns:
        raise ValueError(f"No probability columns found with prefix '{prefix}'.")
    return columns


def _normalized_probabilities(frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    values = frame[columns].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if np.isnan(values).any():
        raise ValueError(f"Probability columns contain missing or non-numeric values: {columns}")
    values = np.clip(values, 0.0, None)
    totals = values.sum(axis=1, keepdims=True)
    if np.any(totals <= 0.0):
        raise ValueError("Probability rows must have positive total mass.")
    return values / totals


def _temperature_grid(temperature_min: float, temperature_max: float, num_grid: int) -> np.ndarray:
    if temperature_min <= 0.0 or temperature_max <= 0.0:
        raise ValueError("Temperature bounds must be positive.")
    if temperature_min > temperature_max:
        raise ValueError("--temperature-min must be <= --temperature-max.")
    if num_grid <= 0:
        raise ValueError("--num-grid must be positive.")
    if num_grid == 1:
        grid = np.asarray([(temperature_min + temperature_max) / 2.0], dtype=float)
    else:
        grid = np.geomspace(temperature_min, temperature_max, num_grid)
    if temperature_min <= 1.0 <= temperature_max:
        grid = np.concatenate([grid, np.asarray([1.0], dtype=float)])
    return np.unique(grid)


def _fit_temperature(
    probabilities: np.ndarray,
    true_indices: np.ndarray,
    valid: np.ndarray,
    temperatures: np.ndarray,
) -> tuple[float, float, float]:
    baseline_nll = _negative_log_likelihood(probabilities[valid], true_indices[valid])
    best_temperature = 1.0
    best_nll = float("inf")
    for temperature in temperatures:
        calibrated = _apply_temperature(probabilities, float(temperature))
        nll = _negative_log_likelihood(calibrated[valid], true_indices[valid])
        if nll < best_nll:
            best_temperature = float(temperature)
            best_nll = float(nll)
    return best_temperature, float(baseline_nll), float(best_nll)


def _calibrated_output_frame(
    frame: pd.DataFrame,
    probability_columns: list[str],
    class_labels: list[str],
    temperature: float,
    true_label_column: str,
    sample_id_column: str,
) -> pd.DataFrame:
    _require_columns(frame, [sample_id_column, true_label_column, *probability_columns], "prediction")
    calibrated_probabilities = _apply_temperature(_normalized_probabilities(frame, probability_columns), temperature)
    predicted_indices = calibrated_probabilities.argmax(axis=1)
    predicted_labels = np.asarray([class_labels[index] for index in predicted_indices], dtype=str)
    confidence = calibrated_probabilities[np.arange(len(frame)), predicted_indices]
    output = pd.DataFrame(
        {
            "sample_id": frame[sample_id_column].fillna("").astype(str).to_numpy(),
            "true_label": frame[true_label_column].fillna("").astype(str).to_numpy(),
            "predicted_label": predicted_labels,
            "confidence": confidence,
            "ood_label": _optional_text(frame, "ood_label"),
        }
    )
    for index, column in enumerate(probability_columns):
        output[column] = calibrated_probabilities[:, index]
    return _preserve_string_columns(output)


def _apply_temperature(probabilities: np.ndarray, temperature: float) -> np.ndarray:
    if temperature <= 0.0:
        raise ValueError("Temperature must be positive.")
    log_probabilities = np.log(np.clip(probabilities, EPSILON, 1.0))
    return _softmax(log_probabilities / temperature)


def _softmax(scores: np.ndarray) -> np.ndarray:
    shifted = scores - scores.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def _negative_log_likelihood(probabilities: np.ndarray, true_indices: np.ndarray) -> float:
    clipped = np.clip(probabilities, EPSILON, 1.0)
    return float(-np.log(clipped[np.arange(len(true_indices)), true_indices]).mean())


def _ece_from_probabilities(probabilities: np.ndarray, true_indices: np.ndarray, n_bins: int = 15) -> float | None:
    if len(probabilities) == 0:
        return None
    confidence = probabilities.max(axis=1)
    predicted_indices = probabilities.argmax(axis=1)
    correct = (predicted_indices == true_indices).astype(float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for index in range(n_bins):
        lower = edges[index]
        upper = edges[index + 1]
        if index == n_bins - 1:
            mask = (confidence >= lower) & (confidence <= upper)
        else:
            mask = (confidence >= lower) & (confidence < upper)
        if not mask.any():
            continue
        ece += (mask.sum() / len(confidence)) * abs(float(confidence[mask].mean()) - float(correct[mask].mean()))
    return float(ece)


def _true_label_indices(labels: np.ndarray, class_labels: list[str]) -> np.ndarray:
    label_to_index = {str(label): index for index, label in enumerate(class_labels)}
    return np.asarray([_label_index(str(label), label_to_index, class_labels) for label in labels], dtype=int)


def _label_index(label: str, label_to_index: dict[str, int], class_labels: list[str]) -> int:
    if label in label_to_index:
        return label_to_index[label]
    recovered = _zero_padded_label(label, class_labels)
    if recovered in label_to_index:
        return label_to_index[recovered]
    return -1


def _zero_padded_label(label: str, class_labels: list[str]) -> str:
    if not label.isdigit():
        return label
    matches = [
        candidate
        for candidate in class_labels
        if candidate.isdigit() and len(candidate) > len(label) and int(candidate) == int(label)
    ]
    return matches[0] if len(matches) == 1 else label


def _optional_text(frame: pd.DataFrame, column: str) -> np.ndarray:
    if column not in frame.columns:
        return np.asarray([""] * len(frame), dtype=str)
    return frame[column].fillna("").astype(str).to_numpy()


def _strip_prefix(column: str, prefix: str) -> str:
    return column[len(prefix) :] if column.startswith(prefix) else column


def _require_columns(frame: pd.DataFrame, columns: list[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} CSV is missing required columns: {missing}")


if __name__ == "__main__":
    main()
