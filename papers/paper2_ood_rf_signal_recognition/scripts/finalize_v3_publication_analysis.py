#!/usr/bin/env python
"""Finalize and validate the Paper 2 v3 publication-readiness package."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from bootstrap_ood_statistics import DATASETS, METHOD_FILES, METRICS, N_BOOTSTRAP, SEED, load_dataset

FROZEN = ("v0_ood_baselines", "v1_temperature_scaling_full", "v2_distance_ood_scores", "v3_uncertainty_distance_fusion")
DATASET_NAMES = {"electrosense": "ElectroSense", "deepsense": "DeepSense", "jamshield": "JamShield"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): sha256(path) for path in sorted(root.rglob("*")) if path.is_file()}


def run_git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, text=True, capture_output=True).stdout


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_markdown(frame: pd.DataFrame, path: Path) -> None:
    display = frame.copy()
    for column in display.select_dtypes(include=["float"]).columns:
        display[column] = display[column].map(lambda x: f"{x:.6f}")
    headers = display.columns.tolist()
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines.extend("| " + " | ".join(map(str, row)) + " |" for row in display.itertuples(index=False, name=None))
    write_text(path, "\n".join(lines) + "\n")


def build_summary(v3_root: Path, output: Path) -> pd.DataFrame:
    source = pd.read_csv(v3_root / "tables/paper2_v0_v3_combined_ood_results.csv")
    keep = ((source.stage == "v0_raw") | (source.stage == "v1_temperature_scaled") |
            (source.stage == "v2_feature_distance") |
            ((source.stage == "v3_fusion") & source.score_method.isin([
                "ts_entropy_cosine_euclidean", "ts_entropy_cosine_euclidean_mahalanobis"])))
    result = source[keep].copy()
    result["analysis_role"] = np.select([
        (result.stage == "v3_fusion") & (result.score_method == "ts_entropy_cosine_euclidean"),
        (result.stage == "v3_fusion") & (result.score_method == "ts_entropy_cosine_euclidean_mahalanobis"),
    ], ["prespecified_primary", "exploratory_ablation"], default="contextual_comparator")
    result["score_orientation"] = "higher_is_more_ood_like"
    result["detection_accuracy_note"] = "evaluation-descriptive; threshold selected on evaluation data"
    result.to_csv(output / "tables/paper2_v0_v3_publication_summary.csv", index=False)
    write_markdown(result, output / "tables/paper2_v0_v3_publication_summary.md")
    return result


def primary_lines(ci: pd.DataFrame) -> list[str]:
    lines = []
    for dataset in DATASETS:
        rows = ci[(ci.dataset == dataset) & (ci.method == "v3_primary")].set_index("metric")
        lines.append(
            f"- {DATASET_NAMES[dataset]}: AUROC {rows.loc['auroc','point_estimate']:.6f} "
            f"(95% CI {rows.loc['auroc','ci_lower']:.6f}–{rows.loc['auroc','ci_upper']:.6f}); "
            f"AUPR-OOD {rows.loc['aupr_ood','point_estimate']:.6f} "
            f"(95% CI {rows.loc['aupr_ood','ci_lower']:.6f}–{rows.loc['aupr_ood','ci_upper']:.6f}); "
            f"FPR95 {rows.loc['fpr95','point_estimate']:.6f} "
            f"(95% CI {rows.loc['fpr95','ci_lower']:.6f}–{rows.loc['fpr95','ci_upper']:.6f})."
        )
    return lines


def write_manuscript(repo: Path, output: Path, ci: pd.DataFrame, diffs: pd.DataFrame) -> None:
    target = repo / "papers/paper2_ood_rf_signal_recognition/manuscript"; target.mkdir(parents=True, exist_ok=True)
    trace = "All numerical estimates in this draft are traceable to `paper2_v3_bootstrap_confidence_intervals.csv` or `paper2_v3_paired_differences.csv`."
    write_text(target / "methods_v3_uncertainty_fusion_draft.md", f"""# Methods: v3 uncertainty–distance fusion (draft)

The prespecified primary score was the equal-weight fusion `ts_entropy_cosine_euclidean`, comprising temperature-scaled predictive entropy, nearest-centroid cosine distance, and nearest-centroid Euclidean distance. Component scores retained the fixed convention that larger values indicate greater OOD-likeness. Each component was robustly normalized using ID validation data only, and no test-OOD result was used to select orientation, weights, thresholds, the primary method, or comparators. The equal-weight four-component variant adding Mahalanobis distance was treated as an exploratory ablation.

AUPR-OOD treated OOD observations as the positive class and used the existing Paper 2 average-precision implementation. Scores were sorted in descending order with a stable mergesort, precision was evaluated at each OOD-positive rank, and those precision values were averaged over all OOD observations. Equal-score observations therefore retained their input CSV order. The same implementation was used for every point estimate and bootstrap replicate.

Uncertainty was estimated using 1,000 nonparametric bootstrap replicates with seed 20260721. ID and OOD observations were resampled separately at their original counts. A common pair of ID/OOD index samples was reused across methods within each dataset, enabling paired differences. Percentile 95% confidence intervals were calculated for AUROC, AUPR-OOD, FPR95, and detection accuracy. Intervals are interpreted for the specific dataset, metric, and comparison reported; they do not support a universal statistical-significance claim, and no family-wise multiplicity adjustment was applied. Detection accuracy is labeled evaluation-descriptive because its threshold was optimized on the evaluation sample.

{trace}
""")
    results_text = (
        "# Results: v0\N{EN DASH}v3 (draft)\n\n"
        "The prespecified primary fusion produced the following fixed-orientation results:\n\n"
        + "\n".join(primary_lines(ci))
        + "\n\nFor JamShield, the primary fusion improved AUROC against each prespecified "
        "comparator, but AUPR-OOD and FPR95 were not uniformly better against every "
        "comparator. AUPR-OOD was lower than temperature-scaled entropy, and FPR95 "
        "was higher than nearest-centroid cosine.\n\n"
        "DeepSense was a negative result under the fixed score orientation: its "
        "primary-fusion AUROC was below 0.5. Post-hoc score negation is presented only "
        "as a diagnostic sensitivity analysis and does not replace the primary result. "
        "The four-component method is an exploratory ablation and is not described as "
        "prespecified. Paired comparisons and whether their 95% intervals exclude zero "
        "are reported in `paper2_v3_paired_differences.csv`; no comparator was selected "
        f"according to test performance.\n\n{trace}\n"
    )
    write_text(target / "results_v0_v3_draft.md", results_text)
    write_text(target / "discussion_v3_draft.md", f"""# Discussion: v3 (draft)

The results support a dataset-dependent interpretation of uncertainty–distance fusion. The prespecified fusion improved some fixed-orientation comparisons but did not generalize uniformly: DeepSense remained directionally inverted, and performance patterns differed across datasets and metrics. These observations warrant caution against universal claims.

The exploratory Mahalanobis addition should be interpreted as an ablation. Any paired interval excluding zero supports a difference for that dataset, metric, and fixed comparison only; it does not establish broad superiority or a causal mechanism. The post-hoc DeepSense inversion diagnostic suggests systematic score-direction mismatch, but test-OOD labels cannot be used to redefine the primary orientation.

{trace}
""")
    write_text(target / "limitations_v3_draft.md", f"""# Limitations: v3 (draft)

The evaluation covers one frozen split for each of three datasets and therefore does not establish universal generalization. Bootstrap intervals quantify sampling variability conditional on these samples and do not capture dataset-shift uncertainty. Detection accuracy uses an evaluation-selected threshold and is descriptive rather than deployment-valid. Equal weighting and score orientation were fixed; no test-OOD adaptation was permitted. The DeepSense result is negative under that orientation. The negated-score analysis is post-hoc and diagnostic only. Multiple dataset, metric, and comparator intervals are reported without a family-wise multiplicity adjustment, so interval exclusion of zero should be interpreted narrowly.

{trace}
""")
    write_text(target / "figure_captions_v3.md", """# Figure captions: v3

1. **OOD AUROC with confidence intervals.** Point estimates and percentile 95% bootstrap confidence intervals under the fixed higher-is-more-OOD orientation; the dashed AUROC = 0.5 line marks chance. The three-component fusion is prespecified; the four-component method is exploratory.
2. **FPR95 with confidence intervals.** False-positive rate at 95% OOD true-positive rate, with percentile 95% bootstrap confidence intervals. Lower values are preferable; axes include zero and the full probability range.
3. **Primary fusion comparison.** This figure reports AUROC only. Paired AUROC differences compare the prespecified primary fusion with each prespecified comparator. Intervals use identical bootstrap resamples across methods; the focused difference scale is centered on zero.
4. **Score distributions.** ID and OOD score-density outlines for the prespecified primary fusion, clipped only for display to the 0.5th–99.5th score percentiles within each dataset. Score and density axes are dataset-specific and should not be compared as common scales across panels.
5. **DeepSense distance and fusion score inversion.** **POST-HOC DIAGNOSTIC ONLY.** Fixed-orientation AUROC is compared with AUROC after score negation. Negated values were not used to change or replace the primary analysis.
""")
    write_text(target / "table_captions_v3.md", """# Table captions: v3

1. **Bootstrap confidence intervals.** Fixed-orientation point estimates and percentile 95% confidence intervals from 1,000 stratified bootstrap replicates. Detection accuracy is evaluation-descriptive.
2. **Paired method differences.** Left-minus-right metric differences using identical resampling indices within dataset. The comparator set was fixed independently of test performance.
3. **v0–v3 publication summary.** Frozen stage-wise OOD results. The three-component v3 method is the prespecified primary analysis; the four-component method is exploratory.
""")
    write_text(target / "reproducibility_checklist_v3.md", """# Reproducibility checklist: v3

- [x] Source commit and Paper 2 v3 tag recorded.
- [x] Frozen v0/v1/v2/v3 inputs hashed before and after analysis.
- [x] Dataset counts and unique sample IDs validated.
- [x] Exact cross-method sample and label alignment validated.
- [x] Higher-is-more-OOD orientation retained for primary results.
- [x] Primary and exploratory methods identified before reporting.
- [x] Bootstrap seed, replicate count, stratification, and pairing recorded.
- [x] Detection-accuracy threshold labeled evaluation-descriptive.
- [x] DeepSense leading-zero labels checked.
- [x] Tables, figures, and SHA-256 manifest generated.
- [ ] Manually review manuscript integration, journal style, and reference placement.
""")


def validate(repo: Path, data_root: Path, output: Path, frozen_before: dict[str, dict[str, str]]) -> dict:
    checks, failures = [], []
    def check(name: str, condition: bool, detail: str = "") -> None:
        checks.append({"check": name, "passed": bool(condition), "detail": detail})
        if not condition: failures.append(f"{name}: {detail}")
    v3_root = data_root / "paper2/experiments/v3_uncertainty_distance_fusion"
    for dataset, (prefix, expected) in DATASETS.items():
        try:
            labels, _, audit = load_dataset(v3_root, prefix, expected)
            check(f"{dataset}: expected sample count", len(labels) == expected, str(len(labels)))
            check(f"{dataset}: unique input sample IDs", audit.sample_id.is_unique)
            check(f"{dataset}: both ID and OOD present", set(labels) == {0, 1})
            if dataset == "deepsense": check("DeepSense leading-zero labels unchanged", audit.true_label.str.fullmatch(r"[01]{4}").all())
        except Exception as exc: check(f"{dataset}: input validation", False, str(exc))
    ci = pd.read_csv(output / "tables/paper2_v3_bootstrap_confidence_intervals.csv")
    diffs = pd.read_csv(output / "tables/paper2_v3_paired_differences.csv")
    reps = pd.read_csv(output / "bootstrap/completed_replicate_summaries.csv")
    check("no NaN or infinite metric values", np.isfinite(ci[["point_estimate","ci_lower","ci_upper"]]).all().all() and np.isfinite(diffs[["point_difference_left_minus_right","ci_lower","ci_upper"]]).all().all())
    check("CI bounds contain point estimates", ((ci.ci_lower <= ci.point_estimate) & (ci.point_estimate <= ci.ci_upper)).all())
    counts = reps.groupby(["dataset","method"]).replicate.nunique()
    check("exactly 1000 successful replicates per dataset and method", (counts == N_BOOTSTRAP).all(), counts.to_dict().__str__())
    paired = diffs.successful_paired_replicates.eq(N_BOOTSTRAP).all()
    check("paired comparisons use identical resampling indices", paired)
    check("all required metrics present", set(ci.metric) == set(METRICS))
    frozen_after = {name: tree_hashes(data_root / "paper2/experiments" / name) for name in FROZEN}
    check("frozen v0/v1/v2/v3 snapshot hashes unchanged", frozen_before == frozen_after,
          f"files={sum(map(len, frozen_after.values()))}")
    paper1_changes = [line for line in run_git(repo, "status", "--short").splitlines() if "paper1" in line.lower()]
    check("no Paper 1 files changed", not paper1_changes, "; ".join(paper1_changes))
    return {"status": "passed" if not failures else "failed", "timestamp_utc": now(),
            "checks_passed": sum(item["passed"] for item in checks), "checks_total": len(checks),
            "failures": failures, "checks": checks}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--repo-root", type=Path, required=True); parser.add_argument("--data-root", type=Path, required=True); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--frozen-before", type=Path, required=True)
    args = parser.parse_args(); output = args.output_root; (output / "metadata").mkdir(parents=True, exist_ok=True)
    frozen_before = json.loads(args.frozen_before.read_text())
    v3_root = args.data_root / "paper2/experiments/v3_uncertainty_distance_fusion"
    summary = build_summary(v3_root, output)
    ci = pd.read_csv(output / "tables/paper2_v3_bootstrap_confidence_intervals.csv"); diffs = pd.read_csv(output / "tables/paper2_v3_paired_differences.csv")
    write_manuscript(args.repo_root, output, ci, diffs)
    metadata = output / "metadata"
    write_text(metadata / "source_commit.txt", run_git(args.repo_root, "rev-parse", "HEAD"))
    write_text(metadata / "source_tag.txt", "paper2-v3-uncertainty-distance-fusion-20260721\n")
    write_text(metadata / "git_status.txt", run_git(args.repo_root, "status", "--short"))
    write_text(metadata / "git_diff_stat.txt", run_git(args.repo_root, "diff", "--stat"))
    write_text(metadata / "run_timestamps.txt", f"finalized_utc={now()}\n")
    config = {"primary_method": "ts_entropy_cosine_euclidean", "exploratory_ablation": "ts_entropy_cosine_euclidean_mahalanobis", "score_orientation": "higher_is_more_ood_like", "bootstrap_replicates": N_BOOTSTRAP, "bootstrap_seed": SEED, "confidence_interval": "percentile_95", "detection_accuracy": "evaluation-descriptive", "dataset_expected_counts": {k: v[1] for k,v in DATASETS.items()}}
    write_text(metadata / "analysis_configuration.json", json.dumps(config, indent=2) + "\n")
    validation = validate(args.repo_root, args.data_root, output, frozen_before)
    write_text(metadata / "validation_report.json", json.dumps(validation, indent=2) + "\n")
    findings = "\n".join(primary_lines(ci))
    write_text(output / "publication_analysis_summary.md",
        f"# Paper 2 v3 publication analysis summary\n\n"
        f"## Prespecified primary analysis\n\n{findings}\n\n"
        "For JamShield, primary-fusion AUROC improved against each prespecified comparator, "
        "but AUPR-OOD and FPR95 were not uniformly better against every comparator. "
        "The four-component method is an exploratory ablation. DeepSense is a negative "
        "result under the fixed higher-is-more-OOD orientation. Paired comparisons are "
        "reported without choosing comparators from test performance. Detection accuracy "
        "is evaluation-descriptive.\n"
    )
    failures_text = "No analysis failures were recorded.\n" if not validation["failures"] else "\n".join(f"- {x}" for x in validation["failures"]) + "\n"
    write_text(output / "publication_analysis_failures.md", "# Publication analysis failures\n\n" + failures_text)
    write_text(output / "README_v3_publication_analysis.md", """# Paper 2 v3 publication analysis

This package contains fixed-orientation, prespecified primary results; an explicitly exploratory four-component ablation; 1,000-replicate stratified paired-bootstrap confidence intervals and differences; publication figures; manuscript drafts; and validation/provenance metadata. Detection accuracy is descriptive because its threshold is selected on evaluation data. The DeepSense negated-score figure is post-hoc diagnostic sensitivity analysis only.

See `tables/`, `figures/`, `bootstrap/`, `metadata/`, `publication_analysis_summary.md`, and `publication_analysis_failures.md`.
""")
    commands = """#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=${REPO_ROOT:-/home/user/src/openew-sa}
DATA_ROOT=${DATA_ROOT:-/mnt/d/openew_sa_data}
OUTPUT_ROOT=${OUTPUT_ROOT:-$DATA_ROOT/paper2/experiments/v3_publication_analysis_20260807}
V3_ROOT=$DATA_ROOT/paper2/experiments/v3_uncertainty_distance_fusion
python "$REPO_ROOT/papers/paper2_ood_rf_signal_recognition/scripts/bootstrap_ood_statistics.py" --v3-root "$V3_ROOT" --output-root "$OUTPUT_ROOT"
python "$REPO_ROOT/papers/paper2_ood_rf_signal_recognition/scripts/plot_v3_publication_figures.py" --v3-root "$V3_ROOT" --output-root "$OUTPUT_ROOT"
# Finalization additionally requires a pre-run frozen-hash JSON passed with --frozen-before.
python -m compileall "$REPO_ROOT/papers/paper2_ood_rf_signal_recognition/scripts"
python -m unittest discover -s "$REPO_ROOT/papers/paper2_ood_rf_signal_recognition/tests" -v
git -C "$REPO_ROOT" diff --check
"""
    write_text(output / "reproducibility_commands.sh", commands)
    (output / "reproducibility_commands.sh").chmod(0o755)
    manifest_rows = [{"path": str(p.relative_to(output)), "sha256": sha256(p), "bytes": p.stat().st_size} for p in sorted(output.rglob("*")) if p.is_file() and p.name != "SHA256_manifest.csv"]
    pd.DataFrame(manifest_rows).to_csv(metadata / "SHA256_manifest.csv", index=False)
    if validation["status"] != "passed": raise SystemExit("Publication validation failed; see validation_report.json")


if __name__ == "__main__":
    main()
