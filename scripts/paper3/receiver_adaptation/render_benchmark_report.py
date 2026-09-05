#!/usr/bin/env python3
"""Render deterministic post-unblind benchmark tables, figures, and manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from openew.paper3.receiver_adaptation.reporting import (
    PRIMARY_REPORT_MODELS,
    analysis_manifest,
    compute_frozen_calibration,
    receiver_difficulty,
    summarize_calibration,
    summarize_catastrophic,
    summarize_compute,
    summarize_hardware,
    summarize_receiver_results,
    summarize_support_budgets,
    validate_unblinded_analysis,
)


def _write_figure(fig: plt.Figure, root: Path, name: str) -> None:
    fig.tight_layout()
    fig.savefig(root / f"{name}.png", dpi=220, bbox_inches="tight")
    fig.savefig(root / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def render(args: argparse.Namespace) -> dict[str, object]:
    analysis = Path(args.benchmark_root) / "analysis"
    figures = analysis / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    validation = validate_unblinded_analysis(analysis)
    averaged = pd.read_csv(analysis / "benchmark_receiver_averaged_results.csv", dtype={"receiver_id": "string"})
    seed = pd.read_csv(analysis / "benchmark_receiver_seed_results.csv", dtype={"receiver_id": "string"})
    budget = pd.read_csv(analysis / "support_budget_all_methods.csv", dtype={"receiver_id": "string"})
    catastrophic = pd.read_csv(analysis / "catastrophic_adaptation.csv", dtype={"receiver_id": "string"})
    oracle = pd.read_csv(analysis / "supervised_oracle_receiver_seed_results.csv", dtype={"receiver_id": "string"})

    primary = summarize_receiver_results(averaged[averaged.model.isin(PRIMARY_REPORT_MODELS)])
    hardware = summarize_hardware(averaged[averaged.model.isin(PRIMARY_REPORT_MODELS)])
    budget_summary = summarize_support_budgets(budget)
    catastrophic_summary = summarize_catastrophic(catastrophic)
    difficulty, correlations = receiver_difficulty(averaged)
    frozen_calibration = compute_frozen_calibration(converted_root=args.converted_root, split_root=args.split_root, frozen_run_root=args.frozen_run_root)
    calibration = summarize_calibration(seed, frozen_calibration, oracle)
    compute = summarize_compute(frozen_compute_path=Path(args.frozen_analysis_root) / "compute_budget_summary.csv", benchmark_root=args.benchmark_root)

    outputs = {
        "primary_receiver_summary.csv": primary,
        "hardware_family_summary.csv": hardware,
        "support_budget_summary.csv": budget_summary,
        "catastrophic_failure_summary.csv": catastrophic_summary,
        "receiver_difficulty_diagnostics.csv": difficulty,
        "receiver_difficulty_correlations.csv": correlations,
        "calibration_quality_summary.csv": calibration,
        "frozen_probability_calibration_receiver_seed.csv": frozen_calibration,
        "compute_fairness_summary.csv": compute,
    }
    for name, frame in outputs.items():
        frame.to_csv(analysis / name, index=False, lineterminator="\n")

    macro = primary[primary.metric == "macro_f1"].set_index("model").loc[[value for value in PRIMARY_REPORT_MODELS if value in set(primary.model)]]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(macro.index, macro["mean"], yerr=macro["std"], capsize=3, color=["#4c78a8" if value != "T3A" else "#f58518" for value in macro.index])
    ax.set_ylim(0, 1); ax.set_ylabel("Receiver-level macro-F1"); ax.set_title("WiSig receiver adaptation benchmark (mean ± receiver SD)"); ax.tick_params(axis="x", rotation=35); ax.grid(axis="y", alpha=.25)
    _write_figure(fig, figures, "receiver_adaptation_macro_f1")

    delta = difficulty.sort_values("P0"); labels = delta.receiver_id.astype(str)
    fig, ax = plt.subplots(figsize=(12, 5)); colors = np.where(delta.t3a_minus_p0 >= 0, "#54a24b", "#e45756")
    ax.bar(labels, delta.t3a_minus_p0, color=colors); ax.axhline(0, color="black", linewidth=.8); ax.set_ylabel("T3A − P0 macro-F1"); ax.set_xlabel("Held-out receiver (ordered by P0)"); ax.tick_params(axis="x", rotation=70); ax.grid(axis="y", alpha=.25)
    _write_figure(fig, figures, "t3a_minus_p0_by_receiver")

    fig, ax = plt.subplots(figsize=(8, 5))
    for method, part in budget_summary.groupby("method"):
        ax.plot(part.support_budget, part.macro_f1_mean, marker="o", label=method)
    ax.set_ylim(0, 1); ax.set_xlabel("Unlabeled receiver support packets"); ax.set_ylabel("Receiver-level macro-F1"); ax.set_title("Prespecified support-budget curves"); ax.legend(); ax.grid(alpha=.25)
    _write_figure(fig, figures, "support_budget_curves")

    selected = hardware[hardware.model.isin(["P0", "T3A", "P2", "SUP_FT_128"])]
    pivot = selected.pivot(index="hardware_family", columns="model", values="macro_f1_mean")
    fig, ax = plt.subplots(figsize=(9, 5)); pivot.plot(kind="bar", ax=ax)
    ax.set_ylim(0, 1); ax.set_ylabel("Receiver-level macro-F1"); ax.set_title("Descriptive hardware-family results"); ax.tick_params(axis="x", rotation=0); ax.grid(axis="y", alpha=.25)
    _write_figure(fig, figures, "hardware_family_results")

    cost = compute[compute.model.isin(["P0", "P2", "T3A", "RX_NORM", "SUP_FT_128"])].copy()
    fig, ax = plt.subplots(figsize=(8, 5)); ax.bar(cost.model, cost.wall_seconds_mean, color="#72b7b2")
    ax.set_yscale("log"); ax.set_ylabel("Mean recorded wall seconds (log scale)"); ax.set_title("Compute cost (training or adaptation record, method-dependent)"); ax.tick_params(axis="x", rotation=30); ax.grid(axis="y", alpha=.25)
    _write_figure(fig, figures, "compute_cost")

    result: dict[str, object] = {"validation": validation, "outputs": sorted(outputs), "figures": 5}
    (analysis / "report_validation.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if args.finalize_manifest:
        manifest_path = analysis / "analysis_manifest.json"
        if manifest_path.exists():
            raise FileExistsError("final analysis manifest already exists")
        manifest_path.write_text(json.dumps(analysis_manifest(analysis), sort_keys=True, indent=2) + "\n", encoding="utf-8")
        result["analysis_manifest_file_sha256"] = __import__("hashlib").sha256(manifest_path.read_bytes()).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-root", required=True)
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--frozen-run-root", required=True)
    parser.add_argument("--frozen-analysis-root", required=True)
    parser.add_argument("--finalize-manifest", action="store_true")
    print(json.dumps(render(parser.parse_args()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
