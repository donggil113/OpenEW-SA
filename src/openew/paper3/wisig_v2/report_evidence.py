"""Assemble a compact, receiver-grain evidence ledger for V2 reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .hashing import canonical_json_bytes, sha256_file
from .suite import PRIMARY_MODELS


def _receiver_setting_summary(frame: pd.DataFrame, setting: str, metric: str = "macro_f1") -> list[dict[str, Any]]:
    if "receiver_id" not in frame or setting not in frame or metric not in frame:
        raise ValueError(f"receiver_id, {setting}, and {metric} are required")
    receiver = frame.groupby(["receiver_id", setting], as_index=False)[metric].mean()
    rows: list[dict[str, Any]] = []
    for value, group in receiver.groupby(setting, sort=True):
        scores = group[metric].to_numpy(dtype=float)
        if len(scores) != 32 or not np.isfinite(scores).all():
            raise RuntimeError(f"{setting}={value} does not contain 32 finite receiver-level values")
        rows.append(
            {
                setting: int(value) if isinstance(value, (int, np.integer)) else float(value) if isinstance(value, (float, np.floating)) else str(value),
                "receiver_count": len(scores),
                "mean": float(scores.mean()),
                "std": float(scores.std(ddof=1)),
                "median": float(np.median(scores)),
                "min": float(scores.min()),
                "max": float(scores.max()),
            }
        )
    return rows


def _model_receiver_summary(frame: pd.DataFrame, metric: str) -> dict[str, dict[str, float | int]]:
    if not {"receiver_id", "model", metric}.issubset(frame.columns):
        raise ValueError(f"receiver_id, model, and {metric} are required")
    receiver = frame.groupby(["receiver_id", "model"], as_index=False)[metric].mean()
    result: dict[str, dict[str, float | int]] = {}
    for model, group in receiver.groupby("model", sort=True):
        values = group[metric].to_numpy(dtype=float)
        if not len(values) or not np.isfinite(values).all():
            raise RuntimeError(f"model {model} has no finite receiver-level values")
        result[str(model)] = {
            "receiver_count": len(values),
            "mean": float(values.mean()),
            "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
            "median": float(np.median(values)),
            "min": float(values.min()),
            "max": float(values.max()),
        }
    return result


def _day_receiver_summary(frame: pd.DataFrame) -> dict[str, dict[str, float | int]]:
    """Expand serialized per-receiver day metrics before equal-weight summary."""

    required = {"model", "seed", "test_day", "per_receiver_macro_f1_json"}
    if not required.issubset(frame.columns):
        raise ValueError(f"day results are missing columns: {sorted(required - set(frame.columns))}")
    rows: list[dict[str, Any]] = []
    for record in frame.to_dict(orient="records"):
        values = json.loads(str(record["per_receiver_macro_f1_json"]))
        if not isinstance(values, dict) or not values:
            raise RuntimeError("day result lacks per-receiver macro-F1 values")
        for receiver, score in values.items():
            rows.append(
                {
                    "receiver_id": str(receiver),
                    "model": str(record["model"]),
                    "seed": int(record["seed"]),
                    "test_day": str(record["test_day"]),
                    "macro_f1": float(score),
                }
            )
    expanded = pd.DataFrame(rows)
    if expanded["receiver_id"].nunique() != 32 or not np.isfinite(expanded["macro_f1"]).all():
        raise RuntimeError("day evidence must contain 32 receivers with finite metrics")
    return _model_receiver_summary(expanded, "macro_f1")


def _oracle_condition_summary(frame: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Summarize nondeployable oracle rows without hiding unevaluable queries."""

    required = {"receiver_id", "seed", "condition", "macro_f1", "query_count", "evaluable_query_count"}
    if not required.issubset(frame.columns):
        raise ValueError(f"oracle results are missing columns: {sorted(required - set(frame.columns))}")
    result: dict[str, dict[str, Any]] = {}
    for condition, group in frame.groupby("condition", sort=True):
        receiver = group.groupby("receiver_id", as_index=False)["macro_f1"].mean()
        finite = receiver[np.isfinite(receiver["macro_f1"].to_numpy(dtype=float))]["macro_f1"].to_numpy(dtype=float)
        query_count = int(group["query_count"].sum())
        evaluable_count = int(group["evaluable_query_count"].sum())
        result[str(condition)] = {
            "receiver_count_total": int(group["receiver_id"].nunique()),
            "receiver_count_evaluable": len(finite),
            "query_count": query_count,
            "evaluable_query_count": evaluable_count,
            "evaluable_fraction": float(evaluable_count / query_count) if query_count else 0.0,
            "mean": float(finite.mean()) if len(finite) else None,
            "std": float(finite.std(ddof=1)) if len(finite) > 1 else 0.0 if len(finite) == 1 else None,
            "median": float(np.median(finite)) if len(finite) else None,
            "min": float(finite.min()) if len(finite) else None,
            "max": float(finite.max()) if len(finite) else None,
            "deployable": False,
        }
        if str(condition) == "TRANSMITTER_PURE_ORACLE":
            required_pure = {"pure_support_label", "prediction_fraction_pure_support_label"}
            if not required_pure.issubset(group.columns):
                raise RuntimeError("transmitter-pure oracle is missing its bias diagnostic")
            bias = group.groupby("receiver_id", as_index=False)["prediction_fraction_pure_support_label"].mean()
            bias_values = bias["prediction_fraction_pure_support_label"].to_numpy(dtype=float)
            if len(bias_values) != 32 or not np.isfinite(bias_values).all():
                raise RuntimeError("transmitter-pure bias diagnostic must contain 32 finite receiver means")
            result[str(condition)]["prediction_fraction_pure_support_label_receiver_mean"] = float(bias_values.mean())
            result[str(condition)]["prediction_fraction_pure_support_label_receiver_range"] = [float(bias_values.min()), float(bias_values.max())]
            result[str(condition)]["selected_local_support_label_counts"] = {
                str(int(label)): int(count)
                for label, count in group["pure_support_label"].astype(int).value_counts().sort_index().items()
            }
    return result


def build_report_evidence(
    analysis_root: str | Path,
    integrity_report: str | Path,
    destination: str | Path,
    *,
    grouped_results: str | Path | None = None,
    equalized_results: str | Path | None = None,
) -> dict[str, Any]:
    """Build a source-backed report ledger after all required audits exist."""

    root = Path(analysis_root)
    required = {
        "primary": root / "primary_receiver_seed_results.csv",
        "paired": root / "paired_receiver_averaged_differences.csv",
        "paired_summary": root / "paired_difference_summary.csv",
        "inference": root / "receiver_level_inference.json",
        "selection": root / "source_validation_method_selection.json",
        "composition": root / "support_composition_audit.csv",
        "context": root / "context_receiver_seed_diagnostics.csv",
        "oracle": root / "composition_oracle_results.csv",
        "support_budget": root / "support_budget_results.csv",
        "context_k": root / "context_k_results.csv",
        "day": root / "day_receiver_seed_results.csv",
        "compute": root / "compute_budget_summary.csv",
        "inference_benchmark": root / "standardized_inference_benchmark_summary.csv",
        "postaudit": root / "target_proxy_postaudit_summary.json",
        "decision": root / "v2_go_no_go_decision.json",
        "quality": root / "analysis_quality_report.json",
        "unblinding": root / "unblinding_manifest.json",
        "preunblind": root.parent / "pre_unblinding_freeze.json",
        "integrity": Path(integrity_report),
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"report evidence is incomplete: {missing}")
    primary = pd.read_csv(required["primary"])
    if len(primary) != 32 * len(PRIMARY_MODELS) * 5:
        raise RuntimeError("primary report evidence must contain 32 receivers x all models x five seeds")
    if set(primary["model"].astype(str)) != set(PRIMARY_MODELS):
        raise RuntimeError("primary report evidence model set differs from the frozen suite")
    if primary.duplicated(["receiver_id", "model", "seed"]).any():
        raise RuntimeError("primary report evidence grain is not unique")
    paired = pd.read_csv(required["paired"])
    composition = pd.read_csv(required["composition"])
    context = pd.read_csv(required["context"])
    oracle = pd.read_csv(required["oracle"])
    support_budget = pd.read_csv(required["support_budget"])
    context_k = pd.read_csv(required["context_k"])
    day = pd.read_csv(required["day"])
    compute = pd.read_csv(required["compute"])
    inference_benchmark = pd.read_csv(required["inference_benchmark"])
    if len(composition) != 32 * 5:
        raise RuntimeError("support-composition audit is incomplete")
    if len(oracle) != 32 * 5 * 3 or not (oracle["deployable"].astype(str).str.lower() == "false").all():
        raise RuntimeError("oracle diagnostics are incomplete or not marked non-deployable")
    if len(day) != 4 * len(PRIMARY_MODELS) * 5:
        raise RuntimeError("day secondary evidence is incomplete")
    paired_means = paired.groupby("comparison", sort=True)["difference"].mean().to_dict()
    positive = paired.groupby("comparison", sort=True)["difference"].apply(lambda values: int((values > 0).sum())).to_dict()
    payload: dict[str, Any] = {
        "schema_version": 1,
        "evidence_grain": {
            "primary": "held-out receiver averaged over five seeds",
            "primary_receiver_count": 32,
            "seeds": [829, 1829, 2829, 3829, 4829],
            "packet_level_inference_used": False,
        },
        "primary_macro_f1": _model_receiver_summary(primary, "macro_f1"),
        "primary_paired_differences": {
            name: {"mean": float(value), "positive_receivers": int(positive[name]), "receiver_count": 32}
            for name, value in sorted(paired_means.items())
        },
        "receiver_inference": json.loads(required["inference"].read_text(encoding="utf-8")),
        "source_only_method_selection": json.loads(required["selection"].read_text(encoding="utf-8")),
        "support_composition": {
            "receiver_seed_rows": len(composition),
            "receiver_count": int(composition["receiver_id"].nunique()),
            "distinct_transmitters_range": [int(composition["distinct_transmitters"].min()), int(composition["distinct_transmitters"].max())],
            "class_entropy_nats_range": [float(composition["class_entropy_nats"].min()), float(composition["class_entropy_nats"].max())],
            "posthoc_correlations": json.loads(required["postaudit"].read_text(encoding="utf-8"))["support_composition_correlations"],
        },
        "p2_context_mechanism": {
            "receiver_seed_rows": int(len(context[context["model"] == "P2"])),
            "support_count": int(context.loc[context["model"] == "P2", "support_count"].min()),
            "context_k": int(context.loc[context["model"] == "P2", "context_k"].min()),
            "isolated_query_count": int(context.loc[context["model"] == "P2", "isolated_query_count"].sum()),
            "attention_entropy_mean": float(context.loc[context["model"] == "P2", "attention_entropy_mean"].mean()),
            "effective_peer_count_mean": float(context.loc[context["model"] == "P2", "effective_peer_count_mean"].mean()),
            "attention_is_not_causal_evidence": True,
        },
        "oracle_composition_controls": _oracle_condition_summary(oracle),
        "support_budget_sensitivity": _receiver_setting_summary(support_budget, "support_budget"),
        "context_k_sensitivity": _receiver_setting_summary(context_k, "context_k"),
        "day_secondary_macro_f1": _day_receiver_summary(day),
        "compute_budget": compute.sort_values("model").replace({np.nan: None}).to_dict(orient="records"),
        "standardized_inference_benchmark": inference_benchmark.sort_values("model").replace({np.nan: None}).to_dict(orient="records"),
        "decision": json.loads(required["decision"].read_text(encoding="utf-8")),
        "quality": json.loads(required["quality"].read_text(encoding="utf-8")),
        "integrity": json.loads(required["integrity"].read_text(encoding="utf-8")),
        "unblinding": json.loads(required["unblinding"].read_text(encoding="utf-8")),
        "preunblinding_freeze": json.loads(required["preunblind"].read_text(encoding="utf-8")),
        "source_files": {name: {"path": str(path), "sha256": sha256_file(path)} for name, path in sorted(required.items())},
    }
    if grouped_results is not None:
        grouped_path = Path(grouped_results)
        grouped = pd.read_csv(grouped_path)
        if len(grouped) != 3 * 32 * 5 * 3:
            raise RuntimeError("grouped receiver evidence is incomplete")
        payload["grouped_receiver_secondary_macro_f1"] = _model_receiver_summary(grouped, "macro_f1")
        payload["source_files"]["grouped"] = {"path": str(grouped_path), "sha256": sha256_file(grouped_path)}
    if equalized_results is not None:
        equalized_path = Path(equalized_results)
        equalized = pd.read_csv(equalized_path)
        if len(equalized) != 32 * 3:
            raise RuntimeError("equalized diagnostic evidence is incomplete")
        payload["equalized_diagnostic_macro_f1"] = _model_receiver_summary(equalized, "macro_f1")
        payload["source_files"]["equalized"] = {"path": str(equalized_path), "sha256": sha256_file(equalized_path)}
    if payload["quality"].get("status") != "PASS" or payload["integrity"].get("status") != "PASS":
        raise RuntimeError("quality and integrity reports must pass before report evidence is released")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(canonical_json_bytes(payload))
    temporary.replace(destination)
    return payload
