"""One-time receiver-level analysis for new blinded benchmark records."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from openew.paper3.wisig.archive import sha256_file
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig.metrics import classification_metrics
from openew.paper3.wisig_v2.blinding import read_blind_predictions
from openew.paper3.wisig_v2.runner import remap_bundle_to_split_targets
from openew.paper3.wisig_v2.statistics import descriptive_summary, holm_adjust, receiver_bootstrap, receiver_sign_flip

from .contracts import BOOTSTRAP_REPLICATES, CATASTROPHIC_MACRO_F1_DROP, INFERENCE_RNG_SEED, SIGN_FLIP_PERMUTATIONS
from .oracle import oracle_run_id
from .budget import budget_plan, budget_run_id


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _extended_metrics(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    metrics = {key: float(value) for key, value in classification_metrics(labels, probabilities).items()}
    chosen = probabilities[np.arange(len(labels)), labels]
    metrics["nll"] = float(-np.log(np.clip(chosen, 1e-12, 1.0)).mean())
    metrics["predictive_entropy"] = float((-(probabilities * np.log(np.clip(probabilities, 1e-12, 1.0))).sum(axis=1)).mean())
    if not np.isfinite(list(metrics.values())).all():
        raise FloatingPointError("analysis metric is non-finite")
    return metrics


def _labels_for_prediction(bundle: ManyRxBundle, payload: dict[str, np.ndarray]) -> np.ndarray:
    try:
        indices = np.asarray([bundle.sample_index[str(value)] for value in payload["sample_ids"]], dtype=np.int64)
    except KeyError as exc:
        raise ValueError("blind prediction contains unknown sample ID") from exc
    return bundle.labels[indices]


def _protocol_bundle(original: ManyRxBundle, split_root: Path, protocol: str) -> ManyRxBundle:
    return remap_bundle_to_split_targets(original, split_root / protocol / "split_summary.json")


def _complete_oracle_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for receiver in range(32):
        protocol = f"receiver_loso_{receiver:02d}"
        for seed in (829, 1829, 2829, 3829, 4829):
            path = root / "runs" / oracle_run_id(protocol, seed) / "run.json"
            if not path.exists():
                raise FileNotFoundError(f"missing oracle record: {path}")
            row = json.loads(path.read_text(encoding="utf-8"))
            prediction = path.parent / "predictions_blind.npz"
            if row.get("status") != "COMPLETE" or row.get("target_metrics") is not None:
                raise RuntimeError(f"oracle record incomplete/unblinded: {path}")
            if sha256_file(prediction) != row.get("prediction_sha256"):
                raise RuntimeError(f"oracle prediction hash mismatch: {prediction}")
            row["record_path"] = str(path)
            row["prediction_path"] = str(prediction)
            records.append(row)
    return records


def _complete_budget_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for protocol, seed in budget_plan():
        path = root / "budget_runs" / budget_run_id(protocol, seed) / "run.json"
        if not path.exists():
            raise FileNotFoundError(f"missing budget record: {path}")
        row = json.loads(path.read_text(encoding="utf-8"))
        manifest_path = path.parent / "prediction_manifest.json"
        if row.get("status") != "COMPLETE" or row.get("evaluation_count") != 7:
            raise RuntimeError(f"budget record incomplete: {path}")
        if sha256_file(manifest_path) != row.get("prediction_manifest_sha256"):
            raise RuntimeError(f"budget manifest hash mismatch: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("labels_loaded_for_metrics") is not False:
            raise RuntimeError("budget predictions were not blind")
        for prediction in manifest["rows"]:
            file_path = path.parent / prediction["prediction_path"]
            if sha256_file(file_path) != prediction["prediction_sha256"]:
                raise RuntimeError(f"budget prediction hash mismatch: {file_path}")
        row["record_path"] = str(path)
        row["manifest_path"] = str(manifest_path)
        records.append(row)
    return records


def _manifest_hash(rows: Iterable[dict[str, str]]) -> str:
    payload = json.dumps(sorted(rows, key=lambda row: tuple(sorted(row.items()))), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def unblind_benchmark(
    *,
    converted_root: str | Path,
    split_root: str | Path,
    frozen_analysis_root: str | Path,
    addendum_root: str | Path,
    benchmark_root: str | Path,
    preregistration_path: str | Path,
    expected_git_sha: str,
) -> dict[str, Any]:
    converted_root, split_root, frozen_analysis_root, addendum_root, benchmark_root = map(Path, (converted_root, split_root, frozen_analysis_root, addendum_root, benchmark_root))
    analysis_root = benchmark_root / "analysis"
    unblind_path = analysis_root / "unblinding_manifest.json"
    if unblind_path.exists():
        raise FileExistsError("benchmark has already been unblinded")
    oracle_records = _complete_oracle_records(benchmark_root)
    budget_records = _complete_budget_records(benchmark_root)
    prediction_rows: list[dict[str, str]] = []
    for row in oracle_records:
        prediction_rows.append({"run_id": row["run_id"], "sha256": row["prediction_sha256"]})
    for row in budget_records:
        manifest = json.loads(Path(row["manifest_path"]).read_text(encoding="utf-8"))
        prediction_rows.extend({"run_id": f"{row['run_id']}::{entry['method']}::{entry['support_budget']}", "sha256": entry["prediction_sha256"]} for entry in manifest["rows"])
    unblind = {
        "status": "UNBLINDED_ONCE",
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "expected_git_sha": expected_git_sha,
        "preregistration_sha256": sha256_file(preregistration_path),
        "oracle_records": len(oracle_records),
        "budget_records": len(budget_records),
        "adaptation_evaluations": len(oracle_records) + sum(row["evaluation_count"] for row in budget_records),
        "prediction_manifest_sha256": _manifest_hash(prediction_rows),
    }
    analysis_root.mkdir(parents=True, exist_ok=True)
    _atomic_json(unblind_path, unblind)
    original = ManyRxBundle.load(converted_root)
    oracle_rows: list[dict[str, Any]] = []
    for row in oracle_records:
        protocol = str(row["protocol_id"])
        bundle = _protocol_bundle(original, split_root, protocol)
        payload = read_blind_predictions(row["prediction_path"])
        metrics = _extended_metrics(_labels_for_prediction(bundle, payload), payload["probabilities"])
        oracle_rows.append({"protocol_id": protocol, "receiver_id": str(bundle.receiver_ids[bundle.split_indices(split_root / protocol / "split_manifest.csv")["test"][0]]), "seed": int(row["seed"]), "model": "SUP_FT_128", "query_count": len(payload["sample_ids"]), **metrics, "adaptation_seconds": float(row["wall_seconds"]), "adapted_parameter_count": int(row["adapted_parameter_count"]), "learning_rate": row["selected_source_validation_only"]["learning_rate"], "steps": row["selected_source_validation_only"]["steps"], "prediction_sha256": row["prediction_sha256"]})
    oracle_frame = pd.DataFrame(oracle_rows).sort_values(["receiver_id", "seed"])
    oracle_frame.to_csv(analysis_root / "supervised_oracle_receiver_seed_results.csv", index=False, lineterminator="\n")
    budget_rows: list[dict[str, Any]] = []
    for row in budget_records:
        protocol = str(row["protocol_id"])
        bundle = _protocol_bundle(original, split_root, protocol)
        manifest = json.loads(Path(row["manifest_path"]).read_text(encoding="utf-8"))
        for entry in manifest["rows"]:
            payload = read_blind_predictions(Path(row["manifest_path"]).parent / entry["prediction_path"])
            budget_rows.append({"protocol_id": protocol, "receiver_id": row["receiver_id"], "seed": int(row["seed"]), "method": entry["method"], "support_budget": int(entry["support_budget"]), "common_query_budget": 256, "query_count": len(payload["sample_ids"]), **_extended_metrics(_labels_for_prediction(bundle, payload), payload["probabilities"]), "prediction_sha256": entry["prediction_sha256"]})
    budget_frame = pd.DataFrame(budget_rows).sort_values(["method", "support_budget", "receiver_id", "seed"])
    budget_frame.to_csv(analysis_root / "new_support_budget_receiver_seed_results.csv", index=False, lineterminator="\n")
    frozen = pd.read_csv(frozen_analysis_root / "primary_receiver_seed_results.csv", dtype={"receiver_id": "string"})
    hardware = frozen[["receiver_id", "hardware_family"]].drop_duplicates()
    oracle_primary = oracle_frame.merge(hardware, on="receiver_id", how="left", validate="many_to_one")
    combined = pd.concat([frozen, oracle_primary], ignore_index=True, sort=False)
    combined.to_csv(analysis_root / "benchmark_receiver_seed_results.csv", index=False, lineterminator="\n")
    metric_columns = ["macro_f1", "accuracy", "balanced_accuracy", "ece"]
    averaged = combined.groupby(["model", "receiver_id", "hardware_family"], as_index=False)[metric_columns].mean()
    averaged.to_csv(analysis_root / "benchmark_receiver_averaged_results.csv", index=False, lineterminator="\n")
    summary_rows: list[dict[str, Any]] = []
    for method, part in averaged.groupby("model", sort=True):
        for metric in metric_columns:
            summary_rows.append({"model": method, "metric": metric, **descriptive_summary(part[metric].to_numpy())})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(analysis_root / "benchmark_summary.csv", index=False, lineterminator="\n")
    pivot = averaged.pivot(index="receiver_id", columns="model", values="macro_f1")
    delta = (pivot["T3A"] - pivot["P0"]).to_numpy(dtype=float)
    sign = receiver_sign_flip(delta, permutations=SIGN_FLIP_PERMUTATIONS, seed=INFERENCE_RNG_SEED)
    inference = {
        "comparison_family": ["T3A_MINUS_P0"],
        "T3A_MINUS_P0": {
            "receiver_delta_summary": descriptive_summary(delta),
            "positive_receivers": int((delta > 0).sum()),
            "negative_receivers": int((delta < 0).sum()),
            "bootstrap": receiver_bootstrap(delta, replicates=BOOTSTRAP_REPLICATES, seed=INFERENCE_RNG_SEED),
            "sign_flip": sign,
            "standardized_mean_difference": float(delta.mean() / delta.std(ddof=1)),
        },
        "holm_adjusted": holm_adjust({"T3A_MINUS_P0": float(sign["p_value"])}),
    }
    _atomic_json(analysis_root / "receiver_level_inference.json", inference)
    catastrophic_rows: list[dict[str, Any]] = []
    seed_pivot = combined.pivot_table(index=["receiver_id", "seed"], columns="model", values="macro_f1")
    for method in sorted(set(seed_pivot) - {"P0"}):
        valid = seed_pivot[["P0", method]].dropna()
        losses = valid[method] - valid["P0"]
        for (receiver, seed), value in losses.items():
            catastrophic_rows.append({"model": method, "receiver_id": receiver, "seed": seed, "delta_from_p0": value, "catastrophic": value < -CATASTROPHIC_MACRO_F1_DROP})
    pd.DataFrame(catastrophic_rows).to_csv(analysis_root / "catastrophic_adaptation.csv", index=False, lineterminator="\n")
    existing_budget = pd.read_csv(addendum_root / "analysis_support_budget.csv")
    all_budget = pd.concat([existing_budget, budget_frame], ignore_index=True, sort=False)
    all_budget.to_csv(analysis_root / "support_budget_all_methods.csv", index=False, lineterminator="\n")
    return {"unblinding": unblind, "inference": inference, "oracle_mean": float(averaged.loc[averaged.model == "SUP_FT_128", "macro_f1"].mean()), "summary_rows": len(summary), "budget_rows": len(all_budget)}
