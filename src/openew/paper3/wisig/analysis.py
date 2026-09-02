"""Preregistered all-run summaries and receiver-cluster uncertainty analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .suite import deduplicate_plan, full_suite_plan
from .validation import load_converted_tables
from .archive import sha256_file
from .runner import RunConfig


PRIMARY_MODELS = ("P0", "P0_WIDE", "DG_CORAL", "DG_GROUPDRO", "P1", "P2", "P2_SHUFFLED", "P2_NULL")
PAIRS = (("P1", "P0"), ("P2", "P0"), ("P2", "P1"), ("P2", "P2_SHUFFLED"), ("P2", "P2_NULL"), ("P2", "P0_WIDE"))


def audit_run_completeness(run_root: str | Path) -> dict[str, Any]:
    """Compare persisted run records with the immutable, code-defined suite grid."""
    expected_rows = deduplicate_plan(full_suite_plan())
    expected = {config.config_hash: phases for phases, config in expected_rows}
    actual: dict[str, list[dict[str, Any]]] = {}
    malformed: list[str] = []
    missing_prediction_files: list[str] = []
    prediction_hash_mismatches: list[str] = []
    missing_checkpoint_files: list[str] = []
    configuration_hash_mismatches: list[str] = []
    run_directory_mismatches: list[str] = []
    checkpoint_inventory: list[dict[str, str]] = []
    for path in sorted(Path(run_root).glob("runs/*/run.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            actual.setdefault(str(record["config_hash"]), []).append(record)
            computed_config_hash = RunConfig(**record["config"]).validate().config_hash
            if computed_config_hash != record["config_hash"]:
                configuration_hash_mismatches.append(str(path))
            if path.parent.name != record["run_id"]:
                run_directory_mismatches.append(str(path))
            if record.get("status") == "COMPLETE":
                prediction_path = path.parent / "predictions.csv"
                checkpoint_path = path.parent / "checkpoint.pt"
                if not prediction_path.exists():
                    missing_prediction_files.append(str(prediction_path))
                elif sha256_file(prediction_path) != record.get("prediction_sha256"):
                    prediction_hash_mismatches.append(str(prediction_path))
                if not checkpoint_path.exists():
                    missing_checkpoint_files.append(str(checkpoint_path))
                else:
                    checkpoint_inventory.append(
                        {
                            "run_id": str(record["run_id"]),
                            "checkpoint_sha256": sha256_file(checkpoint_path),
                        }
                    )
        except (KeyError, json.JSONDecodeError, OSError):
            malformed.append(str(path))
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    duplicates = sorted(key for key, values in actual.items() if len(values) != 1)
    records = [value for values in actual.values() for value in values]
    incomplete = sorted(
        key
        for key, values in actual.items()
        if any(value.get("status") != "COMPLETE" for value in values)
    )
    checks = {
        "all_expected_runs_present": not missing,
        "no_unexpected_runs": not unexpected,
        "one_record_per_config_hash": not duplicates,
        "all_records_complete": not incomplete,
        "all_records_well_formed": not malformed,
        "one_training_git_sha": len({str(value.get("git_sha")) for value in records}) == 1 if records else False,
        "one_data_manifest_sha": len({str(value.get("data_manifest_sha256")) for value in records}) == 1 if records else False,
        "all_complete_predictions_hashed": all(
            value.get("status") != "COMPLETE" or bool(value.get("prediction_sha256"))
            for value in records
        ) if records else False,
        "all_prediction_files_present": not missing_prediction_files,
        "all_prediction_hashes_match": not prediction_hash_mismatches,
        "all_checkpoint_files_present": bool(records) and not missing_checkpoint_files,
        "all_configuration_hashes_recompute": not configuration_hash_mismatches,
        "all_run_directories_match_run_ids": not run_directory_mismatches,
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "expected_unique_runs": len(expected),
        "actual_unique_config_hashes": len(actual),
        "checks": checks,
        "missing_config_hashes": missing,
        "unexpected_config_hashes": unexpected,
        "duplicate_config_hashes": duplicates,
        "incomplete_config_hashes": incomplete,
        "malformed_run_records": malformed,
        "training_git_shas": sorted({str(value.get("git_sha")) for value in records}),
        "data_manifest_shas": sorted({str(value.get("data_manifest_sha256")) for value in records}),
        "missing_prediction_files": missing_prediction_files,
        "prediction_hash_mismatches": prediction_hash_mismatches,
        "missing_checkpoint_files": missing_checkpoint_files,
        "configuration_hash_mismatches": configuration_hash_mismatches,
        "run_directory_mismatches": run_directory_mismatches,
        "checkpoint_inventory": checkpoint_inventory,
    }


def collect_runs(run_root: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for path in sorted(Path(run_root).glob("runs/*/run.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        base = {
            "run_id": record.get("run_id"),
            "protocol_id": record.get("protocol_id"),
            "model_stage": record.get("model_stage"),
            "seed": record.get("seed"),
            "context_size": record.get("context_size"),
            "relation_retention": record.get("relation_retention"),
            "status": record.get("status"),
            "config_hash": record.get("config_hash"),
            "git_sha": record.get("git_sha"),
            "split_sha256": record.get("split_sha256"),
            "data_manifest_sha256": record.get("data_manifest_sha256"),
            "wall_seconds": record.get("wall_seconds"),
            "parameter_count": record.get("parameter_count"),
            "peak_gpu_memory_bytes": record.get("peak_gpu_memory_bytes"),
            "peak_cpu_rss_kib": record.get("peak_cpu_rss_kib"),
            "epochs_completed": record.get("epochs_completed"),
            "prediction_sha256": record.get("prediction_sha256"),
        }
        if record.get("status") != "COMPLETE":
            failures.append({**base, "failure_reason": record.get("failure_reason")})
            continue
        source = record["source_validation_metrics"]
        target = record["held_out_metrics"]
        source_compute = record.get("source_validation_compute", {})
        if target is None:
            continue
        rows.append(
            {
                **base,
                "protocol_type": _protocol_type(record["protocol_id"]),
                "fold_index": _fold_index(record["protocol_id"]),
                **{f"source_validation_{key}": source[key] for key in ("macro_f1", "balanced_accuracy", "accuracy", "ece")},
                **{f"held_out_{key}": target[key] for key in ("macro_f1", "balanced_accuracy", "accuracy", "ece")},
                "inference_seconds": target["compute"]["inference_seconds"],
                "inference_samples_per_second": target["compute"]["samples_per_second"],
                "source_validation_inference_seconds": float(source_compute.get("inference_seconds", 0.0)),
                "training_selection_seconds": max(
                    float(record.get("wall_seconds", 0.0))
                    - float(source_compute.get("inference_seconds", 0.0))
                    - float(target["compute"]["inference_seconds"]),
                    0.0,
                ),
                "attention_entropy_mean": target["compute"].get("attention_entropy_mean", 0.0),
                "effective_peer_count_mean": target["compute"].get("effective_peer_count_mean", 0.0),
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(failures)


def collect_diagnostics(run_root: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    group_rows: list[dict[str, Any]] = []
    relation_rows: list[dict[str, Any]] = []
    for path in sorted(Path(run_root).glob("runs/*/run.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("status") != "COMPLETE" or record.get("held_out_metrics") is None:
            continue
        held = record["held_out_metrics"]
        base = {
            "run_id": record["run_id"],
            "protocol_id": record["protocol_id"],
            "model_stage": record["model_stage"],
            "seed": record["seed"],
            "protocol_type": _protocol_type(record["protocol_id"]),
            "context_size": record.get("context_size"),
            "relation_retention": record.get("relation_retention"),
        }
        for group_type, field in (("receiver", "per_receiver_macro_f1"), ("day", "per_day_macro_f1")):
            for group, value in held.get(field, {}).items():
                group_rows.append({**base, "group_type": group_type, "group_id": group, "macro_f1": float(value)})
        for partition, values in record.get("relation_statistics", {}).items():
            relation_rows.append({**base, "partition": partition, **values})
    return pd.DataFrame(group_rows), pd.DataFrame(relation_rows)


def collect_class_support_performance(run_root: str | Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    root = Path(run_root)
    for path in sorted(root.glob("runs/receiver_fold_*/run.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("status") != "COMPLETE" or record.get("model_stage") not in {"P0", "P2"}:
            continue
        if record.get("context_size") != 32 or record.get("relation_retention") != 1.0:
            continue
        predictions = path.parent / "predictions.csv"
        if not predictions.exists():
            continue
        frame = pd.read_csv(predictions, usecols=["true_transmitter_index", "predicted_transmitter_index"])
        for target, group in frame.groupby("true_transmitter_index", sort=True):
            true = group["true_transmitter_index"].to_numpy()
            predicted = group["predicted_transmitter_index"].to_numpy()
            # Per-class F1 is computed one-vs-rest over the complete prediction file.
            all_true = frame["true_transmitter_index"].to_numpy() == int(target)
            all_pred = frame["predicted_transmitter_index"].to_numpy() == int(target)
            tp = int(np.sum(all_true & all_pred)); fp = int(np.sum(~all_true & all_pred)); fn = int(np.sum(all_true & ~all_pred))
            f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
            rows.append({"protocol_id": record["protocol_id"], "fold_index": _fold_index(record["protocol_id"]), "seed": record["seed"], "model_stage": record["model_stage"], "transmitter_index": int(target), "test_support": len(group), "f1": float(f1)})
    return pd.DataFrame(rows)


def postfreeze_error_diagnostics(
    run_root: str | Path,
    converted_root: str | Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Audit frozen P0/P2 errors against context fields; never returns model inputs."""
    acquisition, _ = load_converted_tables(converted_root)
    acquisition = acquisition[["sample_id", "data_quality_flags"]].copy()
    acquisition["sample_id"] = acquisition["sample_id"].astype(str)
    rows: list[dict[str, Any]] = []
    for path in sorted(Path(run_root).glob("runs/receiver_fold_*/run.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("status") != "COMPLETE" or record.get("model_stage") not in {"P0", "P2"}:
            continue
        if record.get("context_size") != 32 or record.get("relation_retention") != 1.0:
            continue
        predictions = pd.read_csv(
            path.parent / "predictions.csv",
            dtype={"sample_id": "string", "receiver_id": "string", "day_id": "string"},
            usecols=["sample_id", "true_transmitter_index", "predicted_transmitter_index", "receiver_id", "day_id"],
            keep_default_na=False,
        )
        predictions = predictions.merge(acquisition, on="sample_id", how="left", validate="one_to_one")
        if predictions["data_quality_flags"].isna().any():
            raise ValueError("post-freeze diagnostic found samples without acquisition metadata")
        predictions["error"] = predictions["true_transmitter_index"] != predictions["predicted_transmitter_index"]
        base = {"protocol_id": record["protocol_id"], "fold_index": _fold_index(record["protocol_id"]), "seed": record["seed"], "model_stage": record["model_stage"]}
        for field in ("receiver_id", "day_id", "data_quality_flags", "true_transmitter_index"):
            for value, group in predictions.groupby(field, sort=True, dropna=False):
                rows.append({**base, "audit_field": field, "audit_value": str(value), "sample_count": len(group), "error_rate": float(group["error"].mean())})
    detail = pd.DataFrame(rows)
    summary: dict[str, Any] = {"diagnostic_only": True, "used_for_model_redesign": False, "fields": {}}
    if detail.empty:
        return detail, summary
    for field, part in detail.groupby("audit_field", sort=True):
        group_stats = part.groupby(["model_stage", "audit_value"], as_index=False).agg(sample_count=("sample_count", "sum"), error_rate=("error_rate", "mean"))
        correlations: dict[str, float | None] = {}
        for model, model_rows in group_stats.groupby("model_stage", sort=True):
            value = model_rows["sample_count"].rank().corr(model_rows["error_rate"].rank()) if len(model_rows) > 1 else np.nan
            correlations[str(model)] = None if not np.isfinite(value) else float(value)
        summary["fields"][field] = {
            "unique_values": int(group_stats["audit_value"].nunique()),
            "error_rate_min": float(group_stats["error_rate"].min()),
            "error_rate_max": float(group_stats["error_rate"].max()),
            "support_error_spearman_by_model": correlations,
        }
    return detail, summary


def _protocol_type(protocol: str) -> str:
    if protocol.startswith("receiver_fold_"): return "receiver_holdout"
    if protocol.startswith("day_fold_"): return "day_holdout"
    if protocol.startswith("receiver_day_stress_"): return "receiver_day_stress"
    return "unknown"


def _fold_index(protocol: str) -> int:
    try: return int(protocol.rsplit("_", 1)[-1])
    except ValueError: return -1


def select_primary(frame: pd.DataFrame, protocol_type: str) -> pd.DataFrame:
    selected = frame[
        (frame["protocol_type"] == protocol_type)
        & (frame["context_size"] == 32)
        & (
            ((frame["model_stage"] == "P2_NULL") & (frame["relation_retention"] == 0.0))
            | ((frame["model_stage"] != "P2_NULL") & (frame["relation_retention"] == 1.0))
        )
    ].copy()
    return selected.drop_duplicates(["protocol_id", "model_stage", "seed"], keep="first")


def descriptive_summary(frame: pd.DataFrame, group_fields: list[str]) -> pd.DataFrame:
    metrics = ["source_validation_macro_f1", "held_out_macro_f1", "held_out_balanced_accuracy", "held_out_accuracy", "held_out_ece"]
    rows: list[dict[str, Any]] = []
    for key, group in frame.groupby(group_fields, sort=True, dropna=False):
        key = key if isinstance(key, tuple) else (key,)
        row = dict(zip(group_fields, key)); row["run_count"] = len(group)
        for metric in metrics:
            values = group[metric].to_numpy(dtype=float)
            row.update({
                f"{metric}_mean": float(values.mean()),
                f"{metric}_std": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
                f"{metric}_median": float(np.median(values)),
                f"{metric}_min": float(values.min()),
                f"{metric}_max": float(values.max()),
            })
        rows.append(row)
    return pd.DataFrame(rows)


def paired_differences(primary: pd.DataFrame) -> pd.DataFrame:
    index = ["protocol_id", "fold_index", "seed"]
    rows: list[dict[str, Any]] = []
    for left, right in PAIRS:
        a = primary[primary["model_stage"] == left].set_index(index)
        b = primary[primary["model_stage"] == right].set_index(index)
        common = a.index.intersection(b.index)
        for key in common:
            rows.append(
                {
                    "protocol_id": key[0],
                    "fold_index": key[1],
                    "seed": key[2],
                    "comparison": f"{left}-{right}",
                    "held_out_macro_f1_delta": float(a.loc[key, "held_out_macro_f1"] - b.loc[key, "held_out_macro_f1"]),
                    "source_validation_macro_f1_delta": float(a.loc[key, "source_validation_macro_f1"] - b.loc[key, "source_validation_macro_f1"]),
                }
            )
    return pd.DataFrame(rows)


def hierarchical_fold_bootstrap(differences: pd.DataFrame, *, replicates: int = 2000, seed: int = 20260902) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for comparison, group in differences.groupby("comparison", sort=True):
        folds = sorted(group["fold_index"].unique())
        fold_values = {fold: group[group["fold_index"] == fold]["held_out_macro_f1_delta"].to_numpy(dtype=float) for fold in folds}
        estimates = np.empty(replicates, dtype=float)
        for replicate in range(replicates):
            sampled = rng.choice(folds, size=len(folds), replace=True)
            estimates[replicate] = np.mean([value for fold in sampled for value in fold_values[int(fold)]])
        observed = float(group["held_out_macro_f1_delta"].mean())
        rows.append(
            {
                "comparison": comparison,
                "observed_mean_delta": observed,
                "bootstrap_replicates": replicates,
                "cluster_unit": "receiver_fold",
                "paired_seed_differences_preserved": True,
                "ci_2_5": float(np.percentile(estimates, 2.5)),
                "ci_97_5": float(np.percentile(estimates, 97.5)),
                "descriptive_only": True,
            }
        )
    return pd.DataFrame(rows)


def go_no_go(
    primary: pd.DataFrame,
    differences: pd.DataFrame,
    *,
    leakage_gate_passed: bool,
) -> dict[str, Any]:
    def criterion(comparison: str, metric: str = "held_out_macro_f1_delta") -> tuple[float, dict[int, float], int]:
        subset = differences[differences["comparison"] == comparison]
        fold = {int(key): float(value) for key, value in subset.groupby("fold_index")[metric].mean().items()}
        return float(subset[metric].mean()), fold, sum(value > 0 for value in fold.values())
    p2_p0, p2_p0_folds, p2_p0_positive = criterion("P2-P0")
    p2_shuffle, p2_shuffle_folds, p2_shuffle_positive = criterion("P2-P2_SHUFFLED")
    p2_wide, p2_wide_folds, p2_wide_positive = criterion("P2-P0_WIDE")
    source_subset = differences[differences["comparison"] == "P2-P0"]
    source_fold = source_subset.groupby("fold_index")["source_validation_macro_f1_delta"].mean()
    source_mean = float(source_subset["source_validation_macro_f1_delta"].mean())
    criteria = {
        "source_validation_reproducible": source_mean > 0 and int((source_fold > 0).sum()) >= 4,
        "held_out_not_degraded_beyond_0_01": p2_p0 >= -0.01,
        "mechanism_specific_vs_shuffled": p2_shuffle > 0 and p2_shuffle_positive >= 4,
        "capacity_control_advantage": p2_wide > 0 and p2_wide_positive >= 4,
        "benefit_not_one_fold": p2_p0_positive >= 3,
        "leakage_gate": bool(leakage_gate_passed),
    }
    if all(criteria.values()): verdict = "GO"
    elif criteria["leakage_gate"] and criteria["held_out_not_degraded_beyond_0_01"] and sum(criteria.values()) >= 4: verdict = "CONDITIONAL GO"
    else: verdict = "NO-GO"
    return {
        "verdict": verdict,
        "criteria": criteria,
        "descriptive_values": {
            "p2_minus_p0_mean": p2_p0,
            "p2_minus_p0_fold_means": p2_p0_folds,
            "p2_minus_shuffled_mean": p2_shuffle,
            "p2_minus_shuffled_fold_means": p2_shuffle_folds,
            "p2_minus_p0_wide_mean": p2_wide,
            "p2_minus_p0_wide_fold_means": p2_wide_folds,
            "source_validation_p2_minus_p0_mean": source_mean,
            "source_validation_fold_means": {int(key): float(value) for key, value in source_fold.items()},
        },
        "statistical_significance_claimed": False,
    }
