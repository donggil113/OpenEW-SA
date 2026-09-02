#!/usr/bin/env python3
"""Render exact, result-backed Markdown fragments from external WiSig analysis files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def metric(value: float) -> str:
    return f"{float(value):.6f}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = pd.read_csv(args.analysis_root / "primary_results_summary.csv")
    day = pd.read_csv(args.analysis_root / "day_results_summary.csv")
    stress = pd.read_csv(args.analysis_root / "stress_results_summary.csv")
    paired = pd.read_csv(args.analysis_root / "paired_fold_seed_differences.csv")
    retention = pd.read_csv(args.analysis_root / "context_retention_results.csv")
    sizes = pd.read_csv(args.analysis_root / "context_size_results.csv")
    compute = pd.read_csv(args.analysis_root / "compute_cost.csv")
    mechanism = pd.read_csv(args.analysis_root / "context_mechanism_summary.csv")
    decision = json.loads((args.analysis_root / "static_receiver_context_decision.json").read_text(encoding="utf-8"))
    completeness = json.loads((args.analysis_root / "run_completeness_audit.json").read_text(encoding="utf-8"))
    bootstrap = pd.read_csv(args.analysis_root / "hierarchical_fold_bootstrap.csv")
    lines = ["# Exact WiSig result sections", "", "## Primary receiver holdout", "", "| Model | Runs | Source-validation macro-F1 | Held-out macro-F1 | Balanced accuracy | Accuracy | ECE |", "|---|---:|---:|---:|---:|---:|---:|"]
    for _, row in summary.sort_values("model_stage").iterrows():
        lines.append(
            f"| {row.model_stage} | {int(row.run_count)} | {metric(row.source_validation_macro_f1_mean)} ± {metric(row.source_validation_macro_f1_std)} | "
            f"{metric(row.held_out_macro_f1_mean)} ± {metric(row.held_out_macro_f1_std)} | {metric(row.held_out_balanced_accuracy_mean)} | "
            f"{metric(row.held_out_accuracy_mean)} | {metric(row.held_out_ece_mean)} |"
        )
    lines.extend(["", "## Paired receiver-fold/seed deltas", "", "| Comparison | n | Mean | Std | Median | Min | Max |", "|---|---:|---:|---:|---:|---:|---:|"])
    for comparison, group in paired.groupby("comparison", sort=True):
        values = group.held_out_macro_f1_delta
        lines.append(f"| {comparison} | {len(values)} | {metric(values.mean())} | {metric(values.std(ddof=1))} | {metric(values.median())} | {metric(values.min())} | {metric(values.max())} |")
    lines.extend(["", "## Day holdout", "", "| Model | Runs | Held-out macro-F1 mean | Std | Median | Min | Max |", "|---|---:|---:|---:|---:|---:|---:|"])
    for _, row in day.sort_values("model_stage").iterrows():
        lines.append(f"| {row.model_stage} | {int(row.run_count)} | {metric(row.held_out_macro_f1_mean)} | {metric(row.held_out_macro_f1_std)} | {metric(row.held_out_macro_f1_median)} | {metric(row.held_out_macro_f1_min)} | {metric(row.held_out_macro_f1_max)} |")
    lines.extend(["", "## Secondary receiver-plus-day stress test", "", "| Model | Runs | Held-out macro-F1 mean | Std |", "|---|---:|---:|---:|"])
    for _, row in stress.sort_values("model_stage").iterrows():
        lines.append(f"| {row.model_stage} | {int(row.run_count)} | {metric(row.held_out_macro_f1_mean)} | {metric(row.held_out_macro_f1_std)} |")
    lines.extend(["", "## Context retention", "", "| Retention | Runs | Held-out macro-F1 mean | Std |", "|---:|---:|---:|---:|"])
    for retention_value, group in retention.groupby("relation_retention", sort=True):
        lines.append(f"| {100*float(retention_value):.0f}% | {len(group)} | {metric(group.held_out_macro_f1.mean())} | {metric(group.held_out_macro_f1.std(ddof=1))} |")
    lines.extend(["", "## Context size", "", "| Context size | Runs | Held-out macro-F1 mean | Std |", "|---:|---:|---:|---:|"])
    for size, group in sizes.groupby("context_size", sort=True):
        lines.append(f"| {int(size)} | {len(group)} | {metric(group.held_out_macro_f1.mean())} | {metric(group.held_out_macro_f1.std(ddof=1))} |")
    lines.extend(["", "## Context mechanism diagnostics", "", "| Model | Coverage | Isolated-anchor fraction | Mean episode size | Attention entropy | Effective context contributors |", "|---|---:|---:|---:|---:|---:|"])
    for _, row in mechanism.sort_values("model_stage").iterrows():
        lines.append(f"| {row.model_stage} | {metric(row.relation_coverage_mean)} | {metric(row.isolated_anchor_fraction_mean)} | {metric(row.episode_size_mean)} | {metric(row.attention_entropy_mean)} | {metric(row.effective_peer_count_mean)} |")
    lines.extend(["", "## Compute", "", "| Model | Parameters | Training/selection seconds mean | Inference seconds mean | Samples/s mean | Peak GPU bytes mean |", "|---|---:|---:|---:|---:|---:|"])
    for _, row in compute.sort_values("model_stage").iterrows():
        lines.append(f"| {row.model_stage} | {int(row.parameter_count)} | {metric(row.training_selection_seconds_mean)} | {metric(row.inference_seconds_mean)} | {metric(row.inference_samples_per_second_mean)} | {int(row.peak_gpu_memory_bytes_mean)} |")
    lines.extend(["", "## Decision audit", "", f"Verdict: **{decision['verdict']}**", ""])
    for name, passed in decision["criteria"].items():
        lines.append(f"- {name}: {'PASS' if passed else 'FAIL'}")
    lines.extend(["", "## Receiver-fold clustered bootstrap (descriptive)", "", "| Comparison | Observed mean delta | 95% interval | Replicates |", "|---|---:|---:|---:|"])
    for _, row in bootstrap.sort_values("comparison").iterrows():
        lines.append(f"| {row.comparison} | {metric(row.observed_mean_delta)} | [{metric(row.ci_2_5)}, {metric(row.ci_97_5)}] | {int(row.bootstrap_replicates)} |")
    lines.extend(["", f"Run completeness: **{completeness['status']}** ({completeness['actual_unique_config_hashes']}/{completeness['expected_unique_runs']} unique configurations).", "", "These are descriptive summaries. No statistical-significance claim is made."])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
