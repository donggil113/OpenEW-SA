#!/usr/bin/env python
"""Paired stratified bootstrap statistics for Paper 2 v3 OOD scores."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve

from ood_detection_metrics import _average_precision

SEED = 20260721
N_BOOTSTRAP = 1000
DATASETS = {
    "electrosense": ("electrosense_class_ood", 22390),
    "deepsense": ("deepsense_day2_ood", 19200),
    "jamshield": ("jamshield_scenario_ood", 34351),
}
METHOD_FILES = {
    "temperature_scaled_entropy": ("evaluation_scores", "ts_entropy"),
    "nearest_centroid_cosine": ("evaluation_scores", "nearest_centroid_cosine"),
    "nearest_centroid_euclidean": ("evaluation_scores", "nearest_centroid_euclidean"),
    "v3_primary": ("fused_scores", "ts_entropy_cosine_euclidean"),
    "four_component_exploratory": (
        "fused_scores", "ts_entropy_cosine_euclidean_mahalanobis"
    ),
}
COMPARISONS = {
    "v3_primary_vs_temperature_scaled_entropy": ("v3_primary", "temperature_scaled_entropy"),
    "v3_primary_vs_nearest_centroid_cosine": ("v3_primary", "nearest_centroid_cosine"),
    "v3_primary_vs_nearest_centroid_euclidean": ("v3_primary", "nearest_centroid_euclidean"),
    "four_component_exploratory_vs_v3_primary": ("four_component_exploratory", "v3_primary"),
}
METRICS = ("auroc", "aupr_ood", "fpr95", "detection_accuracy")


def compute_metrics(labels: np.ndarray, scores: np.ndarray) -> dict[str, float]:
    """Compute metrics with higher score fixed as more OOD-like."""
    labels = np.asarray(labels, dtype=np.int8)
    scores = np.asarray(scores, dtype=float)
    if labels.shape != scores.shape or set(np.unique(labels)) != {0, 1}:
        raise ValueError("labels and scores must align and contain ID=0 and OOD=1")
    if not np.isfinite(scores).all():
        raise ValueError("scores contain NaN or infinite values")
    fpr, tpr, _ = roc_curve(labels, scores, pos_label=1, drop_intermediate=False)
    qualifying = fpr[tpr >= 0.95]
    fpr95 = float(qualifying.min()) if len(qualifying) else 1.0
    accuracy, _ = best_detection_accuracy(labels, scores)
    return {
        "auroc": float(roc_auc_score(labels, scores)),
        # Keep AUPR-OOD exactly aligned with the existing Paper 2 implementation,
        # including its stable input-order handling of tied scores.
        "aupr_ood": _average_precision(labels, scores),
        "fpr95": fpr95,
        "detection_accuracy": accuracy,
    }


def best_detection_accuracy(labels: np.ndarray, scores: np.ndarray) -> tuple[float, float]:
    """Return evaluation-best accuracy and threshold for the rule score >= threshold."""
    order = np.argsort(-scores, kind="mergesort")
    y = labels[order].astype(np.int64)
    s = scores[order]
    n = len(y)
    n_id = int((y == 0).sum())
    cumulative_correct = n_id + np.cumsum(np.where(y == 1, 1, -1))
    boundaries = np.r_[np.flatnonzero(s[:-1] != s[1:]), n - 1]
    correct = np.r_[n_id, cumulative_correct[boundaries]]
    best_value = correct.max()
    # Among equally accurate finite cutoffs, retain the smallest threshold,
    # matching the existing Paper 2 metric implementation's ascending scan.
    best_position = int(np.flatnonzero(correct == best_value)[-1])
    if best_position == 0:
        return float(correct[0] / n), float("inf")
    boundary = boundaries[best_position - 1]
    return float(correct[best_position] / n), float(s[boundary])


def percentile_interval(values: np.ndarray, level: float = 0.95) -> tuple[float, float]:
    """Percentile interval implemented with NumPy; SciPy is not required."""
    alpha = (1.0 - level) / 2.0
    low, high = np.percentile(np.asarray(values, dtype=float), [100 * alpha, 100 * (1 - alpha)])
    return float(low), float(high)


def load_dataset(v3_root: Path, prefix: str, expected: int) -> tuple[np.ndarray, dict[str, np.ndarray], pd.DataFrame]:
    """Load and validate exact sample alignment for all compared methods."""
    frames: dict[str, pd.DataFrame] = {}
    canonical_ids = canonical_labels = canonical_true = None
    for method, (folder, suffix) in METHOD_FILES.items():
        path = v3_root / folder / f"{prefix}_{suffix}_scores.csv"
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        required = {"sample_id", "true_label", "ood_label", "ood_score"}
        if not required.issubset(frame.columns):
            raise ValueError(f"{path} lacks columns {sorted(required - set(frame.columns))}")
        if len(frame) != expected or frame.sample_id.duplicated().any():
            raise ValueError(f"{path} has invalid count or duplicate sample IDs")
        ids = frame.sample_id.to_numpy()
        labels = frame.ood_label.astype(int).to_numpy()
        true_labels = frame.true_label.to_numpy()
        if canonical_ids is None:
            canonical_ids, canonical_labels, canonical_true = ids, labels, true_labels
        elif not (np.array_equal(ids, canonical_ids) and np.array_equal(labels, canonical_labels)
                  and np.array_equal(true_labels, canonical_true)):
            raise ValueError(f"exact sample alignment failed for {path}")
        scores = pd.to_numeric(frame.ood_score, errors="coerce").to_numpy()
        if not np.isfinite(scores).all():
            raise ValueError(f"non-finite score in {path}")
        frames[method] = frame
    if prefix.startswith("deepsense") and not pd.Series(canonical_true).str.fullmatch(r"[01]{4}").all():
        raise ValueError("DeepSense leading-zero labels were not preserved")
    score_map = {method: pd.to_numeric(frame.ood_score).to_numpy() for method, frame in frames.items()}
    audit = frames["v3_primary"][["sample_id", "true_label", "ood_label"]].copy()
    return canonical_labels.astype(np.int8), score_map, audit


def bootstrap_dataset(dataset: str, labels: np.ndarray, scores: dict[str, np.ndarray],
                      output_dir: Path, n_bootstrap: int = N_BOOTSTRAP, seed: int = SEED,
                      checkpoint_every: int = 100) -> pd.DataFrame:
    """Run or resume a paired, group-stratified bootstrap for one dataset."""
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = output_dir / f"{dataset}_replicates.csv"
    state_path = output_dir / f"{dataset}_rng_state.json"
    if checkpoint.exists():
        rows = pd.read_csv(checkpoint).to_dict("records")
        completed = 0 if not rows else int(max(row["replicate"] for row in rows)) + 1
        rng = np.random.default_rng()
        rng.bit_generator.state = json.loads(state_path.read_text())
    else:
        rows, completed = [], 0
        dataset_offset = sorted(DATASETS).index(dataset) * 1_000_003
        rng = np.random.default_rng(seed + dataset_offset)
    id_positions = np.flatnonzero(labels == 0)
    ood_positions = np.flatnonzero(labels == 1)
    for replicate in range(completed, n_bootstrap):
        sampled = np.concatenate([
            rng.choice(id_positions, len(id_positions), replace=True),
            rng.choice(ood_positions, len(ood_positions), replace=True),
        ])
        sampled_labels = labels[sampled]
        for method, method_scores in scores.items():
            result = compute_metrics(sampled_labels, method_scores[sampled])
            rows.append({"dataset": dataset, "replicate": replicate, "method": method, **result})
        if (replicate + 1) % checkpoint_every == 0 or replicate + 1 == n_bootstrap:
            pd.DataFrame(rows).to_csv(checkpoint, index=False)
            state_path.write_text(json.dumps(rng.bit_generator.state, indent=2) + "\n")
    return pd.DataFrame(rows)


def summarize(labels_by_dataset: dict[str, np.ndarray], scores_by_dataset: dict[str, dict[str, np.ndarray]],
              replicates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ci_rows, difference_rows = [], []
    for dataset in sorted(labels_by_dataset):
        labels, score_map = labels_by_dataset[dataset], scores_by_dataset[dataset]
        for method, scores in score_map.items():
            points = compute_metrics(labels, scores)
            subset = replicates[(replicates.dataset == dataset) & (replicates.method == method)]
            for metric in METRICS:
                low, high = percentile_interval(subset[metric].to_numpy())
                ci_rows.append({
                    "dataset": dataset, "method": method, "analysis_role": (
                        "prespecified_primary" if method == "v3_primary" else
                        "exploratory_ablation" if method == "four_component_exploratory" else "prespecified_comparator"
                    ), "metric": metric, "point_estimate": points[metric], "ci_lower": low,
                    "ci_upper": high, "confidence_level": 0.95, "successful_replicates": len(subset),
                    "score_orientation": "higher_is_more_ood_like",
                    "threshold_note": "evaluation-descriptive" if metric == "detection_accuracy" else "not_applicable",
                })
        for comparison, (left, right) in COMPARISONS.items():
            left_rows = replicates[(replicates.dataset == dataset) & (replicates.method == left)].sort_values("replicate")
            right_rows = replicates[(replicates.dataset == dataset) & (replicates.method == right)].sort_values("replicate")
            if not np.array_equal(left_rows.replicate.to_numpy(), right_rows.replicate.to_numpy()):
                raise ValueError(f"paired replicate alignment failed: {dataset} {comparison}")
            left_point, right_point = compute_metrics(labels, score_map[left]), compute_metrics(labels, score_map[right])
            for metric in METRICS:
                diffs = left_rows[metric].to_numpy() - right_rows[metric].to_numpy()
                low, high = percentile_interval(diffs)
                difference_rows.append({
                    "dataset": dataset, "comparison": comparison, "left_method": left,
                    "right_method": right, "metric": metric,
                    "point_difference_left_minus_right": left_point[metric] - right_point[metric],
                    "ci_lower": low, "ci_upper": high, "confidence_level": 0.95,
                    "successful_paired_replicates": len(diffs),
                    "interval_excludes_zero": bool(low > 0 or high < 0),
                    "score_orientation": "higher_is_more_ood_like",
                    "threshold_note": "evaluation-descriptive" if metric == "detection_accuracy" else "not_applicable",
                })
    return pd.DataFrame(ci_rows), pd.DataFrame(difference_rows)


def _write_markdown(frame: pd.DataFrame, path: Path) -> None:
    formatted = frame.copy()
    for column in formatted.select_dtypes(include=["float"]).columns:
        formatted[column] = formatted[column].map(lambda x: f"{x:.6f}")
    headers = formatted.columns.tolist()
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines += ["| " + " | ".join(map(str, row)) + " |" for row in formatted.itertuples(index=False, name=None)]
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v3-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--n-bootstrap", type=int, default=N_BOOTSTRAP)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    bootstrap_dir, tables_dir = args.output_root / "bootstrap", args.output_root / "tables"
    bootstrap_dir.mkdir(parents=True, exist_ok=True); tables_dir.mkdir(parents=True, exist_ok=True)
    labels_by_dataset, scores_by_dataset, all_replicates = {}, {}, []
    for dataset, (prefix, expected) in DATASETS.items():
        labels, scores, _ = load_dataset(args.v3_root, prefix, expected)
        labels_by_dataset[dataset], scores_by_dataset[dataset] = labels, scores
        all_replicates.append(bootstrap_dataset(dataset, labels, scores, bootstrap_dir,
                                                args.n_bootstrap, args.seed))
    replicates = pd.concat(all_replicates, ignore_index=True)
    replicates.to_csv(bootstrap_dir / "completed_replicate_summaries.csv", index=False)
    metadata = {"seed": args.seed, "replicates": args.n_bootstrap, "resampling": "ID and OOD separately",
                "paired_indices": "one shared sampled-index vector per dataset and replicate across all methods",
                "dataset_seed_offsets": {name: sorted(DATASETS).index(name) * 1_000_003 for name in DATASETS}}
    (bootstrap_dir / "deterministic_seed_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    ci, differences = summarize(labels_by_dataset, scores_by_dataset, replicates)
    for frame, name in ((ci, "paper2_v3_bootstrap_confidence_intervals"),
                        (differences, "paper2_v3_paired_differences")):
        frame.to_csv(tables_dir / f"{name}.csv", index=False)
        _write_markdown(frame, tables_dir / f"{name}.md")


if __name__ == "__main__":
    main()
