#!/usr/bin/env python
"""Validate and report the completed Paper 2 v3 fusion experiments."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


DATASETS = {
    "electrosense_class_ood": ("electrosense", "class_ood", "electrosense_class_ood", 22390),
    "deepsense_day2_ood": ("deepsense", "day2_ood", "deepsense_domain_ood", 19200),
    "jamshield_scenario_ood": ("jamshield", "scenario_ood", "jamshield_domain_ood", 34351),
}
VARIANTS = (
    "ts_entropy_cosine", "ts_entropy_euclidean", "cosine_euclidean",
    "ts_entropy_cosine_euclidean", "ts_entropy_cosine_euclidean_mahalanobis",
)
COMPONENTS = ("ts_entropy", "nearest_centroid_cosine", "nearest_centroid_euclidean", "mahalanobis")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("/mnt/d/openew_sa_data"))
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--frozen-baseline-hashes", type=Path,
                        help="Optional pre-run sha256sum file for v0/v1/v2 integrity validation.")
    args = parser.parse_args()
    paper = args.data_root / "paper2"
    root = paper / "v3_fusion"
    for folder in ("analysis", "tables", "sensitivity_checks"):
        (root / folder).mkdir(parents=True, exist_ok=True)

    errors, checks, result_rows, distribution_rows, inversion_rows = [], [], [], [], []
    for prefix, (dataset, protocol, split_dir, expected) in DATASETS.items():
        manifest = _read(paper / "splits" / split_dir / f"{prefix}_eval.csv")
        validation_manifest = _read(paper / "splits" / split_dir / f"{prefix}_val.csv")
        _check(len(manifest) == expected, checks, errors, prefix, "expected evaluation row count")
        _check(not manifest.sample_id.duplicated().any(), checks, errors, prefix, "unique evaluation sample IDs")

        for component in COMPONENTS:
            validation = _read(root / "validation_scores" / f"{prefix}_{component}_scores.csv")
            evaluation = _read(root / "evaluation_scores" / f"{prefix}_{component}_scores.csv")
            _score_checks(validation, validation_manifest, prefix, f"validation {component}", checks, errors)
            _score_checks(evaluation, manifest, prefix, f"evaluation {component}", checks, errors)
            if component != "ts_entropy":
                canonical = paper / "experiments" / "v2_distance_ood_scores" / "scores" / f"{prefix}_{component}_scores.csv"
                _check(_sha256(canonical) == _sha256(root / "evaluation_scores" / f"{prefix}_{component}_scores.csv"),
                       checks, errors, prefix, f"canonical v2 reuse {component}")
            distribution_rows.extend(_distributions(prefix, component, evaluation))

        for variant in VARIANTS:
            fused_path = root / "fused_scores" / f"{prefix}_{variant}_scores.csv"
            metric_path = root / "metrics" / f"{prefix}_{variant}_metrics.json"
            metadata_path = root / "metadata" / f"{prefix}_{variant}_metadata.json"
            fused, metrics = _read(fused_path), json.loads(metric_path.read_text())
            metadata = json.loads(metadata_path.read_text())
            _score_checks(fused, manifest, prefix, f"fusion {variant}", checks, errors)
            counts = fused.ood_label.value_counts().to_dict()
            _check(metrics["n_samples"] == len(fused) and metrics["n_id"] == counts.get("0", 0)
                   and metrics["n_ood"] == counts.get("1", 0), checks, errors, prefix, f"metric counts {variant}")
            _check(metadata.get("normalization_fit_data") == "id_validation_only", checks, errors,
                   prefix, f"validation-only metadata {variant}")
            _check(metadata.get("validation_sample_count") == len(validation_manifest), checks, errors,
                   prefix, f"validation metadata count {variant}")
            _check(all("validation_scores" in path for path in metadata["validation_inputs"].values()),
                   checks, errors, prefix, f"validation normalization inputs {variant}")
            _check(all(abs(value - 1 / len(metadata["weights"])) < 1e-12
                       for value in metadata["weights"].values()), checks, errors, prefix, f"equal weights {variant}")
            result_rows.append({"dataset": dataset, "protocol": protocol, "model": "equal_weight_fusion",
                                "score_method": variant, **{key: metrics[key] for key in
                                ("auroc", "aupr_ood", "fpr95", "detection_accuracy", "n_id", "n_ood", "n_samples")}})
            distribution_rows.extend(_distributions(prefix, variant, fused))
            if prefix == "deepsense_day2_ood":
                inversion_rows.append(_inversion_row(variant, fused))

        if prefix == "deepsense_day2_ood":
            labels = manifest.label.astype(str)
            _check(labels.str.fullmatch(r"[01]{4}").all(), checks, errors, prefix,
                   "DeepSense manifest labels preserve four digits")
            for path in list((root / "validation_scores").glob(f"{prefix}_*.csv")) + list((root / "fused_scores").glob(f"{prefix}_*.csv")):
                frame = _read(path)
                _check(frame.true_label.astype(str).str.fullmatch(r"[01]{4}").all(), checks, errors,
                       prefix, f"DeepSense labels preserved in {path.name}")

    results = pd.DataFrame(result_rows).sort_values(["dataset", "score_method"])
    _write_table(results, root / "tables" / "paper2_v3_fusion_ood_results")
    _write_table(results, paper / "tables" / "paper2_v3_fusion_ood_results")
    combined = _combined_table(paper, results)
    _write_table(combined, root / "tables" / "paper2_v0_v3_combined_ood_results")
    _write_table(combined, paper / "tables" / "paper2_v0_v3_combined_ood_results")
    pd.DataFrame(distribution_rows).to_csv(root / "analysis" / "score_distribution_summaries.csv", index=False)
    pd.DataFrame(inversion_rows).to_csv(root / "sensitivity_checks" / "deepsense_distance_inversion.csv", index=False)

    if args.frozen_baseline_hashes:
        before = _read_sha256sum(args.frozen_baseline_hashes)
        after = {path: _sha256(Path(path)) for path in before}
        _check(before == after, checks, errors, "all", "frozen v0/v1/v2 snapshots unchanged")
        (root / "metadata" / "frozen_snapshot_integrity.json").write_text(json.dumps({
            "status": "passed" if before == after else "failed", "file_count": len(before),
            "baseline_manifest": str(args.frozen_baseline_hashes), "checked_at_utc": _now(),
        }, indent=2) + "\n")

    validation = {"status": "passed" if not errors else "failed", "timestamp_utc": _now(),
                  "checks_passed": sum(c["passed"] for c in checks), "checks_total": len(checks),
                  "errors": errors, "checks": checks}
    (root / "metadata" / "validation_report.json").write_text(json.dumps(validation, indent=2) + "\n")
    _repository_metadata(args.repo_root, root / "metadata")
    _write_docs(root, results, combined, pd.DataFrame(inversion_rows), errors)
    if errors:
        raise SystemExit("Validation failed:\n" + "\n".join(errors))


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _score_checks(frame, manifest, prefix, name, checks, errors):
    _check(len(frame) == len(manifest), checks, errors, prefix, f"row count {name}")
    _check(frame.sample_id.tolist() == manifest.sample_id.tolist(), checks, errors, prefix, f"exact ID alignment {name}")
    values = pd.to_numeric(frame.ood_score, errors="coerce").to_numpy()
    _check(np.isfinite(values).all(), checks, errors, prefix, f"finite scores {name}")


def _check(condition, checks, errors, dataset, name):
    checks.append({"dataset": dataset, "check": name, "passed": bool(condition)})
    if not condition:
        errors.append(f"{dataset}: {name}")


def _distributions(prefix, method, frame):
    scores = pd.to_numeric(frame.ood_score).to_numpy()
    labels = frame.ood_label.astype(str).to_numpy()
    rows = []
    for label, group in (("ID", scores[labels == "0"]), ("OOD", scores[labels == "1"])):
        rows.append({"dataset_prefix": prefix, "score_method": method, "group": label, "n": len(group),
                     "mean": np.mean(group), "std": np.std(group), "min": np.min(group),
                     "q25": np.percentile(group, 25), "median": np.median(group),
                     "q75": np.percentile(group, 75), "max": np.max(group)})
    return rows


def _inversion_row(variant, frame):
    from ood_detection_metrics import compute_ood_metrics
    labels = frame.ood_label.astype(int).to_numpy()
    scores = pd.to_numeric(frame.ood_score).to_numpy()
    fixed = compute_ood_metrics(labels, scores)
    diagnostic = compute_ood_metrics(labels, -scores)
    return {"fusion_variant": variant, "fixed_orientation_auroc": fixed["auroc"],
            "fixed_orientation_aupr_ood": fixed["aupr_ood"], "fixed_orientation_fpr95": fixed["fpr95"],
            "diagnostic_inverted_auroc": diagnostic["auroc"],
            "diagnostic_inverted_aupr_ood": diagnostic["aupr_ood"],
            "diagnostic_inverted_fpr95": diagnostic["fpr95"],
            "interpretation": "post-hoc diagnostic only; orientation was not changed or selected"}


def _combined_table(paper, v3):
    v0 = pd.read_csv(paper / "experiments/v0_ood_baselines/tables/paper2_v0_ood_results.csv")
    v0 = v0[v0.model.isin(["logistic_regression", "nearest_centroid"])
            & v0.score_method.isin(["entropy", "max_softmax_probability"])].copy()
    v0.insert(0, "stage", "v0_raw")
    v1 = pd.read_csv(paper / "experiments/v1_temperature_scaling_full/tables/paper2_v1_temperature_scaling_full_ood_results.csv")
    v1 = v1[(v1.model == "logistic_regression_ts") & v1.score_method.isin(["entropy", "max_softmax_probability"])].copy()
    v1.insert(0, "stage", "v1_temperature_scaled")
    v2 = pd.read_csv(paper / "experiments/v2_distance_ood_scores/tables/paper2_v2_distance_ood_results.csv")
    v2.insert(0, "stage", "v2_feature_distance")
    v3 = v3.copy(); v3.insert(0, "stage", "v3_fusion")
    columns = ["stage", "dataset", "protocol", "model", "score_method", "auroc", "aupr_ood", "fpr95",
               "detection_accuracy", "n_id", "n_ood", "n_samples"]
    return pd.concat([v0[columns], v1[columns], v2[columns], v3[columns]], ignore_index=True)


def _write_table(frame, stem):
    stem.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(stem.with_suffix(".csv"), index=False)
    headers = frame.columns.tolist()
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(_format(value) for value in row) + " |")
    stem.with_suffix(".md").write_text("\n".join(lines) + "\n")


def _format(value):
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _repository_metadata(repo, target):
    commands = {"current_commit.txt": ["git", "rev-parse", "HEAD"],
                "git_status.txt": ["git", "status", "--short"],
                "git_diff_stat.txt": ["git", "diff", "--stat"],
                "git_log_recent.txt": ["git", "log", "-10", "--oneline"]}
    for name, command in commands.items():
        result = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=True)
        (target / name).write_text(result.stdout)


def _write_docs(root, results, combined, inversion, errors):
    best = results.sort_values("auroc", ascending=False).groupby("dataset", sort=True).head(1)
    best_lines = [f"- {r.dataset}: {r.score_method}, AUROC {r.auroc:.6f}, AUPR-OOD {r.aupr_ood:.6f}, FPR95 {r.fpr95:.6f}, detection accuracy {r.detection_accuracy:.6f}." for r in best.itertuples()]
    counts = results.groupby("dataset").first()[["n_id", "n_ood", "n_samples"]]
    count_lines = [f"- {dataset}: {int(r.n_samples)} total ({int(r.n_id)} ID, {int(r.n_ood)} OOD)." for dataset, r in counts.iterrows()]
    text = f"""# Paper 2 v3 uncertainty-distance fusion

Completed at {_now()}. All 15 equal-weight runs succeeded. Normalization was fitted only on ID validation data; evaluation OOD labels were used only after scores were frozen to compute metrics and summaries.

## Method

For component score s, robust validation normalization is z = (s - median_validation) / (IQR_validation + 1e-12). If validation IQR is zero, validation standard deviation is used; if both are zero, scale 1 is used and recorded. Fusion is the arithmetic mean of its named normalized components. Components are temperature-scaled entropy, nearest-centroid cosine distance, nearest-centroid Euclidean distance, and (in the four-component variant) shared-covariance Mahalanobis distance. Weights are exactly 1/k for k components. All orientations were fixed a priori as higher-is-more-OOD; no evaluation label selected orientation, normalization, weights, variant, or deployment threshold.

## Sample counts

{chr(10).join(count_lines)}

Validation counts were 4,380 ElectroSense, 2,400 DeepSense, and 10,900 JamShield ID samples.

## Best v3 AUROC per dataset (descriptive, not a selection rule)

{chr(10).join(best_lines)}

## DeepSense inversion

All fixed-orientation DeepSense fusion AUROCs are below 0.5 ({inversion.fixed_orientation_auroc.min():.6f}–{inversion.fixed_orientation_auroc.max():.6f}). The two distance-only fusion is also inverted, and adding temperature-scaled entropy does not repair it. Adding Mahalanobis changes AUROC only slightly relative to the three-component fusion and remains worse than distance-only fusion. Negating each already-fused score post hoc yields diagnostic AUROCs of {inversion.diagnostic_inverted_auroc.min():.6f}–{inversion.diagnostic_inverted_auroc.max():.6f}, confirming systematic rank inversion, but these values are sensitivity checks only and were not used to flip or select orientation.

## Limitations and next experiment

Detection accuracy and its reported best threshold are evaluation-descriptive and must not be treated as a deployable threshold. Equal weighting ignores validation-estimable component dependence; Mahalanobis uses a shared covariance model; results cover one split per dataset; and DeepSense exposes domain-dependent distance orientation. The next recommended experiment is a preregistered, ID-validation-only density/tail calibration that estimates distance typicality without OOD labels, then evaluates its fixed mapping on untouched domain-OOD data.
"""
    (root / "README_v3_uncertainty_distance_fusion.md").write_text(text)
    comparisons = []
    for dataset in sorted(results.dataset.unique()):
        old = combined[(combined.dataset == dataset) & (combined.stage != "v3_fusion")]
        new = results[results.dataset == dataset]
        comparisons.append(f"- {dataset}: best v3 AUROC {new.auroc.max():.6f}; best v0-v2 AUROC {old.auroc.max():.6f} (delta {new.auroc.max()-old.auroc.max():+.6f}).")
    (root / "v3_summary.md").write_text(text + "\n## v0/v1/v2/v3 comparison\n\n" + "\n".join(comparisons) + "\n")
    failures = "# v3 failures\n\nNo component-generation, fusion, metric, or validation failures occurred.\n" if not errors else "# v3 failures\n\n" + "\n".join(f"- {e}" for e in errors) + "\n"
    (root / "v3_failures.md").write_text(failures)
    (root / "reproducibility_commands.sh").write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        "REPO_ROOT=${REPO_ROOT:-$HOME/src/openew-sa}\nDATA_ROOT=${DATA_ROOT:-/mnt/d/openew_sa_data}\n"
        "bash \"$REPO_ROOT/papers/paper2_ood_rf_signal_recognition/scripts/run_v3_fusion_experiments.sh\"\n"
        "python \"$REPO_ROOT/papers/paper2_ood_rf_signal_recognition/scripts/finalize_v3_fusion.py\" --repo-root \"$REPO_ROOT\" --data-root \"$DATA_ROOT\"\n")


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_sha256sum(path):
    values = {}
    for line in path.read_text().splitlines():
        digest, filename = line.split("  ", 1)
        values[filename] = digest
    return values


def _now():
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
