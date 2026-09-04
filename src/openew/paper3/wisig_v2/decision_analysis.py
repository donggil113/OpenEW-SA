"""Assemble the fixed GO evidence after all target results are frozen."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .decision import MechanismEvidence, evaluate_mechanism_go
from .hashing import canonical_json_bytes


def build_decision_summary(analysis_root: str | Path, integrity_path: str | Path, destination: str | Path) -> dict[str, Any]:
    root = Path(analysis_root)
    receiver_deltas = pd.read_csv(root / "paired_receiver_averaged_differences.csv")
    paired_summary = pd.read_csv(root / "paired_difference_summary.csv").set_index("comparison")
    primary = pd.read_csv(root / "primary_receiver_seed_results.csv")
    receiver_primary = pd.read_csv(root / "primary_receiver_averaged_results.csv")
    oracle = pd.read_csv(root / "composition_oracle_results.csv")
    selection = json.loads((root / "source_validation_method_selection.json").read_text(encoding="utf-8"))
    integrity = json.loads(Path(integrity_path).read_text(encoding="utf-8"))
    preflight = json.loads((root / "blind_archive_preflight.json").read_text(encoding="utf-8"))
    best_tta = str(selection["groups"]["same_information_tta"]["selected"])
    means = {str(index): float(row["mean"]) for index, row in paired_summary.iterrows()}
    tta_key = f"P2_MINUS_{best_tta}"
    if tta_key not in means:
        raise RuntimeError(f"missing paired comparison for source-selected TTA: {best_tta}")
    means["P2_MINUS_BEST_TTA"] = means[tta_key]
    p2_p0 = receiver_deltas[receiver_deltas["comparison"] == "P2_MINUS_P0"]
    positive_receivers = int((p2_p0["difference"] > 0).sum())
    hardware = receiver_primary[receiver_primary["model"].isin(["P0", "P2"])].pivot(index=["receiver_id", "hardware_family"], columns="model", values="macro_f1").reset_index()
    hardware["difference"] = hardware["P2"] - hardware["P0"]
    hardware_means = {str(key): float(value) for key, value in hardware.groupby("hardware_family")["difference"].mean().items()}
    same_excluded = oracle[oracle["condition"] == "SAME_CLASS_EXCLUDED_ORACLE"]
    coverage = bool((same_excluded["evaluable_query_count"] == same_excluded["query_count"]).all())
    oracle_receiver_mean = same_excluded.groupby("receiver_id")["macro_f1"].mean().mean()
    p0_receiver_mean = primary[primary["model"] == "P0"].groupby("receiver_id")["macro_f1"].mean().mean()
    evidence = MechanismEvidence(
        mean_deltas=means,
        positive_p2_minus_p0_receivers=positive_receivers,
        positive_hardware_families=sum(value > 0 for value in hardware_means.values()),
        same_class_excluded_minus_p0=float(oracle_receiver_mean - p0_receiver_mean),
        same_class_excluded_full_coverage=coverage,
        integrity_pass=integrity.get("status") == "PASS",
        disjoint_support_query_pass=preflight.get("status") == "PASS" and preflight.get("labels_read") is False,
    )
    decision = evaluate_mechanism_go(evidence)
    payload = {
        "status": "COMPLETE",
        "best_same_information_tta_selected_on_source_validation": best_tta,
        "mean_deltas": means,
        "positive_p2_minus_p0_receivers": positive_receivers,
        "hardware_family_mean_p2_minus_p0": hardware_means,
        "positive_hardware_families": evidence.positive_hardware_families,
        "same_class_excluded_minus_p0": evidence.same_class_excluded_minus_p0,
        "same_class_excluded_full_coverage": coverage,
        "decision": decision,
    }
    destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(canonical_json_bytes(payload))
    return payload
