#!/usr/bin/env python
"""Fuse OOD score components using validation-only normalization."""

from __future__ import annotations

import argparse
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

EPSILON = 1e-12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fuse higher-is-OOD scores with normalization fitted only on ID validation data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--validation-component", action="append", required=True, metavar="NAME=CSV_PATH")
    parser.add_argument("--evaluation-component", action="append", required=True, metavar="NAME=CSV_PATH")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metadata-output", required=True, type=Path)
    parser.add_argument("--normalization", choices=("robust_zscore", "zscore"), default="robust_zscore")
    parser.add_argument("--weights", action="append", metavar="COMPONENT=VALUE")
    parser.add_argument("--sample-id-column", default="sample_id")
    parser.add_argument("--score-column", default="ood_score")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validation_paths = _parse_named_values(args.validation_component, "validation component", Path)
    evaluation_paths = _parse_named_values(args.evaluation_component, "evaluation component", Path)
    if set(validation_paths) != set(evaluation_paths):
        raise ValueError("Validation and evaluation component names must match exactly.")
    component_names = list(validation_paths)
    weights = _weights(component_names, args.weights)

    validation = {
        name: _read_component(path, args.sample_id_column, args.score_column, require_ood_label=False)
        for name, path in validation_paths.items()
    }
    evaluation = {
        name: _read_component(path, args.sample_id_column, args.score_column, require_ood_label=True)
        for name, path in evaluation_paths.items()
    }
    _require_identical_ids(validation, "validation", args.sample_id_column)
    _require_identical_ids(evaluation, "evaluation", args.sample_id_column)

    base = evaluation[component_names[0]].copy()
    ids = base[args.sample_id_column].tolist()
    _require_consistent_evaluation_labels(evaluation, ids, args.sample_id_column)
    output = pd.DataFrame({"sample_id": ids})
    if "true_label" in base.columns:
        output["true_label"] = base.set_index(args.sample_id_column).loc[ids, "true_label"].astype(str).to_numpy()
    output["ood_label"] = base.set_index(args.sample_id_column).loc[ids, "ood_label"].astype(str).to_numpy()

    parameters: dict[str, dict[str, float | str]] = {}
    fallback_warnings: list[str] = []
    normalized_columns: list[str] = []
    for name in component_names:
        validation_scores = _ordered_scores(validation[name], validation[name][args.sample_id_column].tolist(), args)
        evaluation_scores = _ordered_scores(evaluation[name], ids, args)
        params, warning = _fit_normalization(validation_scores, args.normalization, name)
        parameters[name] = params
        if warning:
            fallback_warnings.append(warning)
            warnings.warn(warning, RuntimeWarning)
        raw_column = f"{name}_raw_score"
        normalized_column = f"{name}_normalized_score"
        output[raw_column] = evaluation_scores
        output[normalized_column] = (evaluation_scores - float(params["center"])) / float(params["scale"])
        normalized_columns.append(normalized_column)

    output["ood_score"] = sum(output[column] * weights[name] for name, column in zip(component_names, normalized_columns))
    output["fusion_method"] = "+".join(component_names)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)

    metadata = {
        "validation_inputs": {name: str(path.resolve()) for name, path in validation_paths.items()},
        "evaluation_inputs": {name: str(path.resolve()) for name, path in evaluation_paths.items()},
        "normalization": args.normalization,
        "normalization_parameters": parameters,
        "fallback_warnings": fallback_warnings,
        "weights": weights,
        "validation_sample_count": len(next(iter(validation.values()))),
        "evaluation_sample_count": len(output),
        "seed": args.seed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "score_orientation": "higher_is_more_ood_like",
        "normalization_fit_data": "id_validation_only",
    }
    args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
    with args.metadata_output.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"Wrote {len(output)} fused scores to {args.output}")
    print(f"Wrote metadata to {args.metadata_output}")


def _parse_named_values(values, description, converter):
    parsed = {}
    for item in values or []:
        if "=" not in item:
            raise ValueError(f"Invalid {description} '{item}'; expected name=value.")
        name, value = item.split("=", 1)
        if not name or not value or name in parsed:
            raise ValueError(f"Invalid or duplicate {description} '{item}'.")
        parsed[name] = converter(value)
    return parsed


def _read_component(path: Path, id_column: str, score_column: str, require_ood_label: bool) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = [id_column, score_column] + (["ood_label"] if require_ood_label else [])
    missing = [column for column in required if column not in frame]
    if missing:
        raise ValueError(f"Component {path} is missing required columns: {missing}")
    if frame.empty:
        raise ValueError(f"Component {path} is empty.")
    if frame[id_column].eq("").any() or frame[id_column].duplicated().any():
        duplicates = frame.loc[frame[id_column].duplicated(keep=False), id_column].unique().tolist()
        raise ValueError(f"Component {path} contains blank or duplicate sample IDs: {duplicates[:5]}")
    scores = pd.to_numeric(frame[score_column], errors="coerce")
    if not np.isfinite(scores.to_numpy()).all():
        raise ValueError(f"Component {path} contains non-finite scores.")
    frame = frame.copy()
    frame[score_column] = scores
    return frame


def _require_identical_ids(components, split_name, id_column):
    names = list(components)
    reference = set(components[names[0]][id_column])
    for name in names[1:]:
        current = set(components[name][id_column])
        missing, extra = sorted(reference - current), sorted(current - reference)
        if missing or extra:
            raise ValueError(
                f"{split_name.capitalize()} sample ID mismatch for {name}: "
                f"missing={missing[:5]}, extra={extra[:5]}"
            )


def _require_consistent_evaluation_labels(components, ids, id_column):
    reference_name = next(iter(components))
    reference = components[reference_name].set_index(id_column).loc[ids, "ood_label"].astype(str)
    for name, frame in components.items():
        labels = frame.set_index(id_column).loc[ids, "ood_label"].astype(str)
        if not labels.equals(reference):
            raise ValueError(f"Evaluation ood_label values are inconsistent between {reference_name} and {name}.")


def _ordered_scores(frame, ids, args):
    return frame.set_index(args.sample_id_column).loc[ids, args.score_column].to_numpy(dtype=float)


def _fit_normalization(scores: np.ndarray, method: str, name: str):
    median = float(np.median(scores))
    mean = float(np.mean(scores))
    q25, q75 = np.percentile(scores, [25, 75])
    iqr = float(q75 - q25)
    std = float(np.std(scores))
    warning = None
    if method == "zscore":
        center, scale, scale_source = mean, std, "validation_std"
        if not np.isfinite(scale) or scale == 0:
            scale, scale_source = 1.0, "unit_fallback"
            warning = f"Component '{name}' validation standard deviation is zero/non-finite; using scale=1."
    else:
        center, scale, scale_source = median, iqr + EPSILON, "validation_iqr_plus_epsilon"
        if not np.isfinite(iqr) or iqr == 0:
            scale, scale_source = std, "validation_std_fallback"
            if not np.isfinite(scale) or scale == 0:
                scale, scale_source = 1.0, "unit_fallback"
                warning = f"Component '{name}' validation IQR and standard deviation are zero/non-finite; using scale=1."
    return {
        "median": median, "mean": mean, "iqr": iqr, "std": std,
        "center": float(center), "scale": float(scale), "scale_source": scale_source,
        "epsilon": EPSILON,
    }, warning


def _weights(component_names, specifications):
    if not specifications:
        return {name: 1.0 / len(component_names) for name in component_names}
    parsed = _parse_named_values(specifications, "weight", float)
    if set(parsed) != set(component_names):
        raise ValueError("Explicit weights must specify every component exactly once.")
    values = np.asarray(list(parsed.values()), dtype=float)
    if not np.isfinite(values).all() or (values < 0).any() or values.sum() <= 0:
        raise ValueError("Weights must be finite, non-negative, and have a positive sum.")
    total = float(values.sum())
    return {name: float(parsed[name] / total) for name in component_names}


if __name__ == "__main__":
    main()
