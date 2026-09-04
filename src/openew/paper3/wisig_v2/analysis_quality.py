"""Fail-closed grain, bounds, and completeness checks for V2 analysis outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from .analysis import DESCRIPTIVE_COMPARISONS, PRIMARY_COMPARISONS, PRIMARY_RUN_COUNT
from .hashing import canonical_json_bytes
from .suite import PRIMARY_MODELS


UNIT_METRICS = ("macro_f1", "accuracy", "balanced_accuracy", "ece")
EXPECTED_COMPARISONS = (*DESCRIPTIVE_COMPARISONS, "P2_MINUS_BEST_SOURCE_DG")


def finite_unit_interval(frame: pd.DataFrame, columns: Sequence[str]) -> bool:
    for column in columns:
        if column not in frame:
            return False
        values = frame[column].to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values < 0).any() or (values > 1).any():
            return False
    return True


def unique_key(frame: pd.DataFrame, columns: Sequence[str]) -> bool:
    return all(column in frame for column in columns) and not frame.duplicated(list(columns)).any()


def boolean_column_equals(frame: pd.DataFrame, column: str, expected: bool) -> bool:
    if column not in frame:
        return False
    normalized = frame[column].map(
        lambda value: value if isinstance(value, (bool, np.bool_)) else {"true": True, "false": False}.get(str(value).strip().lower())
    )
    return normalized.notna().all() and bool((normalized == expected).all())


def frame_contract(
    frame: pd.DataFrame,
    *,
    expected_rows: int,
    key: Sequence[str],
    metric_columns: Sequence[str] = UNIT_METRICS,
) -> dict[str, bool | int]:
    return {
        "row_count": len(frame),
        "expected_row_count": bool(len(frame) == expected_rows),
        "key_unique": unique_key(frame, key),
        "metrics_bounded": finite_unit_interval(frame, metric_columns),
    }


def sensitivity_contract(frame: pd.DataFrame, setting: str, expected_values: Sequence[int], expected_rows: int) -> dict[str, bool | int]:
    """Validate a receiver/seed sensitivity grid without treating seeds as units."""

    required = {"receiver_id", "seed", setting, *UNIT_METRICS}
    return {
        "row_count": len(frame),
        "expected_row_count": len(frame) == expected_rows,
        "key_unique": required.issubset(frame.columns) and unique_key(frame, ("receiver_id", "seed", setting)),
        "receiver_count": "receiver_id" in frame and frame["receiver_id"].nunique() == 32,
        "seed_set_complete": "seed" in frame and set(frame["seed"].astype(int)) == {829, 1829, 2829, 3829, 4829},
        "setting_set_exact": setting in frame and set(frame[setting].astype(int)) == set(expected_values),
        "metrics_bounded": finite_unit_interval(frame, UNIT_METRICS),
    }


def inference_benchmark_contract(frame: pd.DataFrame) -> dict[str, bool | int]:
    """Validate the fixed seed-829 receiver/model latency benchmark."""

    return {
        "row_count": len(frame),
        "expected_row_count": len(frame) == 32 * len(PRIMARY_MODELS),
        "key_unique": unique_key(frame, ("receiver_id", "model", "seed")),
        "receiver_count": "receiver_id" in frame and frame["receiver_id"].nunique() == 32,
        "model_set_complete": "model" in frame and set(frame["model"].astype(str)) == set(PRIMARY_MODELS),
        "single_frozen_seed": "seed" in frame and set(frame["seed"].astype(int)) == {829},
        "timings_positive": all(
            column in frame and np.isfinite(frame[column].to_numpy(dtype=float)).all() and (frame[column] > 0).all()
            for column in ("latency_seconds_median", "samples_per_second_median")
        ),
        "probabilities_reproduced": "max_probability_reproduction_error" in frame
        and np.isfinite(frame["max_probability_reproduction_error"].to_numpy(dtype=float)).all()
        and (frame["max_probability_reproduction_error"] <= 1e-5).all(),
        "target_labels_not_read": boolean_column_equals(frame, "target_labels_read", False),
    }


def day_receiver_detail_contract(frame: pd.DataFrame) -> dict[str, bool | int]:
    """Require a complete 32-receiver map in every day/model/seed row."""

    if "per_receiver_macro_f1_json" not in frame:
        return {"row_count": len(frame), "every_row_has_32_receivers": False, "receiver_key_set_stable": False, "receiver_metrics_bounded": False}
    mappings: list[dict[str, float]] = []
    try:
        for value in frame["per_receiver_macro_f1_json"]:
            raw = json.loads(str(value))
            if not isinstance(raw, dict):
                raise ValueError("receiver detail is not a mapping")
            mappings.append({str(key): float(metric) for key, metric in raw.items()})
    except (TypeError, ValueError, json.JSONDecodeError):
        return {"row_count": len(frame), "every_row_has_32_receivers": False, "receiver_key_set_stable": False, "receiver_metrics_bounded": False}
    key_sets = [set(value) for value in mappings]
    metrics = np.asarray([metric for value in mappings for metric in value.values()], dtype=float)
    return {
        "row_count": len(frame),
        "every_row_has_32_receivers": bool(mappings) and all(len(value) == 32 for value in mappings),
        "receiver_key_set_stable": bool(key_sets) and all(value == key_sets[0] for value in key_sets),
        "receiver_metrics_bounded": bool(len(metrics)) and np.isfinite(metrics).all() and bool(((metrics >= 0) & (metrics <= 1)).all()),
    }


def validate_analysis_outputs(
    analysis_root: str | Path,
    destination: str | Path,
    *,
    day_csv: str | Path | None = None,
    grouped_csv: str | Path | None = None,
    equalized_csv: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(analysis_root)
    required = {
        "primary": "primary_receiver_seed_results.csv",
        "receiver": "primary_receiver_averaged_results.csv",
        "paired_seed": "paired_receiver_seed_differences.csv",
        "paired_receiver": "paired_receiver_averaged_differences.csv",
        "inference": "receiver_level_inference.json",
        "preflight": "blind_archive_preflight.json",
        "unblinding": "unblinding_manifest.json",
        "selection": "source_validation_method_selection.json",
        "context": "context_receiver_seed_diagnostics.csv",
    }
    missing = sorted(filename for filename in required.values() if not (root / filename).is_file())
    if missing:
        raise FileNotFoundError(f"missing required V2 analysis files: {missing}")
    primary = pd.read_csv(root / required["primary"])
    receiver = pd.read_csv(root / required["receiver"])
    paired_seed = pd.read_csv(root / required["paired_seed"])
    paired_receiver = pd.read_csv(root / required["paired_receiver"])
    inference = json.loads((root / required["inference"]).read_text(encoding="utf-8"))
    preflight = json.loads((root / required["preflight"]).read_text(encoding="utf-8"))
    unblinding = json.loads((root / required["unblinding"]).read_text(encoding="utf-8"))
    selection = json.loads((root / required["selection"]).read_text(encoding="utf-8"))
    context = pd.read_csv(root / required["context"])
    comparison_counts = paired_seed.groupby("comparison").size().to_dict()
    receiver_comparison_counts = paired_receiver.groupby("comparison").size().to_dict()
    checks = {
        "primary_row_count": len(primary) == PRIMARY_RUN_COUNT,
        "primary_key_unique": unique_key(primary, ("receiver_id", "model", "seed")),
        "primary_receiver_count": primary["receiver_id"].nunique() == 32,
        "primary_model_set": set(primary["model"].astype(str)) == set(PRIMARY_MODELS),
        "primary_seed_set": set(primary["seed"].astype(int)) == {829, 1829, 2829, 3829, 4829},
        "primary_metrics_bounded": finite_unit_interval(primary, UNIT_METRICS),
        "receiver_row_count": len(receiver) == 32 * len(PRIMARY_MODELS),
        "receiver_key_unique": unique_key(receiver, ("receiver_id", "model")),
        "five_seeds_per_receiver_model": "seed_count" in receiver and (receiver["seed_count"] == 5).all(),
        "receiver_metrics_bounded": finite_unit_interval(receiver, UNIT_METRICS),
        "paired_seed_key_unique": unique_key(paired_seed, ("comparison", "receiver_id", "seed")),
        "paired_receiver_key_unique": unique_key(paired_receiver, ("comparison", "receiver_id")),
        "comparison_set_complete": set(comparison_counts) == set(EXPECTED_COMPARISONS),
        "paired_seed_count_per_comparison": all(comparison_counts.get(name) == 32 * 5 for name in EXPECTED_COMPARISONS),
        "paired_receiver_count_per_comparison": all(receiver_comparison_counts.get(name) == 32 for name in EXPECTED_COMPARISONS),
        "inference_unit_receiver": inference.get("primary_unit") == "receiver",
        "seed_averaging_before_inference": inference.get("seed_aggregation") == "mean within receiver before inference",
        "primary_inference_family_exact": set(inference.get("comparisons", {})) == set(PRIMARY_COMPARISONS),
        "receiver_bootstrap_configuration": all(value.get("bootstrap", {}).get("receiver_count") == 32 and value.get("bootstrap", {}).get("replicates") == 10_000 for value in inference.get("comparisons", {}).values()),
        "receiver_permutation_configuration": all(value.get("sign_flip", {}).get("receiver_count") == 32 and value.get("sign_flip", {}).get("permutations") == 100_000 for value in inference.get("comparisons", {}).values()),
        "blind_preflight_complete": preflight.get("status") == "PASS" and preflight.get("record_count") == PRIMARY_RUN_COUNT and preflight.get("labels_read") is False,
        "one_time_unblinding_complete": unblinding.get("completed_primary_runs") == PRIMARY_RUN_COUNT and unblinding.get("expected_primary_runs") == PRIMARY_RUN_COUNT,
        "method_selection_source_only": selection.get("selection_uses_target_metrics") is False,
        "method_selection_equal_weights_validation_receivers": set(selection.get("groups", {})) == {"same_information_tta", "source_dg"}
        and all(group.get("selection_metric") == "equal-weight mean of per-receiver source-validation macro-F1" for group in selection.get("groups", {}).values()),
        "context_diagnostic_row_count": len(context) == PRIMARY_RUN_COUNT,
        "context_diagnostic_key_unique": unique_key(context, ("receiver_id", "model", "seed")),
        "context_diagnostic_model_set": set(context["model"].astype(str)) == set(PRIMARY_MODELS),
        "context_diagnostic_receiver_count": context["receiver_id"].nunique() == 32,
        "context_diagnostic_support_query_disjoint": "support_query_overlap" in context and (context["support_query_overlap"] == 0).all(),
        "context_diagnostic_common_finite": all(
            column in context and np.isfinite(context[column].to_numpy(dtype=float)).all()
            for column in ("support_count", "query_count", "support_query_overlap")
        ),
        "p2_context_contract": len(context[context["model"] == "P2"]) == 32 * 5
        and (context.loc[context["model"] == "P2", "support_count"] == 128).all()
        and (context.loc[context["model"] == "P2", "context_k"] == 32).all()
        and (context.loc[context["model"] == "P2", "isolated_query_count"] == 0).all()
        and np.isfinite(
            context.loc[
                context["model"] == "P2",
                ("attention_entropy_mean", "effective_peer_count_mean", "inference_seconds", "samples_per_second"),
            ].to_numpy(dtype=float)
        ).all(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    optional: dict[str, Any] = {}
    if (root / "support_composition_audit.csv").exists():
        composition = pd.read_csv(root / "support_composition_audit.csv")
        optional["support_composition"] = {
            "row_count": len(composition),
            "expected_row_count": len(composition) == 32 * 5,
            "key_unique": unique_key(composition, ("receiver_id", "seed")),
            "audit_only_labels_disclosed": boolean_column_equals(composition, "labels_used_for_audit_only", True),
        }
        optional["support_composition"] = {name: int(value) if name == "row_count" else bool(value) for name, value in optional["support_composition"].items()}
    if (root / "composition_oracle_results.csv").exists():
        oracle = pd.read_csv(root / "composition_oracle_results.csv")
        optional["oracle_composition"] = {
            "row_count": len(oracle),
            "expected_row_count": len(oracle) == 32 * 5 * 3,
            "key_unique": unique_key(oracle, ("receiver_id", "seed", "condition")),
            "receiver_count": "receiver_id" in oracle and oracle["receiver_id"].nunique() == 32,
            "seed_set_complete": "seed" in oracle and set(oracle["seed"].astype(int)) == {829, 1829, 2829, 3829, 4829},
            "condition_set_exact": "condition" in oracle and set(oracle["condition"].astype(str)) == {"TRANSMITTER_PURE_ORACLE", "SAME_CLASS_EXCLUDED_ORACLE", "SAME_CLASS_ONLY_ORACLE"},
            "deployable_false": boolean_column_equals(oracle, "deployable", False),
            "label_dependency_disclosed": boolean_column_equals(oracle, "labels_used_to_construct_context", True),
            "evaluable_within_query": {"evaluable_query_count", "query_count"}.issubset(oracle.columns)
            and (oracle["evaluable_query_count"] >= 0).all()
            and (oracle["evaluable_query_count"] <= oracle["query_count"]).all(),
        }
        optional["oracle_composition"] = {name: int(value) if name == "row_count" else bool(value) for name, value in optional["oracle_composition"].items()}
    if (root / "support_budget_results.csv").exists():
        frame = pd.read_csv(root / "support_budget_results.csv")
        optional["support_budget"] = sensitivity_contract(frame, "support_budget", (16, 32, 64, 128, 256), 32 * 5 * 5)
    if (root / "context_k_results.csv").exists():
        frame = pd.read_csv(root / "context_k_results.csv")
        optional["context_k"] = sensitivity_contract(frame, "context_k", (8, 16, 32, 64), 32 * 5 * 4)
    if (root / "compute_budget_per_run.csv").exists():
        frame = pd.read_csv(root / "compute_budget_per_run.csv")
        optional["compute"] = {
            "row_count": len(frame),
            "expected_row_count": len(frame) == PRIMARY_RUN_COUNT,
            "run_id_unique": unique_key(frame, ("run_id",)),
            "model_set_complete": "model" in frame and set(frame["model"].astype(str)) == set(PRIMARY_MODELS),
            "resource_values_nonnegative": all(
                column in frame and np.isfinite(frame[column].to_numpy(dtype=float)).all() and (frame[column] >= 0).all()
                for column in (
                    "parameter_count",
                    "measured_total_wall_seconds",
                    "measured_peak_cpu_rss_kib",
                    "measured_peak_gpu_memory_bytes",
                    "support_encoding_flops_approx",
                    "support_statistics_ops_approx",
                    "total_test_flops_approx",
                )
            ),
        }
    if (root / "standardized_inference_benchmark.csv").exists():
        frame = pd.read_csv(root / "standardized_inference_benchmark.csv")
        optional["standardized_inference"] = inference_benchmark_contract(frame)
    if (root / "day_receiver_seed_results.csv").exists():
        frame = pd.read_csv(root / "day_receiver_seed_results.csv")
        optional["day"] = {
            "row_count": len(frame),
            "expected_row_count": len(frame) == 4 * len(PRIMARY_MODELS) * 5,
            "key_unique": unique_key(frame, ("protocol_id", "model", "seed")),
            "day_count": "test_day" in frame and frame["test_day"].nunique() == 4,
            "model_set_complete": "model" in frame and set(frame["model"].astype(str)) == set(PRIMARY_MODELS),
            "seed_set_complete": "seed" in frame and set(frame["seed"].astype(int)) == {829, 1829, 2829, 3829, 4829},
            "metrics_bounded": finite_unit_interval(frame, UNIT_METRICS),
            **{key: value for key, value in day_receiver_detail_contract(frame).items() if key != "row_count"},
        }
    if day_csv is not None:
        day = pd.read_csv(day_csv)
        optional["day_secondary_external"] = {
            **frame_contract(day, expected_rows=4 * len(PRIMARY_MODELS) * 5, key=("protocol_id", "model", "seed")),
            "four_days": bool(day["test_day"].nunique() == 4),
            "model_set_complete": bool(set(day["model"].astype(str)) == set(PRIMARY_MODELS)),
            "seed_set_complete": bool(set(day["seed"].astype(int)) == {829, 1829, 2829, 3829, 4829}),
            **{key: value for key, value in day_receiver_detail_contract(day).items() if key != "row_count"},
        }
    if grouped_csv is not None:
        grouped = pd.read_csv(grouped_csv)
        optional["grouped_receiver_external"] = {
            **frame_contract(grouped, expected_rows=3 * 32 * 5 * 3, key=("repeat", "fold", "receiver_id", "model", "seed")),
            "receiver_count": bool(grouped["receiver_id"].nunique() == 32),
            "repeat_count": bool(grouped["repeat"].nunique() == 3),
            "model_set_complete": bool(set(grouped["model"].astype(str)) == {"P0", "P2", "P2_SHUFFLED"}),
        }
    if equalized_csv is not None:
        equalized = pd.read_csv(equalized_csv)
        optional["equalized_external"] = {
            **frame_contract(equalized, expected_rows=32 * 3, key=("receiver_id", "model", "seed")),
            "receiver_count": bool(equalized["receiver_id"].nunique() == 32),
            "single_preregistered_seed": bool(set(equalized["seed"].astype(int)) == {829}),
            "model_set_complete": bool(set(equalized["model"].astype(str)) == {"P0", "P2", "P2_SHUFFLED"}),
        }
    optional_pass = all(all(value for key, value in group.items() if key != "row_count") for group in optional.values())
    payload = {
        "schema_version": 1,
        "status": "PASS" if all(checks.values()) and optional_pass else "FAIL",
        "required_checks": checks,
        "optional_checks_present": optional,
        "primary_grain": "one row per held-out receiver, model, and seed",
        "inferential_grain": "one five-seed-averaged paired difference per held-out receiver",
        "packet_level_inference_used": False,
    }
    destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(canonical_json_bytes(payload))
    if payload["status"] != "PASS":
        raise RuntimeError("V2 analysis quality validation failed")
    return payload
