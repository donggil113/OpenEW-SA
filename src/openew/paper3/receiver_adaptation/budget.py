"""Blinded RX-NORM budget sweep and zero-support T3A mechanism control."""

from __future__ import annotations

import hashlib
import json
import resource
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch

from openew.paper3.wisig.archive import sha256_file
from openew.paper3.wisig.checkpoint import atomic_json
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig.models import IndependentClassifier
from openew.paper3.wisig_v2.blinding import write_blind_predictions
from openew.paper3.wisig_v2.models import NormalizationStatistics, T3AAdapter
from openew.paper3.wisig_v2.runner import RunConfig, _encode_backbone, _independent_probabilities, _stream_statistics, remap_bundle_to_split_targets, set_determinism
from openew.paper3.wisig_v2.support import freeze_support_query

from .contracts import BENCHMARK_SEEDS, SUPPORT_BUDGETS


def budget_run_id(protocol: str, seed: int) -> str:
    return f"{protocol}__adaptation_budgets__s{seed}"


def _base_run_id(protocol: str, method: str, seed: int) -> str:
    return f"{protocol}__{method.lower()}__s{seed}__b128__k32__r100__raw"


def _config_hash(protocol: str, seed: int) -> str:
    payload = json.dumps({"protocol": protocol, "seed": seed, "rx_norm_budgets": SUPPORT_BUDGETS, "t3a_budgets": [0], "common_query_budget": 256}, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _load_model(path: Path, class_count: int, device: torch.device) -> tuple[IndependentClassifier, dict[str, Any]]:
    checkpoint = torch.load(path, map_location=device, weights_only=True)
    model = IndependentClassifier(class_count, wide=False).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model, checkpoint


def run_budget_record(
    converted_root: str | Path,
    split_root: str | Path,
    frozen_run_root: str | Path,
    output_root: str | Path,
    *,
    protocol: str,
    seed: int,
    bundle: ManyRxBundle | None = None,
    resume: bool = True,
) -> dict[str, Any]:
    if seed not in BENCHMARK_SEEDS:
        raise ValueError("seed is not frozen")
    converted_root, split_root, frozen_run_root, output_root = map(Path, (converted_root, split_root, frozen_run_root, output_root))
    output = output_root / "budget_runs" / budget_run_id(protocol, seed)
    record_path = output / "run.json"
    split_path = split_root / protocol / "split_manifest.csv"
    source_norm_checkpoint = frozen_run_root / "runs" / _base_run_id(protocol, "SOURCE_NORM", seed) / "checkpoint.pt"
    p0_checkpoint = frozen_run_root / "runs" / _base_run_id(protocol, "P0", seed) / "checkpoint.pt"
    t3a_record_path = frozen_run_root / "runs" / _base_run_id(protocol, "T3A", seed) / "run.json"
    compatibility = {
        "config_hash": _config_hash(protocol, seed),
        "split_sha256": sha256_file(split_path),
        "source_norm_checkpoint_sha256": sha256_file(source_norm_checkpoint),
        "p0_checkpoint_sha256": sha256_file(p0_checkpoint),
        "frozen_t3a_record_sha256": sha256_file(t3a_record_path),
    }
    if resume and record_path.exists():
        prior = json.loads(record_path.read_text(encoding="utf-8"))
        if prior.get("status") == "COMPLETE" and all(prior.get(key) == value for key, value in compatibility.items()):
            return prior
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    record: dict[str, Any] = {"run_id": budget_run_id(protocol, seed), "status": "RUNNING", "protocol_id": protocol, "seed": seed, "target_metrics": None, **compatibility, "start_time": datetime.now(timezone.utc).isoformat()}
    atomic_json(record, record_path)
    try:
        set_determinism(seed)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        original = bundle or ManyRxBundle.load(converted_root)
        local = remap_bundle_to_split_targets(original, split_root / protocol / "split_summary.json")
        roles = local.split_indices(split_path)
        receiver = str(local.receiver_ids[roles["test"][0]])
        maximum = freeze_support_query(roles["test"], local.sample_ids, local.receiver_ids, receiver_id=receiver, support_budget=256, seed=seed)
        support = np.asarray(maximum.support_indices, dtype=np.int64)
        query = np.asarray(maximum.query_indices, dtype=np.int64)
        source_model, source_checkpoint = _load_model(source_norm_checkpoint, len(local.transmitter_ids), device)
        raw_stats = source_checkpoint.get("source_normalization")
        if not raw_stats:
            raise RuntimeError("SOURCE-NORM checkpoint lacks source statistics")
        source_stats = NormalizationStatistics(**raw_stats).validate()
        prediction_rows: list[dict[str, Any]] = []
        for budget in SUPPORT_BUDGETS:
            statistics = source_stats if budget == 0 else _stream_statistics(local.features, support[:budget])
            probabilities = _independent_probabilities(source_model, local, query, device, 1024, statistics)
            destination = output / f"rx_norm_b{budget:03d}_predictions_blind.npz"
            prediction_rows.append({
                "method": "RX_NORM" if budget else "SOURCE_NORM",
                "support_budget": budget,
                "common_query_budget": 256,
                "support_sample_ids_sha256": hashlib.sha256("\n".join(local.sample_ids[support[:budget]].astype(str)).encode()).hexdigest(),
                "query_count": len(query),
                "prediction_sha256": write_blind_predictions(destination, local.sample_ids[query], probabilities),
                "prediction_path": destination.name,
                "normalization": {"mean_i": statistics.mean_i, "mean_q": statistics.mean_q, "rms": statistics.rms, "sample_count": statistics.sample_count},
            })
        p0_model, _ = _load_model(p0_checkpoint, len(local.transmitter_ids), device)
        frozen_t3a = json.loads(t3a_record_path.read_text(encoding="utf-8"))
        filter_k = frozen_t3a.get("selected_t3a_filter_source_validation_only")
        if filter_k is None:
            raise RuntimeError("frozen T3A record lacks source-validation selection")
        query_embeddings = torch.from_numpy(_encode_backbone(p0_model, local, query, device, 1024)).to(device)
        empty_support = torch.empty((0, p0_model.classifier.in_features), dtype=query_embeddings.dtype, device=device)
        t3a_probabilities = torch.softmax(T3AAdapter(p0_model.classifier, int(filter_k)).predict(query_embeddings, empty_support), dim=-1).cpu().numpy()
        destination = output / "t3a_b000_predictions_blind.npz"
        prediction_rows.append({
            "method": "T3A", "support_budget": 0, "common_query_budget": 256,
            "support_sample_ids_sha256": hashlib.sha256(b"").hexdigest(), "query_count": len(query),
            "prediction_sha256": write_blind_predictions(destination, local.sample_ids[query], t3a_probabilities),
            "prediction_path": destination.name, "filter_k_source_validation_only": int(filter_k),
        })
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        manifest_path = output / "prediction_manifest.json"
        atomic_json({"rows": prediction_rows, "labels_loaded_for_metrics": False, "query_used_for_adaptation": False}, manifest_path)
        record.update({
            "status": "COMPLETE", "end_time": datetime.now(timezone.utc).isoformat(), "wall_seconds": time.perf_counter() - started,
            "device": str(device), "receiver_id": receiver, "support_max": len(support), "query_count": len(query),
            "evaluation_count": len(prediction_rows), "prediction_manifest_sha256": sha256_file(manifest_path),
            "target_labels_used_for_adaptation": False, "target_labels_used_for_metrics": False, "query_used_for_adaptation": False,
            "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else 0,
        })
        atomic_json(record, record_path)
        return record
    except Exception as exc:
        record.update({"status": "FAILED", "failure_reason": f"{type(exc).__name__}: {exc}", "end_time": datetime.now(timezone.utc).isoformat(), "wall_seconds": time.perf_counter() - started})
        atomic_json(record, record_path)
        raise


def budget_plan() -> list[tuple[str, int]]:
    return [(f"receiver_loso_{receiver:02d}", seed) for receiver in range(32) for seed in BENCHMARK_SEEDS]
