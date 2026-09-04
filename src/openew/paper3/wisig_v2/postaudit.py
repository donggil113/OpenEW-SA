"""Post-unblinding receiver/day/class-support diagnostics without redesign."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig.validation import load_converted_tables

from .analysis import collect_primary_records
from .blinding import read_blind_predictions
from .hashing import canonical_json_bytes
from .runner import remap_bundle_to_split_targets


def correlation_diagnostic(frame: pd.DataFrame, field: str, outcome: str) -> dict[str, Any]:
    """Return standards-compliant nullable correlations for post-hoc diagnostics."""

    pair = frame[[field, outcome]].dropna()
    if len(pair) < 3:
        return {"defined": False, "pearson": None, "spearman": None, "reason": "fewer_than_three_complete_rows", "row_count": len(pair)}
    if pair[field].nunique() < 2 or pair[outcome].nunique() < 2:
        return {"defined": False, "pearson": None, "spearman": None, "reason": "constant_variable", "row_count": len(pair)}
    pearson = float(pair.corr(method="pearson").iloc[0, 1])
    spearman = float(pair.corr(method="spearman").iloc[0, 1])
    if not np.isfinite(pearson) or not np.isfinite(spearman):
        return {"defined": False, "pearson": None, "spearman": None, "reason": "nonfinite_result", "row_count": len(pair)}
    return {"defined": True, "pearson": pearson, "spearman": spearman, "reason": None, "row_count": len(pair)}


def run_target_proxy_postaudit(
    converted_root: str | Path,
    split_root: str | Path,
    run_root: str | Path,
    analysis_root: str | Path,
) -> dict[str, Any]:
    split_root, run_root, analysis_root = Path(split_root), Path(run_root), Path(analysis_root)
    if not (analysis_root / "unblinding_manifest.json").exists():
        raise RuntimeError("target proxy post-audit is forbidden before the one-time unblinding")
    original = ManyRxBundle.load(converted_root)
    acquisition, _ = load_converted_tables(converted_root)
    quality_by_id = dict(zip(acquisition["sample_id"].astype(str), acquisition["data_quality_flags"].fillna("").astype(str)))
    day_rows: list[dict[str, Any]] = []
    class_rows: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []
    selected_models = {"P0", "P0_WIDE", "DG_DANN", "P1", "P2", "P2_SHUFFLED", "P2_NULL", "P2_MISMATCHED_RX", "RX_NORM", "T3A"}
    for record in collect_primary_records(run_root):
        if record["model_stage"] not in selected_models:
            continue
        protocol = record["protocol_id"]
        summary = json.loads((split_root / protocol / "split_summary.json").read_text(encoding="utf-8"))
        receiver = str(summary["assignment_metadata"]["test_receiver"])
        bundle = remap_bundle_to_split_targets(original, split_root / protocol / "split_summary.json")
        prediction = read_blind_predictions(Path(record["record_path"]).parent / "predictions_blind.npz")
        sample_ids = prediction["sample_ids"].astype(str)
        indices = np.asarray([bundle.sample_index[value] for value in sample_ids], dtype=np.int64)
        truth = bundle.labels[indices]; predicted = prediction["probabilities"].argmax(axis=1)
        for day in sorted(set(bundle.day_ids[indices].astype(str))):
            mask = bundle.day_ids[indices].astype(str) == day
            day_rows.append({"protocol_id": protocol, "receiver_id": receiver, "seed": int(record["config"]["seed"]), "model": record["model_stage"], "day_id": day, "query_count": int(mask.sum()), "macro_f1": float(f1_score(truth[mask], predicted[mask], average="macro", zero_division=0))})
        test_support = summary["per_class_support"]
        for class_index, transmitter in enumerate(bundle.transmitter_ids):
            mask = truth == class_index
            if not mask.any():
                continue
            class_rows.append({"protocol_id": protocol, "receiver_id": receiver, "seed": int(record["config"]["seed"]), "model": record["model_stage"], "transmitter_id": transmitter, "query_count": int(mask.sum()), "test_support_before_support_bank_removal": int(test_support[transmitter]["test"]), "class_f1": float(f1_score(truth, predicted, labels=[class_index], average=None, zero_division=0)[0])})
        quality = np.asarray([quality_by_id[value] or "NONE" for value in sample_ids])
        for flag in sorted(set(quality)):
            mask = quality == flag
            quality_rows.append({"protocol_id": protocol, "receiver_id": receiver, "seed": int(record["config"]["seed"]), "model": record["model_stage"], "quality_flag": flag, "query_count": int(mask.sum()), "error_rate": float(np.mean(predicted[mask] != truth[mask]))})
    outputs = {
        "per_day": pd.DataFrame(day_rows),
        "per_class": pd.DataFrame(class_rows),
        "quality": pd.DataFrame(quality_rows),
    }
    for name, frame in outputs.items():
        frame.to_csv(analysis_root / f"target_postaudit_{name}.csv", index=False, lineterminator="\n")

    composition = pd.read_csv(analysis_root / "support_composition_audit.csv")
    correlations = {"receiver_seed_rows": {}, "receiver_averaged_rows": {}}
    receiver_composition = composition.groupby("receiver_id", as_index=False).agg(
        class_entropy_nats=("class_entropy_nats", "mean"),
        distinct_transmitters=("distinct_transmitters", "mean"),
        largest_class_fraction=("largest_class_fraction", "mean"),
        query_same_class_present_fraction=("query_same_class_present_fraction", "mean"),
        p2_minus_p0_macro_f1=("p2_minus_p0_macro_f1", "mean"),
    )
    for field in ("class_entropy_nats", "distinct_transmitters", "largest_class_fraction", "query_same_class_present_fraction"):
        correlations["receiver_seed_rows"][field] = correlation_diagnostic(composition, field, "p2_minus_p0_macro_f1")
        correlations["receiver_averaged_rows"][field] = correlation_diagnostic(receiver_composition, field, "p2_minus_p0_macro_f1")
    payload = {
        "status": "DIAGNOSTIC_ONLY",
        "model_redesign_permitted": False,
        "receiver_is_primary_unit": True,
        "support_composition_correlations": correlations,
        "quality_flags": sorted(outputs["quality"]["quality_flag"].unique()),
        "row_counts": {name: len(frame) for name, frame in outputs.items()},
    }
    (analysis_root / "target_proxy_postaudit_summary.json").write_bytes(canonical_json_bytes(payload))
    return payload
