"""One-time unblinding, receiver-level summaries, and support-composition audits."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig.metrics import classification_metrics
from openew.paper3.wisig.metrics import per_group_macro_f1

from .blinding import create_unblinding_manifest, read_blind_predictions
from .hashing import canonical_json_bytes, sha256_file
from .runner import remap_bundle_to_split_targets
from .statistics import clustered_bootstrap, descriptive_summary, holm_adjust, receiver_bootstrap, receiver_sign_flip
from .suite import PRIMARY_MODELS
from .support import freeze_support_query


PRIMARY_RUN_COUNT = 32 * len(PRIMARY_MODELS) * 5
PRIMARY_COMPARISONS = {
    "P2_MINUS_P0": ("P2", "P0"),
    "P2_MINUS_P0_WIDE": ("P2", "P0_WIDE"),
    "P2_MINUS_P2_SHUFFLED": ("P2", "P2_SHUFFLED"),
    "P2_MINUS_T3A": ("P2", "T3A"),
}
DESCRIPTIVE_COMPARISONS = {
    **PRIMARY_COMPARISONS,
    "P1_MINUS_P0": ("P1", "P0"),
    "P2_MINUS_P1": ("P2", "P1"),
    "P2_MINUS_P2_NULL": ("P2", "P2_NULL"),
    "P2_MINUS_P2_MISMATCHED_RX": ("P2", "P2_MISMATCHED_RX"),
    "P2_MINUS_RX_NORM": ("P2", "RX_NORM"),
    "RX_NORM_MINUS_SOURCE_NORM": ("RX_NORM", "SOURCE_NORM"),
}


def collect_primary_records(run_root: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted((Path(run_root) / "runs").glob("receiver_loso_*/run.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        config = record.get("config", {})
        if config.get("support_budget") == 128 and config.get("context_k") == 32 and config.get("context_retention") == 1.0 and config.get("data_variant") == "raw":
            record["record_path"] = str(path)
            records.append(record)
    return records


def verify_primary_completion(records: list[dict[str, Any]]) -> None:
    if len(records) != PRIMARY_RUN_COUNT:
        raise RuntimeError(f"expected {PRIMARY_RUN_COUNT} primary records, found {len(records)}")
    failures = [record["run_id"] for record in records if record.get("status") != "COMPLETE"]
    if failures:
        raise RuntimeError(f"primary records not complete: {failures[:5]}")
    if any(record.get("held_out_metrics") is not None for record in records):
        raise RuntimeError("target metrics were exposed before unblinding")
    if any(record.get("target_labels_loaded_for_metrics") is not False for record in records):
        raise RuntimeError("a primary run did not preserve the target-blinding contract")


def validate_record_blind_archive(record: dict[str, Any], split_root: str | Path) -> dict[str, Any]:
    """Validate a target archive against frozen query IDs without reading labels."""

    split_root = Path(split_root)
    protocol = str(record["protocol_id"])
    summary = json.loads((split_root / protocol / "split_summary.json").read_text(encoding="utf-8"))
    manifest = pd.read_csv(split_root / protocol / "split_manifest.csv", dtype={"sample_id": "string", "split": "string"}, keep_default_na=False)
    test_ids = manifest.loc[manifest["split"] == "test", "sample_id"].astype(str).to_numpy()
    receiver = str(summary["assignment_metadata"]["test_receiver"])
    positions = np.arange(len(test_ids), dtype=np.int64)
    frozen = freeze_support_query(
        positions,
        test_ids,
        np.asarray([receiver] * len(test_ids)),
        receiver_id=receiver,
        support_budget=int(record["config"]["support_budget"]),
        seed=int(record["config"]["seed"]),
    )
    expected_ids = {str(test_ids[index]) for index in frozen.query_indices}
    prediction_path = Path(record["record_path"]).parent / "predictions_blind.npz"
    expected_classes = int(summary["eligible_transmitter_count"])
    validate_blind_archive_expected(record, prediction_path, expected_ids, expected_classes)
    return {
        "run_id": record["run_id"],
        "query_count": len(expected_ids),
        "class_count": expected_classes,
        "support_query_disjoint": True,
        "labels_read": False,
    }


def validate_blind_archive_expected(
    record: dict[str, Any],
    prediction_path: str | Path,
    expected_ids: set[str],
    expected_classes: int,
) -> dict[str, np.ndarray]:
    """Fail closed on the hash, IDs, dimensions, and simplex of a blind archive."""

    prediction_path = Path(prediction_path)
    if sha256_file(prediction_path) != record["target_prediction_sha256"]:
        raise RuntimeError(f"prediction hash mismatch in {record['run_id']}")
    prediction = read_blind_predictions(prediction_path)
    actual_ids = prediction["sample_ids"].astype(str)
    if len(actual_ids) != len(set(actual_ids)) or set(actual_ids) != expected_ids:
        raise RuntimeError(f"blind query IDs do not match frozen support/query split in {record['run_id']}")
    probabilities = prediction["probabilities"]
    if probabilities.shape != (len(expected_ids), expected_classes):
        raise RuntimeError(f"blind prediction shape mismatch in {record['run_id']}")
    if (probabilities < -1e-7).any() or not np.allclose(probabilities.sum(axis=1), 1.0, rtol=1e-5, atol=1e-6):
        raise RuntimeError(f"invalid probability simplex in {record['run_id']}")
    return prediction


def validate_target_receiver_diagnostic(record: dict[str, Any], split_root: str | Path) -> dict[str, Any]:
    """Normalize and validate non-label target inference diagnostics."""

    split_root = Path(split_root)
    summary = json.loads((split_root / str(record["protocol_id"]) / "split_summary.json").read_text(encoding="utf-8"))
    receiver = str(summary["assignment_metadata"]["test_receiver"])
    diagnostics = record.get("target_receiver_diagnostics")
    if not isinstance(diagnostics, dict) or len(diagnostics) != 1 or receiver not in diagnostics:
        raise RuntimeError(f"missing unique target-receiver diagnostics in {record['run_id']}")
    detail = diagnostics[receiver]
    common = ("support_count", "query_count", "requested_budget", "full_budget_met", "support_query_overlap", "support_fraction")
    missing = [field for field in common if field not in detail]
    if missing:
        raise RuntimeError(f"missing target receiver diagnostics in {record['run_id']}: {missing}")
    if int(detail["support_query_overlap"]) != 0:
        raise RuntimeError(f"support/query overlap in {record['run_id']}")
    if int(detail["query_count"]) != int(record["target_prediction_count"]):
        raise RuntimeError(f"diagnostic/prediction query count mismatch in {record['run_id']}")
    optional = ("context_retention", "context_k", "isolated_query_count", "attention_entropy_mean", "effective_peer_count_mean", "inference_seconds", "samples_per_second")
    row = {
        "protocol_id": str(record["protocol_id"]),
        "receiver_id": receiver,
        "hardware_family": str(summary["assignment_metadata"]["test_receiver_hardware"]),
        "seed": int(record["config"]["seed"]),
        "model": str(record["model_stage"]),
        **{field: detail[field] for field in common},
        **{field: detail.get(field) for field in optional},
    }
    if row["model"] == "P2":
        required_p2 = ("context_k", "isolated_query_count", "attention_entropy_mean", "effective_peer_count_mean", "inference_seconds", "samples_per_second")
        values = [row[field] for field in required_p2]
        if any(value is None for value in values) or not np.isfinite(np.asarray(values, dtype=float)).all():
            raise RuntimeError(f"P2 context diagnostics are incomplete in {record['run_id']}")
        if int(row["support_count"]) != 128 or int(row["context_k"]) != 32 or int(row["isolated_query_count"]) != 0:
            raise RuntimeError(f"P2 context diagnostics violate the frozen primary contract in {record['run_id']}")
    return row


def expected_role_query_ids(
    bundle: ManyRxBundle,
    role_indices: np.ndarray,
    *,
    support_budget: int,
    seed: int,
) -> set[str]:
    """Reconstruct deterministic disjoint queries for every receiver in a role."""

    expected: set[str] = set()
    for receiver in sorted(set(bundle.receiver_ids[role_indices].astype(str))):
        receiver_indices = role_indices[bundle.receiver_ids[role_indices].astype(str) == receiver]
        frozen = freeze_support_query(
            receiver_indices,
            bundle.sample_ids,
            bundle.receiver_ids,
            receiver_id=receiver,
            support_budget=support_budget,
            seed=seed,
        )
        expected.update(str(bundle.sample_ids[index]) for index in frozen.query_indices)
    return expected


def source_only_selections(records: list[dict[str, Any]], destination: str | Path) -> dict[str, Any]:
    receiver_means: list[float] = []
    for record in records:
        per_receiver = record.get("source_validation_metrics", {}).get("per_receiver_macro_f1")
        if not isinstance(per_receiver, dict) or not per_receiver:
            raise RuntimeError(f"missing source-validation receiver metrics in {record.get('run_id', '<unknown>')}")
        values = np.asarray(list(per_receiver.values()), dtype=float)
        if not np.isfinite(values).all():
            raise RuntimeError(f"non-finite source-validation receiver metric in {record.get('run_id', '<unknown>')}")
        receiver_means.append(float(values.mean()))
    frame = pd.DataFrame(
        {
            "model": [record["model_stage"] for record in records],
            "source_validation_receiver_macro_f1": receiver_means,
        }
    )
    candidates = {
        "same_information_tta": ["T3A"],
        "source_dg": ["DG_CORAL", "DG_GROUPDRO", "DG_DANN"],
    }
    payload: dict[str, Any] = {"selection_uses_target_metrics": False, "groups": {}}
    for group, models in candidates.items():
        scores = frame[frame["model"].isin(models)].groupby("model")["source_validation_receiver_macro_f1"].mean().to_dict()
        winner = max(sorted(scores), key=lambda model: scores[model])
        payload["groups"][group] = {
            "candidates": models,
            "selection_metric": "equal-weight mean of per-receiver source-validation macro-F1",
            "source_validation_receiver_means": scores,
            "selected": winner,
        }
    destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(canonical_json_bytes(payload))
    return payload


def _run_receiver(record: dict[str, Any], split_root: Path) -> str:
    summary = json.loads((split_root / record["protocol_id"] / "split_summary.json").read_text(encoding="utf-8"))
    return str(summary["assignment_metadata"]["test_receiver"])


def unblind_primary(
    converted_root: str | Path,
    split_root: str | Path,
    run_root: str | Path,
    analysis_root: str | Path,
    preregistration_path: str | Path,
) -> dict[str, Any]:
    run_root, split_root, analysis_root = Path(run_root), Path(split_root), Path(analysis_root)
    records = collect_primary_records(run_root)
    verify_primary_completion(records)
    preflight = [validate_record_blind_archive(record, split_root) for record in records]
    (analysis_root / "blind_archive_preflight.json").parent.mkdir(parents=True, exist_ok=True)
    (analysis_root / "blind_archive_preflight.json").write_bytes(canonical_json_bytes({"status": "PASS", "record_count": len(preflight), "labels_read": False, "records": preflight}))
    selection = source_only_selections(records, analysis_root / "source_validation_method_selection.json")
    plan_path = run_root / "frozen_run_plan.json"
    hashes = {record["run_id"]: str(record["target_prediction_sha256"]) for record in records}
    create_unblinding_manifest(
        analysis_root / "unblinding_manifest.json",
        preregistration_sha=sha256_file(preregistration_path),
        plan_sha=sha256_file(plan_path),
        prediction_hashes=hashes,
        completed_primary_runs=len(records),
        expected_primary_runs=PRIMARY_RUN_COUNT,
    )
    original_bundle = ManyRxBundle.load(converted_root)
    rows: list[dict[str, Any]] = []
    context_rows: list[dict[str, Any]] = []
    for record in records:
        protocol = record["protocol_id"]
        bundle = remap_bundle_to_split_targets(original_bundle, split_root / protocol / "split_summary.json")
        prediction_path = Path(record["record_path"]).parent / "predictions_blind.npz"
        if sha256_file(prediction_path) != record["target_prediction_sha256"]:
            raise RuntimeError(f"prediction hash mismatch in {record['run_id']}")
        prediction = read_blind_predictions(prediction_path)
        sample_ids = prediction["sample_ids"].astype(str)
        indices = np.asarray([bundle.sample_index[value] for value in sample_ids], dtype=np.int64)
        labels = bundle.labels[indices]
        if (labels < 0).any():
            raise RuntimeError("blind predictions include an ineligible target")
        metrics = classification_metrics(labels, prediction["probabilities"])
        receiver = _run_receiver(record, split_root)
        source_receiver_values = np.asarray(list(record["source_validation_metrics"]["per_receiver_macro_f1"].values()), dtype=float)
        if not len(source_receiver_values) or not np.isfinite(source_receiver_values).all():
            raise RuntimeError(f"invalid source-validation receiver diagnostics in {record['run_id']}")
        row = {
            "protocol_id": protocol,
            "receiver_id": receiver,
            "hardware_family": json.loads((split_root / protocol / "split_summary.json").read_text(encoding="utf-8"))["assignment_metadata"]["test_receiver_hardware"],
            "seed": int(record["config"]["seed"]),
            "model": record["model_stage"],
            "query_count": len(indices),
            **metrics,
            "source_validation_macro_f1": float(record["source_validation_metrics"]["macro_f1"]),
            "source_validation_equal_receiver_macro_f1": float(source_receiver_values.mean()),
            "parameter_count": int(record["parameter_count"]),
            "wall_seconds": float(record["wall_seconds"]),
            "peak_gpu_memory_bytes": int(record["peak_gpu_memory_bytes"]),
            "prediction_sha256": record["target_prediction_sha256"],
        }
        rows.append(row)
        context_rows.append(validate_target_receiver_diagnostic(record, split_root))
    per_run = pd.DataFrame(rows).sort_values(["protocol_id", "seed", "model"])
    per_run.to_csv(analysis_root / "primary_receiver_seed_results.csv", index=False, lineterminator="\n")
    context_frame = pd.DataFrame(context_rows).sort_values(["protocol_id", "seed", "model"])
    if len(context_frame) != PRIMARY_RUN_COUNT or context_frame.duplicated(["receiver_id", "model", "seed"]).any():
        raise RuntimeError("context diagnostics do not match the primary receiver/model/seed grain")
    context_frame.to_csv(analysis_root / "context_receiver_seed_diagnostics.csv", index=False, lineterminator="\n")
    source_validation = per_run[["protocol_id", "receiver_id", "hardware_family", "seed", "model", "source_validation_macro_f1", "source_validation_equal_receiver_macro_f1"]].copy()
    source_validation.to_csv(analysis_root / "source_validation_receiver_seed_results.csv", index=False, lineterminator="\n")
    source_receiver_means = source_validation.groupby(["model", "receiver_id"], as_index=False)["source_validation_equal_receiver_macro_f1"].mean()
    pd.DataFrame(
        [
            {"model": model, "metric": "equal-weight source-validation receiver macro-F1", **descriptive_summary(group["source_validation_equal_receiver_macro_f1"])}
            for model, group in source_receiver_means.groupby("model", sort=True)
        ]
    ).to_csv(analysis_root / "source_validation_receiver_summary.csv", index=False, lineterminator="\n")

    receiver_means = per_run.groupby(["model", "receiver_id", "hardware_family"], as_index=False).agg(
        macro_f1=("macro_f1", "mean"),
        accuracy=("accuracy", "mean"),
        balanced_accuracy=("balanced_accuracy", "mean"),
        ece=("ece", "mean"),
        source_validation_macro_f1=("source_validation_macro_f1", "mean"),
        source_validation_equal_receiver_macro_f1=("source_validation_equal_receiver_macro_f1", "mean"),
        seed_count=("seed", "nunique"),
    )
    if len(receiver_means) != 32 * len(PRIMARY_MODELS) or not (receiver_means["seed_count"] == 5).all():
        raise RuntimeError("receiver-level aggregation did not retain all five seeds per receiver/model")
    receiver_means.to_csv(analysis_root / "primary_receiver_averaged_results.csv", index=False, lineterminator="\n")

    summaries: list[dict[str, Any]] = []
    for model, group in receiver_means.groupby("model", sort=True):
        row: dict[str, Any] = {"model": model}
        for metric in ("macro_f1", "accuracy", "balanced_accuracy", "ece"):
            row.update({f"{metric}_{key}": value for key, value in descriptive_summary(group[metric]).items()})
        summaries.append(row)
    summary_frame = pd.DataFrame(summaries).sort_values("model")
    summary_frame.to_csv(analysis_root / "primary_receiver_level_summary.csv", index=False, lineterminator="\n")
    per_run.groupby(["model", "seed"], as_index=False).agg(
        receiver_macro_f1=("macro_f1", "mean"),
        receiver_accuracy=("accuracy", "mean"),
        receiver_balanced_accuracy=("balanced_accuracy", "mean"),
        receiver_ece=("ece", "mean"),
    ).to_csv(analysis_root / "seed_variability_summary.csv", index=False, lineterminator="\n")

    paired_rows: list[dict[str, Any]] = []
    receiver_differences: dict[str, dict[str, float]] = {}
    for name, (left, right) in DESCRIPTIVE_COMPARISONS.items():
        left_rows = per_run[per_run["model"] == left].set_index(["protocol_id", "receiver_id", "seed"])
        right_rows = per_run[per_run["model"] == right].set_index(["protocol_id", "receiver_id", "seed"])
        joined = left_rows[["macro_f1"]].join(right_rows[["macro_f1"]], lsuffix="_left", rsuffix="_right", how="inner")
        if len(joined) != 32 * 5:
            raise RuntimeError(f"paired comparison {name} has {len(joined)} rather than 160 rows")
        joined["difference"] = joined["macro_f1_left"] - joined["macro_f1_right"]
        for index, row in joined.reset_index().iterrows():
            paired_rows.append({"comparison": name, "protocol_id": row["protocol_id"], "receiver_id": row["receiver_id"], "seed": int(row["seed"]), "difference": float(row["difference"])})
        receiver_differences[name] = {str(receiver): float(value) for receiver, value in joined["difference"].groupby("receiver_id").mean().items()}
    best_source_dg = str(selection["groups"]["source_dg"]["selected"])
    left_rows = per_run[per_run["model"] == "P2"].set_index(["protocol_id", "receiver_id", "seed"])
    right_rows = per_run[per_run["model"] == best_source_dg].set_index(["protocol_id", "receiver_id", "seed"])
    joined = left_rows[["macro_f1"]].join(right_rows[["macro_f1"]], lsuffix="_left", rsuffix="_right", how="inner")
    if len(joined) != 32 * 5:
        raise RuntimeError("P2 versus source-selected DG baseline is not fully paired")
    joined["difference"] = joined["macro_f1_left"] - joined["macro_f1_right"]
    for _, row in joined.reset_index().iterrows():
        paired_rows.append({"comparison": "P2_MINUS_BEST_SOURCE_DG", "right_model": best_source_dg, "protocol_id": row["protocol_id"], "receiver_id": row["receiver_id"], "seed": int(row["seed"]), "difference": float(row["difference"])})
    receiver_differences["P2_MINUS_BEST_SOURCE_DG"] = {str(receiver): float(value) for receiver, value in joined["difference"].groupby("receiver_id").mean().items()}
    paired = pd.DataFrame(paired_rows)
    paired.to_csv(analysis_root / "paired_receiver_seed_differences.csv", index=False, lineterminator="\n")

    inference: dict[str, Any] = {"primary_unit": "receiver", "seed_aggregation": "mean within receiver before inference", "comparisons": {}}
    raw_p: dict[str, float] = {}
    for name in PRIMARY_COMPARISONS:
        values = list(receiver_differences[name].values())
        bootstrap = receiver_bootstrap(values)
        permutation = receiver_sign_flip(values)
        raw_p[name] = float(permutation["p_value"])
        inference["comparisons"][name] = {"bootstrap": bootstrap, "sign_flip": permutation, "receiver_differences": receiver_differences[name]}
    adjusted = holm_adjust(raw_p)
    for name, value in adjusted.items():
        inference["comparisons"][name]["holm_adjusted_p_value"] = value
    hardware_by_receiver = receiver_means[receiver_means["model"] == "P2"][["receiver_id", "hardware_family"]].set_index("receiver_id")["hardware_family"].to_dict()
    inference["hardware_family_sensitivity"] = {}
    for name, differences in receiver_differences.items():
        grouped: dict[str, list[float]] = {}
        for receiver, value in differences.items():
            grouped.setdefault(str(hardware_by_receiver[receiver]), []).append(value)
        inference["hardware_family_sensitivity"][name] = clustered_bootstrap(grouped)
    (analysis_root / "receiver_level_inference.json").write_bytes(canonical_json_bytes(inference))
    receiver_paired = paired.groupby(["comparison", "receiver_id"], as_index=False)["difference"].mean()
    receiver_paired.to_csv(analysis_root / "paired_receiver_averaged_differences.csv", index=False, lineterminator="\n")
    pd.DataFrame([
        {"comparison": name, **descriptive_summary(group["difference"])}
        for name, group in receiver_paired.groupby("comparison", sort=True)
    ]).to_csv(analysis_root / "paired_difference_summary.csv", index=False, lineterminator="\n")

    composition = support_composition_audit(original_bundle, split_root, records, per_run)
    composition.to_csv(analysis_root / "support_composition_audit.csv", index=False, lineterminator="\n")
    return {
        "status": "COMPLETE",
        "primary_runs": len(per_run),
        "models": sorted(per_run["model"].unique()),
        "strongest_same_information_tta": selection["groups"]["same_information_tta"]["selected"],
        "strongest_source_dg": selection["groups"]["source_dg"]["selected"],
        "outputs": sorted(str(path) for path in analysis_root.iterdir()),
    }


def support_composition_audit(
    original_bundle: ManyRxBundle,
    split_root: Path,
    records: Iterable[dict[str, Any]],
    per_run: pd.DataFrame,
) -> pd.DataFrame:
    p2_deltas = per_run[per_run["model"].isin(["P0", "P2"])].pivot_table(index=["protocol_id", "receiver_id", "seed"], columns="model", values="macro_f1").reset_index()
    p2_deltas["p2_minus_p0"] = p2_deltas["P2"] - p2_deltas["P0"]
    unique = {(record["protocol_id"], int(record["config"]["seed"])) for record in records}
    rows: list[dict[str, Any]] = []
    for protocol, seed in sorted(unique):
        bundle = remap_bundle_to_split_targets(original_bundle, split_root / protocol / "split_summary.json")
        test = bundle.split_indices(split_root / protocol / "split_manifest.csv")["test"]
        receiver = str(bundle.receiver_ids[test[0]])
        split = freeze_support_query(test, bundle.sample_ids, bundle.receiver_ids, receiver_id=receiver, support_budget=128, seed=seed)
        support_labels = bundle.labels[np.asarray(split.support_indices, dtype=np.int64)]
        counts = np.bincount(support_labels, minlength=len(bundle.transmitter_ids)); nonzero = counts[counts > 0]
        probabilities = nonzero / nonzero.sum()
        entropy = -float(np.sum(probabilities * np.log(probabilities)))
        query_labels = bundle.labels[np.asarray(split.query_indices, dtype=np.int64)]
        delta = p2_deltas[(p2_deltas["protocol_id"] == protocol) & (p2_deltas["seed"] == seed)]["p2_minus_p0"].iloc[0]
        rows.append(
            {
                "protocol_id": protocol,
                "receiver_id": receiver,
                "seed": seed,
                "support_count": len(support_labels),
                "distinct_transmitters": len(nonzero),
                "class_entropy_nats": entropy,
                "effective_class_count": float(np.exp(entropy)),
                "largest_class_fraction": float(probabilities.max()),
                "smallest_present_class_fraction": float(probabilities.min()),
                "query_same_class_present_fraction": float(np.mean(np.isin(query_labels, np.flatnonzero(counts)))),
                "p2_minus_p0_macro_f1": float(delta),
                "labels_used_for_audit_only": True,
            }
        )
    return pd.DataFrame(rows).sort_values(["protocol_id", "seed"])


def unblind_day_secondary(
    converted_root: str | Path,
    split_root: str | Path,
    run_root: str | Path,
    analysis_root: str | Path,
) -> dict[str, Any]:
    """Evaluate the preregistered coarse-day secondary suite only after primary unblinding."""

    split_root, run_root, analysis_root = Path(split_root), Path(run_root), Path(analysis_root)
    if not (analysis_root / "unblinding_manifest.json").exists():
        raise RuntimeError("day secondary metrics are forbidden before primary unblinding")
    day_manifest_path = analysis_root / "day_secondary_unblinding_manifest.json"
    if day_manifest_path.exists():
        raise FileExistsError("day secondary already unblinded")
    records: list[dict[str, Any]] = []
    for path in sorted((run_root / "runs").glob("day_lodo_*/run.json")):
        record = json.loads(path.read_text(encoding="utf-8")); record["record_path"] = str(path)
        config = record.get("config", {})
        if config.get("support_budget") == 128 and config.get("context_k") == 32 and config.get("data_variant") == "raw":
            records.append(record)
    expected = 4 * len(PRIMARY_MODELS) * 5
    if len(records) != expected or any(record.get("status") != "COMPLETE" for record in records):
        raise RuntimeError(f"day secondary requires {expected} complete records, found {len(records)}")
    if any(record.get("held_out_metrics") is not None or record.get("target_labels_loaded_for_metrics") is not False for record in records):
        raise RuntimeError("day secondary violated target blinding")
    original = ManyRxBundle.load(converted_root); rows: list[dict[str, Any]] = []
    prediction_hashes: dict[str, str] = {}
    for record in records:
        protocol = record["protocol_id"]
        bundle = remap_bundle_to_split_targets(original, split_root / protocol / "split_summary.json")
        path = Path(record["record_path"]).parent / "predictions_blind.npz"
        prediction_hashes[record["run_id"]] = record["target_prediction_sha256"]
        test_indices = bundle.split_indices(split_root / protocol / "split_manifest.csv")["test"]
        expected_ids = expected_role_query_ids(
            bundle,
            test_indices,
            support_budget=int(record["config"]["support_budget"]),
            seed=int(record["config"]["seed"]),
        )
        prediction = validate_blind_archive_expected(record, path, expected_ids, len(bundle.transmitter_ids))
        sample_ids = prediction["sample_ids"].astype(str)
        indices = np.asarray([bundle.sample_index[value] for value in sample_ids], dtype=np.int64)
        metrics = classification_metrics(bundle.labels[indices], prediction["probabilities"])
        per_receiver = per_group_macro_f1(bundle.labels[indices], prediction["probabilities"], bundle.receiver_ids[indices])
        rows.append({"protocol_id": protocol, "test_day": json.loads((split_root / protocol / "split_summary.json").read_text(encoding="utf-8"))["assignment_metadata"]["test_day"], "seed": int(record["config"]["seed"]), "model": record["model_stage"], "query_count": len(indices), **metrics, "equal_weight_receiver_macro_f1": float(np.mean(list(per_receiver.values()))), "per_receiver_macro_f1_json": json.dumps(per_receiver, sort_keys=True)})
    frame = pd.DataFrame(rows).sort_values(["protocol_id", "seed", "model"])
    frame.to_csv(analysis_root / "day_receiver_seed_results.csv", index=False, lineterminator="\n")
    manifest = {"status": "UNBLINDED_AFTER_PRIMARY", "record_count": len(frame), "prediction_manifest_sha256": __import__("hashlib").sha256(canonical_json_bytes(dict(sorted(prediction_hashes.items())))).hexdigest()}
    day_manifest_path.write_bytes(canonical_json_bytes(manifest))
    return manifest


def unblind_equalized_diagnostic(
    converted_root: str | Path,
    split_root: str | Path,
    run_root: str | Path,
    analysis_root: str | Path,
    primary_analysis_root: str | Path,
) -> dict[str, Any]:
    """Unblind the separately preregistered one-seed equalized diagnostic."""

    split_root, run_root, analysis_root = Path(split_root), Path(run_root), Path(analysis_root)
    if not (Path(primary_analysis_root) / "unblinding_manifest.json").exists():
        raise RuntimeError("equalized diagnostic cannot be unblinded before raw primary completion")
    manifest_path = analysis_root / "equalized_unblinding_manifest.json"
    if manifest_path.exists():
        raise FileExistsError("equalized diagnostic already unblinded")
    records: list[dict[str, Any]] = []
    for path in sorted((run_root / "runs").glob("receiver_loso_*/run.json")):
        record = json.loads(path.read_text(encoding="utf-8")); record["record_path"] = str(path)
        if record.get("config", {}).get("data_variant") == "official_equalized":
            records.append(record)
    expected = 32 * 3
    if len(records) != expected or any(record.get("status") != "COMPLETE" for record in records):
        raise RuntimeError(f"equalized diagnostic requires {expected} complete records, found {len(records)}")
    if any(record.get("held_out_metrics") is not None or record.get("target_labels_loaded_for_metrics") is not False for record in records):
        raise RuntimeError("equalized diagnostic violated target blinding")
    preflight = [validate_record_blind_archive(record, split_root) for record in records]
    original = ManyRxBundle.load(converted_root); rows: list[dict[str, Any]] = []; hashes: dict[str, str] = {}
    for record in records:
        protocol = record["protocol_id"]
        bundle = remap_bundle_to_split_targets(original, split_root / protocol / "split_summary.json")
        prediction = read_blind_predictions(Path(record["record_path"]).parent / "predictions_blind.npz")
        sample_ids = prediction["sample_ids"].astype(str)
        indices = np.asarray([bundle.sample_index[value] for value in sample_ids], dtype=np.int64)
        summary = json.loads((split_root / protocol / "split_summary.json").read_text(encoding="utf-8"))
        rows.append(
            {
                "protocol_id": protocol,
                "receiver_id": str(summary["assignment_metadata"]["test_receiver"]),
                "hardware_family": str(summary["assignment_metadata"]["test_receiver_hardware"]),
                "seed": int(record["config"]["seed"]),
                "model": record["model_stage"],
                "query_count": len(indices),
                **classification_metrics(bundle.labels[indices], prediction["probabilities"]),
            }
        )
        hashes[record["run_id"]] = str(record["target_prediction_sha256"])
    frame = pd.DataFrame(rows).sort_values(["protocol_id", "model"])
    analysis_root.mkdir(parents=True, exist_ok=True)
    frame.to_csv(analysis_root / "equalized_receiver_results.csv", index=False, lineterminator="\n")
    summaries = []
    for model, group in frame.groupby("model", sort=True):
        summaries.append({"model": model, **{f"macro_f1_{key}": value for key, value in descriptive_summary(group["macro_f1"]).items()}})
    pd.DataFrame(summaries).to_csv(analysis_root / "equalized_receiver_summary.csv", index=False, lineterminator="\n")
    pivot = frame.pivot(index="receiver_id", columns="model", values="macro_f1")
    deltas = pivot.assign(
        P2_MINUS_P0=pivot["P2"] - pivot["P0"],
        P2_MINUS_P2_SHUFFLED=pivot["P2"] - pivot["P2_SHUFFLED"],
    )[["P2_MINUS_P0", "P2_MINUS_P2_SHUFFLED"]].reset_index()
    deltas.to_csv(analysis_root / "equalized_receiver_differences.csv", index=False, lineterminator="\n")
    manifest = {
        "status": "UNBLINDED_AFTER_RAW_PRIMARY",
        "record_count": len(frame),
        "receiver_count": int(frame["receiver_id"].nunique()),
        "seed_count": int(frame["seed"].nunique()),
        "blind_preflight_passed": len(preflight) == expected,
        "prediction_manifest_sha256": __import__("hashlib").sha256(canonical_json_bytes(dict(sorted(hashes.items())))).hexdigest(),
        "diagnostic_only": True,
    }
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    return manifest


def unblind_grouped_secondary(
    converted_root: str | Path,
    split_root: str | Path,
    run_root: str | Path,
    analysis_root: str | Path,
    primary_analysis_root: str | Path,
) -> dict[str, Any]:
    """Evaluate fixed repeated grouped-receiver predictions after primary unblinding."""

    split_root, run_root, analysis_root = Path(split_root), Path(run_root), Path(analysis_root)
    if not (Path(primary_analysis_root) / "unblinding_manifest.json").exists():
        raise RuntimeError("grouped secondary cannot be unblinded before raw LOSO primary")
    manifest_path = analysis_root / "grouped_secondary_unblinding_manifest.json"
    if manifest_path.exists():
        raise FileExistsError("grouped receiver secondary already unblinded")
    record_paths = sorted((run_root / "runs").glob("grouped_receiver_*/run.json"))
    records = []
    for path in record_paths:
        record = json.loads(path.read_text(encoding="utf-8")); record["record_path"] = str(path); records.append(record)
    expected = 12 * 3 * 5
    if len(records) != expected or any(record.get("status") != "COMPLETE" for record in records):
        raise RuntimeError(f"grouped secondary requires {expected} complete records, found {len(records)}")
    if any(record.get("held_out_metrics") is not None or record.get("target_labels_loaded_for_metrics") is not False for record in records):
        raise RuntimeError("grouped secondary violated target blinding")
    original = ManyRxBundle.load(converted_root); rows: list[dict[str, Any]] = []; hashes: dict[str, str] = {}
    for record in records:
        protocol = record["protocol_id"]; seed = int(record["config"]["seed"])
        bundle = remap_bundle_to_split_targets(original, split_root / protocol / "split_summary.json")
        split_indices = bundle.split_indices(split_root / protocol / "split_manifest.csv")
        expected_query: set[str] = set()
        for receiver in sorted(set(bundle.receiver_ids[split_indices["test"]].astype(str))):
            indices = split_indices["test"][bundle.receiver_ids[split_indices["test"]].astype(str) == receiver]
            frozen = freeze_support_query(indices, bundle.sample_ids, bundle.receiver_ids, receiver_id=receiver, support_budget=128, seed=seed)
            expected_query.update(str(bundle.sample_ids[index]) for index in frozen.query_indices)
        prediction_path = Path(record["record_path"]).parent / "predictions_blind.npz"
        if sha256_file(prediction_path) != record["target_prediction_sha256"]:
            raise RuntimeError(f"grouped prediction hash mismatch: {record['run_id']}")
        prediction = validate_blind_archive_expected(record, prediction_path, expected_query, len(bundle.transmitter_ids))
        sample_ids = prediction["sample_ids"].astype(str)
        indices = np.asarray([bundle.sample_index[value] for value in sample_ids], dtype=np.int64)
        probabilities = prediction["probabilities"]
        summary = json.loads((split_root / protocol / "split_summary.json").read_text(encoding="utf-8"))
        for receiver in sorted(set(bundle.receiver_ids[indices].astype(str))):
            mask = bundle.receiver_ids[indices].astype(str) == receiver
            rows.append(
                {
                    "protocol_id": protocol,
                    "repeat": int(summary["assignment_metadata"]["repeat"]),
                    "fold": int(summary["assignment_metadata"]["fold"]),
                    "receiver_id": receiver,
                    "seed": seed,
                    "model": record["model_stage"],
                    "query_count": int(mask.sum()),
                    **classification_metrics(bundle.labels[indices][mask], probabilities[mask]),
                }
            )
        hashes[record["run_id"]] = str(record["target_prediction_sha256"])
    frame = pd.DataFrame(rows).sort_values(["repeat", "fold", "receiver_id", "seed", "model"])
    expected_rows = 3 * 32 * 5 * 3
    if len(frame) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} grouped receiver result rows, found {len(frame)}")
    analysis_root.mkdir(parents=True, exist_ok=True)
    frame.to_csv(analysis_root / "grouped_secondary_receiver_seed_results.csv", index=False, lineterminator="\n")
    receiver_means = frame.groupby(["receiver_id", "model"], as_index=False).agg(macro_f1=("macro_f1", "mean"), accuracy=("accuracy", "mean"), balanced_accuracy=("balanced_accuracy", "mean"), ece=("ece", "mean"))
    receiver_means.to_csv(analysis_root / "grouped_secondary_receiver_averages.csv", index=False, lineterminator="\n")
    manifest = {
        "status": "UNBLINDED_AFTER_RAW_PRIMARY",
        "record_count": len(records),
        "receiver_result_count": len(frame),
        "receiver_count": int(frame["receiver_id"].nunique()),
        "repeat_count": int(frame["repeat"].nunique()),
        "prediction_manifest_sha256": __import__("hashlib").sha256(canonical_json_bytes(dict(sorted(hashes.items())))).hexdigest(),
        "secondary_only": True,
    }
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    return manifest
