"""Deterministic post-unblinding reports for the receiver benchmark.

This module never trains or adapts a model.  It consumes the create-once
unblinding outputs and the hash-verified frozen V2 predictions.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig_v2.blinding import read_blind_predictions
from openew.paper3.wisig_v2.runner import remap_bundle_to_split_targets

from .contracts import BENCHMARK_SEEDS, CATASTROPHIC_MACRO_F1_DROP, PRIMARY_RECEIVER_COUNT
from .frozen import sha256_file

PRIMARY_REPORT_MODELS = ("P0", "P0_WIDE", "DG_CORAL", "DG_DANN", "DG_GROUPDRO", "RX_NORM", "T3A", "P2", "SUP_FT_128")
CALIBRATION_MODELS = ("P0", "T3A", "P2")


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def validate_unblinded_analysis(analysis_root: str | Path) -> dict[str, Any]:
    root = Path(analysis_root)
    manifest = json.loads((root / "unblinding_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "UNBLINDED_ONCE" or manifest.get("oracle_records") != 160 or manifest.get("budget_records") != 160:
        raise RuntimeError("one-time benchmark unblinding contract is incomplete")
    seed = pd.read_csv(root / "benchmark_receiver_seed_results.csv", dtype={"receiver_id": "string"})
    averaged = pd.read_csv(root / "benchmark_receiver_averaged_results.csv", dtype={"receiver_id": "string"})
    if seed.duplicated(["model", "receiver_id", "seed"]).any():
        raise RuntimeError("duplicate model/receiver/seed result")
    if len(set(seed.receiver_id)) != PRIMARY_RECEIVER_COUNT or set(seed.seed) != set(BENCHMARK_SEEDS):
        raise RuntimeError("receiver or seed grid changed")
    counts = seed.groupby("model").size().to_dict()
    if any(count != PRIMARY_RECEIVER_COUNT * len(BENCHMARK_SEEDS) for count in counts.values()):
        raise RuntimeError("incomplete primary model grid")
    if averaged.duplicated(["model", "receiver_id"]).any() or set(averaged.model) != set(seed.model):
        raise RuntimeError("receiver averaging output is inconsistent")
    metric_columns = ["macro_f1", "accuracy", "balanced_accuracy", "ece"]
    if not np.isfinite(seed[metric_columns].to_numpy(dtype=float)).all():
        raise FloatingPointError("non-finite primary metric")
    budget = pd.read_csv(root / "support_budget_all_methods.csv", dtype={"receiver_id": "string"})
    expected_budget = {"P2": {16, 32, 64, 128, 256}, "T3A": {0, 16, 32, 64, 128, 256}, "RX_NORM": {16, 32, 64, 128, 256}, "SOURCE_NORM": {0}}
    actual_budget = {method: set(map(int, part.support_budget)) for method, part in budget.groupby("method")}
    if actual_budget != expected_budget:
        raise RuntimeError(f"support-budget grid changed: {actual_budget}")
    return {"status": "PASS", "unblinding_time_utc": manifest["time_utc"], "models": sorted(counts), "receiver_count": 32, "seeds": list(BENCHMARK_SEEDS), "primary_rows": len(seed), "budget_rows": len(budget)}


def summarize_receiver_results(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"model", "receiver_id", "macro_f1", "accuracy", "balanced_accuracy", "ece"}
    if not required <= set(frame):
        raise ValueError(f"missing result fields: {sorted(required - set(frame))}")
    rows: list[dict[str, Any]] = []
    for method, part in frame.groupby("model", sort=True):
        for metric in ("macro_f1", "accuracy", "balanced_accuracy", "ece"):
            values = part[metric].to_numpy(dtype=float)
            rows.append({"model": method, "metric": metric, "receiver_count": len(values), "mean": values.mean(), "std": values.std(ddof=1), "median": np.median(values), "min": values.min(), "max": values.max()})
    return pd.DataFrame(rows)


def summarize_hardware(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (method, family), part in frame.groupby(["model", "hardware_family"], sort=True):
        values = part.macro_f1.to_numpy(dtype=float)
        rows.append({"model": method, "hardware_family": family, "receiver_count": len(values), "macro_f1_mean": values.mean(), "macro_f1_std": values.std(ddof=1) if len(values) > 1 else math.nan})
    result = pd.DataFrame(rows)
    baseline = result[result.model == "P0"][["hardware_family", "macro_f1_mean"]].rename(columns={"macro_f1_mean": "p0_macro_f1"})
    return result.merge(baseline, on="hardware_family", how="left", validate="many_to_one").assign(delta_from_p0=lambda value: value.macro_f1_mean - value.p0_macro_f1)


def summarize_catastrophic(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"model", "receiver_id", "seed", "delta_from_p0", "catastrophic"}
    if not required <= set(frame):
        raise ValueError("catastrophic frame has wrong schema")
    rows = []
    for method, part in frame.groupby("model", sort=True):
        rows.append({"model": method, "receiver_seed_records": len(part), "catastrophic_count": int(part.catastrophic.astype(bool).sum()), "catastrophic_fraction": float(part.catastrophic.astype(bool).mean()), "mean_delta_from_p0": float(part.delta_from_p0.mean()), "min_delta_from_p0": float(part.delta_from_p0.min()), "threshold": -CATASTROPHIC_MACRO_F1_DROP})
    return pd.DataFrame(rows)


def summarize_support_budgets(frame: pd.DataFrame) -> pd.DataFrame:
    receiver = frame.groupby(["method", "support_budget", "receiver_id"], as_index=False)[["macro_f1", "ece"]].mean()
    rows = []
    for (method, budget), part in receiver.groupby(["method", "support_budget"], sort=True):
        rows.append({"method": method, "support_budget": int(budget), "receiver_count": len(part), "macro_f1_mean": part.macro_f1.mean(), "macro_f1_std": part.macro_f1.std(ddof=1), "macro_f1_median": part.macro_f1.median(), "ece_mean": part.ece.mean()})
    return pd.DataFrame(rows)


def _safe_correlation(left: np.ndarray, right: np.ndarray) -> float:
    left, right = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    if len(left) < 2 or left.std() == 0 or right.std() == 0:
        return math.nan
    return float(np.corrcoef(left, right)[0, 1])


def receiver_difficulty(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    pivot = frame.pivot(index=["receiver_id", "hardware_family"], columns="model", values="macro_f1").reset_index()
    for method in ("T3A", "P2", "RX_NORM", "SUP_FT_128"):
        pivot[f"{method.lower()}_minus_p0"] = pivot[method] - pivot["P0"]
    correlations = []
    for column in ("t3a_minus_p0", "p2_minus_p0", "rx_norm_minus_p0", "sup_ft_128_minus_p0"):
        correlations.append({"comparison": column, "pearson_with_p0_error": _safe_correlation(1.0 - pivot.P0, pivot[column]), "receiver_count": len(pivot), "diagnostic_only": True})
    return pivot, pd.DataFrame(correlations)


def _calibration_metrics(labels: np.ndarray, probabilities: np.ndarray) -> tuple[float, float]:
    chosen = probabilities[np.arange(len(labels)), labels]
    nll = float(-np.log(np.clip(chosen, 1e-12, 1.0)).mean())
    entropy = float((-(probabilities * np.log(np.clip(probabilities, 1e-12, 1.0))).sum(axis=1)).mean())
    if not np.isfinite((nll, entropy)).all():
        raise FloatingPointError("non-finite calibration diagnostic")
    return nll, entropy


def compute_frozen_calibration(*, converted_root: str | Path, split_root: str | Path, frozen_run_root: str | Path) -> pd.DataFrame:
    original = ManyRxBundle.load(converted_root)
    protocol_cache: dict[str, ManyRxBundle] = {}
    rows: list[dict[str, Any]] = []
    for run_path in sorted(Path(frozen_run_root).glob("*/run.json")):
        record = json.loads(run_path.read_text(encoding="utf-8"))
        method = str(record["model_stage"])
        if method not in CALIBRATION_MODELS:
            continue
        protocol = str(record["protocol_id"])
        if protocol not in protocol_cache:
            protocol_cache[protocol] = remap_bundle_to_split_targets(original, Path(split_root) / protocol / "split_summary.json")
        bundle = protocol_cache[protocol]
        payload = read_blind_predictions(run_path.parent / "predictions_blind.npz")
        indices = np.asarray([bundle.sample_index[str(value)] for value in payload["sample_ids"]], dtype=np.int64)
        nll, entropy = _calibration_metrics(bundle.labels[indices], payload["probabilities"])
        rows.append({"protocol_id": protocol, "receiver_id": str(bundle.receiver_ids[bundle.split_indices(Path(split_root) / protocol / "split_manifest.csv")["test"][0]]), "seed": int(record["config"]["seed"]), "model": method, "nll": nll, "predictive_entropy": entropy, "prediction_sha256": record["target_prediction_sha256"]})
    frame = pd.DataFrame(rows).sort_values(["model", "receiver_id", "seed"])
    if len(frame) != len(CALIBRATION_MODELS) * PRIMARY_RECEIVER_COUNT * len(BENCHMARK_SEEDS):
        raise RuntimeError("frozen calibration grid is incomplete")
    return frame


def summarize_calibration(primary: pd.DataFrame, recomputed: pd.DataFrame, oracle: pd.DataFrame) -> pd.DataFrame:
    ece = primary[primary.model.isin((*CALIBRATION_MODELS, "SUP_FT_128"))].groupby(["model", "receiver_id"], as_index=False).ece.mean().groupby("model").ece.agg(["mean", "std"]).reset_index().rename(columns={"mean": "ece_mean", "std": "ece_std"})
    detail = pd.concat([recomputed, oracle[["receiver_id", "seed", "model", "nll", "predictive_entropy"]]], ignore_index=True)
    detail = detail.groupby(["model", "receiver_id"], as_index=False)[["nll", "predictive_entropy"]].mean().groupby("model")[["nll", "predictive_entropy"]].agg(["mean", "std"])
    detail.columns = ["_".join(value) for value in detail.columns]
    return ece.merge(detail.reset_index(), on="model", how="left", validate="one_to_one")


def summarize_compute(*, frozen_compute_path: str | Path, benchmark_root: str | Path) -> pd.DataFrame:
    frozen = pd.read_csv(frozen_compute_path)
    keep = [column for column in ("model", "run_count", "parameter_count", "wall_seconds_mean", "peak_gpu_memory_bytes_median", "inference_seconds_mean", "support_encoding_flops_approx_mean") if column in frozen]
    frozen = frozen[keep].copy()
    oracle_records = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((Path(benchmark_root) / "runs").glob("*/run.json"))]
    budget_records = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((Path(benchmark_root) / "budget_runs").glob("*/run.json"))]
    oracle = pd.DataFrame([{"model": "SUP_FT_128", "run_count": len(oracle_records), "parameter_count": 64_774, "adapted_parameter_count": np.mean([row["adapted_parameter_count"] for row in oracle_records]), "wall_seconds_mean": np.mean([row["wall_seconds"] for row in oracle_records]), "peak_gpu_memory_bytes_median": np.median([row["peak_gpu_memory_bytes"] for row in oracle_records]), "inference_seconds_mean": math.nan, "support_encoding_flops_approx_mean": math.nan}])
    budget = pd.DataFrame([{"model": "RX_NORM_BUDGET_GRID", "run_count": len(budget_records), "parameter_count": 64_774, "adapted_parameter_count": 0, "wall_seconds_mean": np.mean([row["wall_seconds"] for row in budget_records]), "peak_gpu_memory_bytes_median": np.median([row["peak_gpu_memory_bytes"] for row in budget_records]), "inference_seconds_mean": math.nan, "support_encoding_flops_approx_mean": math.nan}])
    return pd.concat([frozen, oracle, budget], ignore_index=True, sort=False)


def analysis_manifest(root: str | Path, *, exclude: Iterable[str] = ("analysis_manifest.json",)) -> dict[str, Any]:
    root = Path(root)
    excluded = set(exclude)
    rows = []
    for path in sorted(value for value in root.rglob("*") if value.is_file() and value.name not in excluded):
        rows.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"schema_version": 1, "status": "FINAL_IMMUTABLE_ANALYSIS_PACKAGE", "file_count": len(rows), "files": rows, "manifest_sha256": hashlib.sha256(canonical).hexdigest()}
