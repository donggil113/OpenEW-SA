"""Transparent operation-count and measured-resource summaries for V2."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from openew.paper3.wisig.data import ManyRxBundle

from .analysis import collect_primary_records
from .support import build_query_context_indices, freeze_support_query


SAMPLE_BYTES = 256 * 2 * 4
TRAINED_STAGES = frozenset({"P0", "P0_WIDE", "DG_CORAL", "DG_GROUPDRO", "DG_DANN", "SOURCE_NORM", "P1", "P2"})


def conv1d_flops(length: int, in_channels: int, out_channels: int, kernel: int) -> int:
    """Multiply-plus-add count (two FLOPs), excluding norm/activation."""

    if min(length, in_channels, out_channels, kernel) <= 0:
        raise ValueError("convolution dimensions must be positive")
    return 2 * length * in_channels * out_channels * kernel


def backbone_forward_flops() -> int:
    return sum(
        (
            conv1d_flops(128, 2, 16, 7),
            conv1d_flops(64, 16, 32, 5),
            conv1d_flops(64, 32, 32, 3),
            conv1d_flops(64, 16, 32, 1),
            conv1d_flops(32, 32, 64, 5),
            conv1d_flops(32, 64, 64, 3),
            conv1d_flops(32, 32, 64, 1),
            conv1d_flops(32, 64, 64, 5),
            conv1d_flops(32, 64, 64, 3),
        )
    )


def forward_flops(stage: str, *, class_count: int = 6, context_k: int = 32, source_domain_count: int = 28) -> int:
    base = backbone_forward_flops()
    linear = lambda left, right: 2 * left * right
    if stage == "P0_WIDE":
        return base + linear(64, 147) + linear(147, class_count)
    if stage == "DG_DANN":
        return base + linear(64, class_count) + linear(64, 64) + linear(64, source_domain_count)
    if stage in {"P0", "DG_CORAL", "DG_GROUPDRO", "SOURCE_NORM", "RX_NORM", "T3A"}:
        return base + linear(64, class_count)
    if stage in {"P1", "P2", "P2_SHUFFLED", "P2_NULL", "P2_MISMATCHED_RX"}:
        scorer = context_k * (linear(64, 32) + linear(32, 1)) if stage not in {"P1", "P2_NULL"} else 0
        weighted_sum = 2 * context_k * 64 if stage != "P2_NULL" else 0
        return base + scorer + weighted_sum + linear(128, 64) + linear(64, class_count)
    raise ValueError(f"unknown stage {stage}")


def benchmark_context_assembly(
    converted_root: str | Path,
    split_root: str | Path,
    destination: str | Path,
    *,
    repeats: int = 5,
) -> pd.DataFrame:
    """Time label-free support freezing and query-to-support index assembly."""

    if repeats <= 0:
        raise ValueError("repeats must be positive")
    bundle = ManyRxBundle.load(converted_root)
    split_root = Path(split_root)
    rows: list[dict[str, Any]] = []
    for protocol_path in sorted(split_root.glob("receiver_loso_*")):
        role = bundle.split_indices(protocol_path / "split_manifest.csv")["test"]
        receiver = str(bundle.receiver_ids[role[0]])
        for seed in (829, 1829, 2829, 3829, 4829):
            elapsed: list[float] = []
            for _ in range(repeats):
                start = time.perf_counter()
                frozen = freeze_support_query(role, bundle.sample_ids, bundle.receiver_ids, receiver_id=receiver, support_budget=128, seed=seed)
                matrix = build_query_context_indices(frozen.query_indices, frozen.support_indices, bundle.sample_ids, receiver, k=32, seed=seed)
                elapsed.append(time.perf_counter() - start)
            rows.append(
                {
                    "protocol_id": protocol_path.name,
                    "receiver_id": receiver,
                    "seed": seed,
                    "support_count": len(frozen.support_indices),
                    "query_count": len(frozen.query_indices),
                    "context_index_entries": int(matrix.size),
                    "assembly_seconds_median": float(np.median(elapsed)),
                    "assembly_seconds_min": float(np.min(elapsed)),
                    "repeats": repeats,
                    "labels_accessed": False,
                }
            )
    frame = pd.DataFrame(rows).sort_values(["protocol_id", "seed"])
    destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False, lineterminator="\n")
    return frame


def generate_compute_audit(
    run_root: str | Path,
    split_root: str | Path,
    destination: str | Path,
    *,
    converted_root: str | Path | None = None,
) -> pd.DataFrame:
    records = collect_primary_records(run_root)
    rows: list[dict[str, Any]] = []
    split_root = Path(split_root)
    for record in records:
        stage = str(record["model_stage"])
        split = pd.read_csv(split_root / record["protocol_id"] / "split_manifest.csv", usecols=["split"])
        train_count = int((split["split"] == "train").sum())
        diagnostics = next(iter(record["target_receiver_diagnostics"].values()))
        context_k = int(record["config"]["context_k"])
        estimate = forward_flops(stage, context_k=context_k)
        trained = stage in TRAINED_STAGES
        epochs = int(record["epochs_completed"]) if trained else 0
        training_flops = int(3 * estimate * train_count * epochs) if trained else 0
        if "inference_seconds" in diagnostics:
            inference_seconds = float(diagnostics["inference_seconds"])
            timing_source = "instrumented_context_inference"
        elif not trained:
            inference_seconds = float(record["wall_seconds"])
            timing_source = "derived_condition_total_wall_proxy"
        else:
            inference_seconds = np.nan
            timing_source = "not_separately_instrumented"
        target_support_used = 128 if stage in {"P1", "P2", "RX_NORM", "T3A"} else 0
        donor_support_used = 128 if stage in {"P2_SHUFFLED", "P2_MISMATCHED_RX"} else 0
        query_count = int(record["target_prediction_count"])
        support_backbone_packets = (
            target_support_used + donor_support_used
            if stage in {"P1", "P2", "P2_SHUFFLED", "P2_MISMATCHED_RX", "T3A"}
            else 0
        )
        support_encoding_flops = support_backbone_packets * backbone_forward_flops()
        # RX-NORM makes two streaming passes over 128 x 256 x I/Q values.
        # Four scalar operations per value is an explicit approximation for
        # accumulation followed by subtract/square/accumulate.
        support_statistics_ops = target_support_used * 256 * 2 * 4 if stage == "RX_NORM" else 0
        total_test_flops = query_count * estimate + support_encoding_flops + support_statistics_ops
        rows.append(
            {
                "run_id": record["run_id"],
                "model": stage,
                "seed": int(record["config"]["seed"]),
                "protocol_id": record["protocol_id"],
                "parameter_count": record["parameter_count"],
                "epochs_completed": epochs,
                "train_count": train_count,
                "measured_total_wall_seconds": record["wall_seconds"],
                "measured_peak_cpu_rss_kib": record["peak_cpu_rss_kib"],
                "measured_peak_gpu_memory_bytes": record["peak_gpu_memory_bytes"],
                "measured_or_proxy_inference_seconds": inference_seconds,
                "inference_timing_source": timing_source,
                "query_count": query_count,
                "target_receiver_support_packets_used": target_support_used,
                "source_validation_donor_packets_used": donor_support_used,
                "forward_flops_per_query_approx": estimate,
                "support_encoding_flops_approx": support_encoding_flops,
                "support_statistics_ops_approx": support_statistics_ops,
                "total_test_flops_approx": total_test_flops,
                "source_training_flops_approx": training_flops,
                "target_query_payload_bytes": query_count * SAMPLE_BYTES,
                "support_payload_bytes": (target_support_used + donor_support_used) * SAMPLE_BYTES,
                "flop_scope_note": "conv/linear/einsum multiply-adds plus explicitly separated RX-NORM support-statistics operations; query normalization, activation, optimizer, CORAL, prototype updates, and transfer overhead excluded; backward approximated as 2x forward",
            }
        )
    frame = pd.DataFrame(rows).sort_values(["model", "protocol_id", "seed"])
    destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False, lineterminator="\n")
    frame.groupby("model", as_index=False).agg(
        run_count=("run_id", "count"),
        parameter_count=("parameter_count", "median"),
        wall_seconds_mean=("measured_total_wall_seconds", "mean"),
        wall_seconds_std=("measured_total_wall_seconds", "std"),
        peak_cpu_rss_kib_median=("measured_peak_cpu_rss_kib", "median"),
        peak_gpu_memory_bytes_median=("measured_peak_gpu_memory_bytes", "median"),
        inference_seconds_mean=("measured_or_proxy_inference_seconds", "mean"),
        source_training_flops_approx_mean=("source_training_flops_approx", "mean"),
        support_encoding_flops_approx_mean=("support_encoding_flops_approx", "mean"),
        support_statistics_ops_approx_mean=("support_statistics_ops_approx", "mean"),
        total_test_flops_approx_mean=("total_test_flops_approx", "mean"),
        forward_flops_per_query_approx=("forward_flops_per_query_approx", "median"),
    ).to_csv(destination.with_name("compute_budget_summary.csv"), index=False, lineterminator="\n")
    if converted_root is not None:
        benchmark_context_assembly(converted_root, split_root, destination.with_name("context_assembly_benchmark.csv"))
    return frame
