"""Receiver-level addendum aggregation, figures, and immutable manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from openew.paper3.wisig.archive import sha256_file
from openew.paper3.wisig.checkpoint import atomic_json
from openew.paper3.wisig_v2.statistics import descriptive_summary, receiver_bootstrap

from .contracts import ADDENDUM_SEEDS, EXPECTED_RECEIVERS
from .inference import summarize_receiver_deltas


def collect_shuffled_training(output_root: str | Path) -> pd.DataFrame:
    paths = sorted((Path(output_root) / "shuffled_training" / "runs").glob("*/run.json"))
    if len(paths) != EXPECTED_RECEIVERS * len(ADDENDUM_SEEDS):
        raise RuntimeError(f"shuffled training requires 160 records, found {len(paths)}")
    rows: list[dict[str, Any]] = []
    for path in paths:
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("status") != "COMPLETE" or record.get("analysis_status") != "POSTHOC_MECHANISTIC":
            raise RuntimeError(f"incomplete/non-posthoc shuffled record: {path}")
        if record.get("labels_used_to_construct_training_context") is not False:
            raise RuntimeError(f"label-dependent shuffled training record: {path}")
        receiver = next(iter(record["evaluations"]["P2"]["receiver_diagnostics"]))
        for stage, detail in record["evaluations"].items():
            rows.append({
                "protocol_id": record["protocol_id"],
                "receiver_id": receiver,
                "seed": int(record["seed"]),
                "training_context": "SHUFFLED_RECEIVER",
                "evaluation_stage": stage,
                "condition": detail["condition"],
                "evidence_category": detail["evidence_category"],
                "query_count": int(detail["query_count"]),
                "best_epoch": int(record["best_epoch"]),
                "source_validation_macro_f1": float(record["best_source_validation_macro_f1"]),
                "wall_seconds": float(record["wall_seconds"]),
                **{key: float(value) for key, value in detail["metrics"].items() if key in {"macro_f1", "accuracy", "balanced_accuracy", "ece"}},
            })
    frame = pd.DataFrame(rows).sort_values(["condition", "protocol_id", "seed"])
    if len(frame) != 160 * 3 or frame.duplicated(["receiver_id", "seed", "condition"]).any():
        raise RuntimeError("shuffled-training evaluation grain is invalid")
    return frame


def _condition_summary(frame: pd.DataFrame, *, group: str) -> pd.DataFrame:
    receiver = frame.groupby([group, "receiver_id"], as_index=False)["macro_f1"].mean()
    return pd.DataFrame([
        {group: value, **descriptive_summary(part["macro_f1"].to_numpy()), "bootstrap": json.dumps(receiver_bootstrap(part["macro_f1"].to_numpy(), replicates=10_000, seed=20_260_903), sort_keys=True)}
        for value, part in receiver.groupby(group, sort=True)
    ])


def _save_figure(fig: plt.Figure, root: Path, name: str) -> None:
    figure_root = root / "figures"
    figure_root.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(figure_root / f"{name}.png", dpi=200)
    fig.savefig(figure_root / f"{name}.pdf")
    plt.close(fig)


def _bar_figure(frame: pd.DataFrame, group: str, root: Path, name: str, title: str) -> None:
    receiver = frame.groupby([group, "receiver_id"], as_index=False).macro_f1.mean()
    summary = receiver.groupby(group).macro_f1.agg(["mean", "std"]).reset_index()
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    x = np.arange(len(summary))
    ax.bar(x, summary["mean"], yerr=summary["std"], capsize=3, color="#4472C4")
    ax.set_xticks(x, summary[group], rotation=20, ha="right")
    ax.set_ylabel("Equal-weight receiver macro-F1")
    ax.set_ylim(0, 1)
    ax.set_title(title)
    ax.grid(axis="y", alpha=.25)
    _save_figure(fig, root, name)


def _budget_figure(frame: pd.DataFrame, root: Path) -> None:
    receiver = frame.groupby(["method", "support_budget", "receiver_id"], as_index=False).macro_f1.mean()
    summary = receiver.groupby(["method", "support_budget"]).macro_f1.agg(["mean", "std"]).reset_index()
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for method, part in summary.groupby("method", sort=True):
        ax.errorbar(part.support_budget, part["mean"], yerr=part["std"], marker="o", capsize=3, label=method)
    ax.set_xscale("log", base=2)
    ax.set_xticks([16,32,64,128,256], ["16","32","64","128","256"])
    ax.set_ylim(0, 1)
    ax.set_xlabel("Unlabeled receiver-support budget")
    ax.set_ylabel("Equal-weight receiver macro-F1")
    ax.set_title("Post-hoc support-budget efficiency")
    ax.legend()
    ax.grid(alpha=.25)
    _save_figure(fig, root, "support_budget_efficiency")


def _hardware_summary(primary: pd.DataFrame) -> pd.DataFrame:
    means = primary.groupby(["hardware_family", "receiver_id", "model"], as_index=False).macro_f1.mean()
    pivot = means.pivot(index=["hardware_family", "receiver_id"], columns="model", values="macro_f1")
    rows: list[dict[str, Any]] = []
    for comparison, left, right in (("P2_MINUS_P0","P2","P0"),("T3A_MINUS_P0","T3A","P0"),("P2_MINUS_T3A","P2","T3A")):
        values = (pivot[left] - pivot[right]).rename("difference").reset_index()
        for family, part in values.groupby("hardware_family", sort=True):
            rows.append({"comparison": comparison, "hardware_family": family, **descriptive_summary(part.difference.to_numpy()), "positive_receivers": int((part.difference > 0).sum())})
    return pd.DataFrame(rows)


def build_addendum_analysis(
    addendum_root: str | Path,
    frozen_analysis_root: str | Path,
) -> dict[str, Any]:
    root, frozen = Path(addendum_root), Path(frozen_analysis_root)
    query = pd.read_csv(root / "query_coupling_receiver_seed_results.csv")
    t3a_budget = pd.read_csv(root / "t3a_support_budget_receiver_seed_results.csv")
    p2_budget = pd.read_csv(frozen / "support_budget_results.csv").assign(method="P2")
    t3a_budget = t3a_budget.assign(method="T3A")
    budgets = pd.concat([p2_budget[t3a_budget.columns], t3a_budget], ignore_index=True)
    composition_tta = pd.read_csv(root / "tta_rxnorm_composition_receiver_seed_results.csv")
    p2_oracle = pd.read_csv(frozen / "composition_oracle_results.csv").assign(method="P2", evidence_category="ORACLE_DIAGNOSTIC")
    common = [value for value in composition_tta.columns if value in p2_oracle.columns]
    composition = pd.concat([composition_tta[common], p2_oracle[common]], ignore_index=True)
    primary = pd.read_csv(frozen / "primary_receiver_seed_results.csv")
    shuffled = collect_shuffled_training(root)

    query.to_csv(root / "analysis_query_coupling.csv", index=False, lineterminator="\n")
    budgets.to_csv(root / "analysis_support_budget.csv", index=False, lineterminator="\n")
    composition.to_csv(root / "analysis_composition_stress.csv", index=False, lineterminator="\n")
    shuffled.to_csv(root / "analysis_shuffled_training.csv", index=False, lineterminator="\n")
    hardware = _hardware_summary(primary)
    hardware.to_csv(root / "analysis_hardware_family.csv", index=False, lineterminator="\n")

    query_summary = _condition_summary(query, group="condition")
    budget_summary = _condition_summary(budgets.rename(columns={"support_budget":"condition"}), group="condition")
    composition_summary = composition.groupby(["method", "condition", "receiver_id"], as_index=False).macro_f1.mean().groupby(["method", "condition"]).macro_f1.agg(["count","mean","std","median","min","max"]).reset_index()
    shuffled_summary = _condition_summary(shuffled, group="condition")
    query_summary.to_csv(root / "summary_query_coupling.csv", index=False, lineterminator="\n")
    budget_summary.to_csv(root / "summary_support_budget.csv", index=False, lineterminator="\n")
    composition_summary.to_csv(root / "summary_composition_stress.csv", index=False, lineterminator="\n")
    shuffled_summary.to_csv(root / "summary_shuffled_training.csv", index=False, lineterminator="\n")

    _bar_figure(query, "condition", root, "query_coupling", "Query-coupling information-access diagnostic")
    _bar_figure(shuffled, "condition", root, "shuffled_context_training", "Shuffled-context source training")
    _bar_figure(composition.assign(method_condition=composition.method + " / " + composition.condition), "method_condition", root, "composition_stress", "Oracle composition stress (nondeployable)")
    _budget_figure(budgets, root)

    summary = {
        "status": "COMPLETE",
        "analysis_status": "POSTHOC_MECHANISTIC_ADDENDUM",
        "query_coupling": {
            "chunk_minus_disjoint": summarize_receiver_deltas(query, "QUERY_COUPLED_CHUNK", "DISJOINT_NATURAL"),
            "full_partition_minus_disjoint": summarize_receiver_deltas(query, "FULL_RECEIVER_PARTITION", "DISJOINT_NATURAL"),
        },
        "shuffled_training": {
            "natural_minus_shuffled": summarize_receiver_deltas(shuffled, "NATURAL", "SHUFFLED"),
            "natural_minus_null": summarize_receiver_deltas(shuffled, "NATURAL", "NULL"),
        },
        "equalized": json.loads((root / "equalized_intersection_audit.json").read_text(encoding="utf-8")),
        "records": {
            "query_coupling": len(query),
            "support_budget": len(budgets),
            "composition": len(composition),
            "shuffled_training": len(shuffled),
        },
    }
    atomic_json(summary, root / "addendum_summary.json")
    return summary


def hash_addendum_analysis(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    manifest_path = root / "analysis_manifest.json"
    paths = sorted(path for path in root.rglob("*") if path.is_file() and path != manifest_path and "records" not in path.parts and "shuffled_training" not in path.parts)
    files = {str(path.relative_to(root)): sha256_file(path) for path in paths}
    aggregate = hashlib.sha256()
    for name, digest in files.items():
        aggregate.update(name.encode()); aggregate.update(b"\0"); aggregate.update(digest.encode()); aggregate.update(b"\n")
    payload = {"schema_version": 1, "status": "FROZEN_POSTHOC_ANALYSIS", "file_count": len(files), "files": files, "sha256": aggregate.hexdigest()}
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing != payload:
            raise RuntimeError("analysis changed after manifest freeze")
    else:
        atomic_json(payload, manifest_path)
    return payload
