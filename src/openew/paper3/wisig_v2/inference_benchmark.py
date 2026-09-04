"""Label-free, standardized test-time latency benchmark for frozen V2 runs."""

from __future__ import annotations

import json
import time
from dataclasses import fields
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
import torch

from openew.paper3.wisig.data import ManyRxBundle

from .analysis import collect_primary_records
from .blinding import read_blind_predictions
from .models import NormalizationStatistics
from .runner import RunConfig, _evaluate_condition_on_role, _load_base_model, _receiver_codes, remap_bundle_to_split_targets, set_determinism
from .suite import PRIMARY_MODELS


BENCHMARK_SEED = 829
BENCHMARK_REPEATS = 3


def select_benchmark_records(records: Sequence[dict[str, Any]], *, seed: int = BENCHMARK_SEED) -> list[dict[str, Any]]:
    selected = [record for record in records if int(record.get("config", {}).get("seed", -1)) == seed]
    expected = 32 * len(PRIMARY_MODELS)
    keys = [(str(record.get("protocol_id")), str(record.get("model_stage"))) for record in selected]
    if len(selected) != expected or len(set(keys)) != expected:
        raise RuntimeError(f"inference benchmark requires {expected} unique receiver/model records, found {len(selected)}")
    if set(model for _, model in keys) != set(PRIMARY_MODELS):
        raise RuntimeError("inference benchmark model set differs from the frozen primary suite")
    if any(record.get("status") != "COMPLETE" for record in selected):
        raise RuntimeError("inference benchmark requires complete records")
    return sorted(selected, key=lambda record: (str(record["protocol_id"]), str(record["model_stage"])))


def _config_from_record(record: dict[str, Any]) -> RunConfig:
    allowed = {field.name for field in fields(RunConfig)}
    values = {key: value for key, value in record["config"].items() if key in allowed}
    return RunConfig(**values).validate()


def benchmark_frozen_inference(
    converted_root: str | Path,
    split_root: str | Path,
    run_root: str | Path,
    destination: str | Path,
    *,
    seed: int = BENCHMARK_SEED,
    repeats: int = BENCHMARK_REPEATS,
) -> pd.DataFrame:
    """Reproduce blind probabilities and time inference without reading targets."""

    if repeats <= 0:
        raise ValueError("benchmark repeats must be positive")
    split_root, run_root, destination = Path(split_root), Path(run_root), Path(destination)
    records = select_benchmark_records(collect_primary_records(run_root), seed=seed)
    set_determinism(seed)
    original = ManyRxBundle.load(converted_root)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows: list[dict[str, Any]] = []
    for record in records:
        config = _config_from_record(record)
        protocol = str(record["protocol_id"])
        bundle = remap_bundle_to_split_targets(original, split_root / protocol / "split_summary.json")
        roles = bundle.split_indices(split_root / protocol / "split_manifest.csv")
        _, _, source_receivers = _receiver_codes(bundle, roles["train"])
        model, _, checkpoint = _load_base_model(config, run_root, len(bundle.transmitter_ids), len(source_receivers), device)
        raw_statistics = checkpoint.get("source_normalization")
        source_statistics = NormalizationStatistics(**raw_statistics).validate() if raw_statistics else None
        filter_k = record.get("selected_t3a_filter_source_validation_only")
        archived = read_blind_predictions(Path(record["record_path"]).parent / "predictions_blind.npz")

        durations: list[float] = []
        reproduced_order: np.ndarray | None = None
        reproduced_probabilities: np.ndarray | None = None
        diagnostics: dict[str, Any] | None = None
        for repeat in range(repeats + 1):
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            started = time.perf_counter()
            order, probabilities, diagnostics = _evaluate_condition_on_role(
                config.model_stage,
                model,
                bundle,
                roles["test"],
                roles["validation"],
                device,
                config,
                source_statistics=source_statistics,
                t3a_filter_k=int(filter_k) if filter_k is not None else None,
            )
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            elapsed = time.perf_counter() - started
            if repeat:
                durations.append(elapsed)
            reproduced_order, reproduced_probabilities = order, probabilities
        assert reproduced_order is not None and reproduced_probabilities is not None and diagnostics is not None
        reproduced_ids = bundle.sample_ids[reproduced_order].astype(str)
        archived_ids = archived["sample_ids"].astype(str)
        if not np.array_equal(reproduced_ids, archived_ids):
            raise RuntimeError(f"benchmark query order differs from blind archive: {record['run_id']}")
        max_probability_error = float(np.max(np.abs(reproduced_probabilities.astype(np.float64) - archived["probabilities"].astype(np.float64))))
        if max_probability_error > 1e-5:
            raise RuntimeError(f"benchmark probabilities differ from blind archive: {record['run_id']} ({max_probability_error})")
        receiver = json.loads((split_root / protocol / "split_summary.json").read_text(encoding="utf-8"))["assignment_metadata"]["test_receiver"]
        rows.append(
            {
                "run_id": str(record["run_id"]),
                "protocol_id": protocol,
                "receiver_id": str(receiver),
                "model": str(config.model_stage),
                "seed": seed,
                "query_count": len(reproduced_ids),
                "repeat_count": repeats,
                "latency_seconds_median": float(np.median(durations)),
                "latency_seconds_min": float(np.min(durations)),
                "latency_seconds_max": float(np.max(durations)),
                "samples_per_second_median": float(len(reproduced_ids) / np.median(durations)),
                "max_probability_reproduction_error": max_probability_error,
                "checkpoint_load_excluded": True,
                "support_and_adaptation_included": True,
                "target_labels_read": False,
                "device": str(device),
            }
        )
    frame = pd.DataFrame(rows).sort_values(["protocol_id", "model"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False, lineterminator="\n")
    frame.groupby("model", as_index=False).agg(
        receiver_count=("receiver_id", "nunique"),
        query_count_median=("query_count", "median"),
        latency_seconds_median=("latency_seconds_median", "median"),
        latency_seconds_mean=("latency_seconds_median", "mean"),
        samples_per_second_median=("samples_per_second_median", "median"),
        max_probability_reproduction_error=("max_probability_reproduction_error", "max"),
    ).to_csv(destination.with_name("standardized_inference_benchmark_summary.csv"), index=False, lineterminator="\n")
    return frame
