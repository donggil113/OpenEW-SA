"""Checkpointed execution engine for the frozen static-relational pilot."""

from __future__ import annotations

import copy
import csv
import json
import math
import os
import random
import resource
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import torch
from torch import nn

from openew.paper3.static_relational.checkpoint import (
    atomic_torch_save,
    atomic_write_json,
    canonical_hash,
    compatible_completed_run,
)
from openew.paper3.static_relational.datasets import (
    FrozenArtifact,
    SplitIndices,
    Standardizer,
    balanced_class_weights,
    build_frozen_split,
    feature_tensor,
    fit_standardizer,
    load_frozen_artifact,
)
from openew.paper3.static_relational.graph import (
    RelationPlan,
    anchor_batches,
    build_context_batch,
    build_relation_plan,
)
from openew.paper3.static_relational.hypergraph import to_torch_context
from openew.paper3.static_relational.integrity import (
    IntegrityViolation,
    source_tree_hash,
    verify_pre_run_snapshot,
)
from openew.paper3.static_relational.metrics import classification_metrics, require_finite_probabilities
from openew.paper3.static_relational.models import build_classifier, parameter_count
from openew.paper3.static_relational.relation_contract import (
    LeakageContractViolation,
    SplitContaminationError,
    STAGE_RELATIONS,
    validate_relation_types,
)


CRITICAL_EXCEPTIONS = (IntegrityViolation, LeakageContractViolation, SplitContaminationError)


@dataclass(frozen=True)
class RunSpec:
    dataset: str
    protocol: str
    model_stage: str
    seed: int
    relation_types: tuple[str, ...]
    relation_retention: float = 1.0
    shuffled_relations: bool = False
    variant: str = "primary"

    @property
    def run_id(self) -> str:
        relations = "none" if not self.relation_types else "-".join(self.relation_types)
        retention = int(round(self.relation_retention * 100))
        shuffle = "shuffled" if self.shuffled_relations else "actual"
        return (
            f"{self.dataset}__{self.protocol}__{self.model_stage}__seed{self.seed}__"
            f"{self.variant}__{shuffle}__ret{retention:03d}__{relations}"
        )

    def scientific_key(self) -> tuple[Any, ...]:
        return (
            self.dataset,
            self.protocol,
            self.model_stage,
            self.seed,
            self.relation_types,
            round(self.relation_retention, 8),
            self.shuffled_relations,
        )


@dataclass
class PreparedProtocol:
    artifact: FrozenArtifact
    split: SplitIndices
    standardizer: Standardizer


def plan_full_suite(config: dict[str, Any], seeds: Iterable[int] | None = None) -> list[RunSpec]:
    selected_seeds = tuple(int(value) for value in (seeds or config["seeds"]))
    candidates: list[RunSpec] = []
    relational_protocols = (
        ("jamshield", "jamshield_scenario"),
        ("jamshield", "jamshield_reactive"),
        ("electrosense", "electrosense_sensor"),
    )
    for dataset, protocol in relational_protocols:
        for seed in selected_seeds:
            for stage in ("m0", "m1", "m2"):
                candidates.append(
                    RunSpec(dataset, protocol, stage, seed, STAGE_RELATIONS[dataset][stage])
                )
    for seed in selected_seeds:
        candidates.append(RunSpec("deepsense", "deepsense_cross_day", "m0", seed, ()))
    for dataset, protocol in relational_protocols:
        for seed in selected_seeds:
            candidates.append(
                RunSpec(
                    dataset,
                    protocol,
                    "m2",
                    seed,
                    STAGE_RELATIONS[dataset]["m2"],
                    shuffled_relations=True,
                    variant="shuffled_control",
                )
            )
            for retention in config["retention_levels"]:
                if float(retention) >= 1.0:
                    continue
                candidates.append(
                    RunSpec(
                        dataset,
                        protocol,
                        "m2",
                        seed,
                        STAGE_RELATIONS[dataset]["m2"],
                        relation_retention=float(retention),
                        variant=f"retention_{int(round(float(retention) * 100))}",
                    )
                )
    for seed in selected_seeds:
        for relation_types, variant in (
            (("receiver",), "receiver_only"),
            (("date",), "date_only"),
            (("receiver_date",), "receiver_date_only"),
        ):
            candidates.append(
                RunSpec(
                    "electrosense",
                    "electrosense_sensor",
                    "m2",
                    seed,
                    relation_types,
                    variant=variant,
                )
            )
    return _deduplicate_specs(candidates)


def plan_smoke_suite(config: dict[str, Any]) -> list[RunSpec]:
    seed = int(config["smoke"]["seed"])
    specs: list[RunSpec] = []
    for dataset, protocol in (
        ("jamshield", "jamshield_scenario"),
        ("electrosense", "electrosense_sensor"),
    ):
        for stage in ("m0", "m1", "m2"):
            specs.append(
                RunSpec(dataset, protocol, stage, seed, STAGE_RELATIONS[dataset][stage], variant="smoke")
            )
    return specs


def _deduplicate_specs(candidates: list[RunSpec]) -> list[RunSpec]:
    unique: dict[tuple[Any, ...], RunSpec] = {}
    for spec in candidates:
        unique.setdefault(spec.scientific_key(), spec)
    return list(unique.values())


def run_suite(
    config: dict[str, Any],
    run_root: str | Path,
    specs: list[RunSpec],
    resume: bool,
    smoke: bool,
    evaluate_heldout: bool,
) -> dict[str, Any]:
    root = Path(run_root)
    for directory in ("configs", "checkpoints", "logs", "predictions", "metrics", "metadata", "analysis"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    if evaluate_heldout:
        _require_committed_freeze()
    pre_snapshot = verify_pre_run_snapshot(config["pre_run_integrity"])
    repo_root = Path(__file__).resolve().parents[4]
    source_hash = source_tree_hash(
        [
            repo_root / "src/openew/paper3/static_relational",
            repo_root / "scripts/paper3/static_relational",
            repo_root / "configs/paper3/static_relational",
            repo_root / "papers/paper3_dynamic_hypergraph_sa/pilot/m0_m2_frozen_pilot_protocol.md",
            repo_root / "papers/paper3_dynamic_hypergraph_sa/pilot/pilot_configuration_freeze.md",
        ],
        repo_root,
    )
    atomic_write_json(root / "configs" / "suite_manifest.json", {
        "planned_run_count": len(specs),
        "specs": [asdict(spec) | {"run_id": spec.run_id} for spec in specs],
        "smoke": smoke,
        "evaluate_heldout": evaluate_heldout,
        "source_hash": source_hash,
        "pre_run_integrity": pre_snapshot,
    })
    prepared_cache: dict[tuple[str, str], PreparedProtocol] = {}
    results: list[dict[str, Any]] = []
    fatal: BaseException | None = None
    for ordinal, spec in enumerate(specs, start=1):
        print(f"[{ordinal}/{len(specs)}] {spec.run_id}", flush=True)
        try:
            key = (spec.dataset, spec.protocol)
            if key not in prepared_cache:
                prepared_cache[key] = prepare_protocol(config, spec.dataset, spec.protocol)
            result = run_one(
                config=config,
                run_root=root,
                spec=spec,
                prepared=prepared_cache[key],
                pre_snapshot=pre_snapshot,
                source_hash=source_hash,
                resume=resume,
                smoke=smoke,
                evaluate_heldout=evaluate_heldout,
            )
        except CRITICAL_EXCEPTIONS as error:
            fatal = error
            result = {"run_id": spec.run_id, "status": "FAILED", "failure_reason": repr(error)}
            results.append(result)
            raise
        except Exception as error:  # keep independent runs alive by contract
            result = _record_failure(root, spec, error)
            print(f"[failed] {spec.run_id}: {error!r}", flush=True)
        results.append(result)
    summary = {
        "planned": len(specs),
        "completed": sum(item.get("status") == "COMPLETED" for item in results),
        "failed": sum(item.get("status") == "FAILED" for item in results),
        "skipped_compatible": sum(item.get("resume_action") == "SKIPPED_COMPATIBLE" for item in results),
        "fatal": repr(fatal) if fatal else "",
    }
    atomic_write_json(root / "metadata" / "suite_summary.json", summary)
    return summary


def prepare_protocol(config: dict[str, Any], dataset: str, protocol_name: str) -> PreparedProtocol:
    protocol = config["protocols"][protocol_name]
    if protocol["dataset"] != dataset:
        raise ValueError(f"Protocol/dataset mismatch: {protocol_name}/{dataset}")
    artifact = load_frozen_artifact(dataset, config["artifacts"][dataset])
    split = build_frozen_split(
        artifact,
        protocol_name,
        protocol,
        float(config["source_validation_fraction"]),
        int(config["split_seed"]),
    )
    standardizer = fit_standardizer(artifact.features, split.train)
    return PreparedProtocol(artifact, split, standardizer)


def run_one(
    config: dict[str, Any],
    run_root: Path,
    spec: RunSpec,
    prepared: PreparedProtocol,
    pre_snapshot: dict[str, Any],
    source_hash: str,
    resume: bool,
    smoke: bool,
    evaluate_heldout: bool,
) -> dict[str, Any]:
    validate_relation_types(spec.dataset, spec.relation_types)
    if spec.model_stage == "m0" and spec.relation_types:
        raise LeakageContractViolation("M0 relation request")
    run_config = _resolved_run_config(config, spec, smoke, evaluate_heldout)
    config_hash = canonical_hash(run_config)
    artifact_key = f"processed_{spec.dataset}"
    artifact_hashes = {artifact_key: pre_snapshot["roots"][artifact_key]}
    signature = {
        "config_hash": config_hash,
        "source_hash": source_hash,
        "artifact_hashes": artifact_hashes,
        "split_hashes": prepared.split.hashes,
    }
    metadata_path = run_root / "metadata" / f"{spec.run_id}.json"
    if resume:
        completed = compatible_completed_run(metadata_path, signature)
        if completed is not None:
            return completed | {"resume_action": "SKIPPED_COMPATIBLE"}
    atomic_write_json(run_root / "configs" / f"{spec.run_id}.json", run_config)
    git_sha = _git_sha()
    start_time = _utc_now()
    start_wall = time.perf_counter()
    seed_everything(spec.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    train_indices, val_indices = _possibly_cap_source_indices(
        prepared, config, spec, smoke
    )
    train_metadata = _relation_metadata(prepared.artifact, train_indices)
    val_metadata = _relation_metadata(prepared.artifact, val_indices)
    relation_start = time.perf_counter()
    train_plan = _make_plan(train_metadata, spec, "train", config)
    val_plan = _make_plan(val_metadata, spec, "source_validation", config)
    relation_overhead = time.perf_counter() - relation_start

    training = config["training"]
    input_dim = int(np.prod(prepared.artifact.features.shape[1:]))
    model = build_classifier(
        dataset=spec.dataset,
        model_stage=spec.model_stage,
        relation_types=spec.relation_types,
        input_dim=input_dim,
        num_classes=len(prepared.artifact.class_names),
        hidden_dim=int(training["hidden_dim"]),
        dropout=float(training["dropout"]),
    ).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(training["learning_rate"]),
        weight_decay=float(training["weight_decay"]),
    )
    class_weight = None
    if training["class_weight"][spec.dataset] == "balanced":
        class_weight = balanced_class_weights(prepared.artifact, train_indices).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weight)
    epochs = int(config["smoke"]["epochs"] if smoke else training["epochs"])
    checkpoint_path = run_root / "checkpoints" / f"{spec.run_id}.pt"
    start_epoch = 0
    epoch_losses: list[float] = []
    best_epoch = -1
    best_validation = -math.inf
    best_state: dict[str, torch.Tensor] | None = None
    if resume and checkpoint_path.exists():
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
        if checkpoint.get("signature") == signature:
            model.load_state_dict(checkpoint["model_state_dict"])
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            start_epoch = int(checkpoint["epoch"]) + 1
            epoch_losses = list(checkpoint["epoch_losses"])
            best_epoch = int(checkpoint["best_epoch"])
            best_validation = float(checkpoint["best_validation"])
            best_state = checkpoint["best_state"]
            _restore_rng_state(checkpoint["rng_state"])

    running_metadata = {
        "run_id": spec.run_id,
        "dataset": spec.dataset,
        "protocol": spec.protocol,
        "model_stage": spec.model_stage,
        "seed": spec.seed,
        "variant": spec.variant,
        "relation_types": list(spec.relation_types),
        "relation_retention": spec.relation_retention,
        "shuffled_relations": spec.shuffled_relations,
        "context_size": int(config["max_context_size"]),
        "git_sha": git_sha,
        **signature,
        "start_time": start_time,
        "end_time": None,
        "device": str(device),
        "parameter_count": parameter_count(model),
        "status": "RUNNING",
        "failure_reason": "",
    }
    atomic_write_json(metadata_path, running_metadata)

    train_targets = prepared.artifact.label_indices(train_indices)
    val_targets = prepared.artifact.label_indices(val_indices)
    batch_size = int(training["batch_size"][spec.dataset])
    for epoch in range(start_epoch, epochs):
        model.train()
        total_loss = 0.0
        total_nodes = 0
        batches = anchor_batches(train_plan, len(train_indices), batch_size, spec.seed, epoch, True)
        for anchors in batches:
            logits, context_seconds = _forward_anchor_batch(
                model,
                prepared,
                train_indices,
                train_plan,
                anchors,
                device,
            )
            relation_overhead += context_seconds
            labels = torch.as_tensor(train_targets[anchors], dtype=torch.long, device=device)
            loss = criterion(logits, labels)
            if not torch.isfinite(loss):
                raise ValueError("Non-finite training loss")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach().cpu()) * len(anchors)
            total_nodes += len(anchors)
        epoch_loss = total_loss / max(total_nodes, 1)
        epoch_losses.append(epoch_loss)
        validation_probabilities, validation_context_time = predict_probabilities(
            model,
            prepared,
            val_indices,
            val_plan,
            batch_size,
            spec.seed,
            device,
        )
        relation_overhead += validation_context_time
        validation_metrics = classification_metrics(
            val_targets,
            validation_probabilities,
            prepared.artifact.metadata.iloc[val_indices]["domain_id"].astype(str).to_numpy(),
            prepared.artifact.class_names,
            int(training["ece_bins"]),
        )
        if validation_metrics["macro_f1"] > best_validation:
            best_validation = float(validation_metrics["macro_f1"])
            best_epoch = epoch
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        atomic_torch_save(
            checkpoint_path,
            {
                "signature": signature,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "epoch": epoch,
                "epoch_losses": epoch_losses,
                "best_epoch": best_epoch,
                "best_validation": best_validation,
                "best_state": best_state,
                "rng_state": _capture_rng_state(),
            },
        )
    if best_state is None:
        raise RuntimeError("Training completed without a source-validation checkpoint")
    model.load_state_dict(best_state)
    model.to(device)
    if smoke and min(epoch_losses[1:], default=epoch_losses[0]) >= epoch_losses[0]:
        raise RuntimeError(f"Smoke loss did not decrease: {epoch_losses}")

    source_probabilities, source_context_time = predict_probabilities(
        model, prepared, val_indices, val_plan, batch_size, spec.seed, device
    )
    relation_overhead += source_context_time
    source_metrics = classification_metrics(
        val_targets,
        source_probabilities,
        prepared.artifact.metadata.iloc[val_indices]["domain_id"].astype(str).to_numpy(),
        prepared.artifact.class_names,
        int(training["ece_bins"]),
    )
    _write_prediction_csv(
        run_root / "predictions" / f"{spec.run_id}__source_validation.csv",
        prepared.artifact,
        val_indices,
        source_probabilities,
        val_targets,
    )
    training_wall = time.perf_counter() - start_wall

    heldout_metrics: dict[str, Any] | None = None
    heldout_plan_stats: dict[str, Any] | None = None
    inference_wall = 0.0
    if evaluate_heldout:
        heldout_metadata = _relation_metadata(prepared.artifact, prepared.split.heldout)
        relation_start = time.perf_counter()
        heldout_plan = _make_plan(heldout_metadata, spec, "heldout", config)
        relation_overhead += time.perf_counter() - relation_start
        inference_start = time.perf_counter()
        heldout_probabilities, heldout_context_time = predict_probabilities(
            model,
            prepared,
            prepared.split.heldout,
            heldout_plan,
            batch_size,
            spec.seed,
            device,
        )
        inference_wall = time.perf_counter() - inference_start
        relation_overhead += heldout_context_time
        require_finite_probabilities(heldout_probabilities)
        frozen_path = run_root / "predictions" / f"{spec.run_id}__heldout_frozen.npz"
        _atomic_save_npz(
            frozen_path,
            sample_id=prepared.artifact.metadata.iloc[prepared.split.heldout]["sample_id"].astype(str).to_numpy(),
            domain_id=prepared.artifact.metadata.iloc[prepared.split.heldout]["domain_id"].astype(str).to_numpy(),
            probabilities=heldout_probabilities,
        )
        prediction_freeze_time = _utc_now()
        # Scientific firewall: held-out targets are read only after the target
        # probabilities and IDs above are atomically frozen.
        heldout_targets = prepared.artifact.label_indices(prepared.split.heldout)
        heldout_metrics = classification_metrics(
            heldout_targets,
            heldout_probabilities,
            prepared.artifact.metadata.iloc[prepared.split.heldout]["domain_id"].astype(str).to_numpy(),
            prepared.artifact.class_names,
            int(training["ece_bins"]),
        )
        heldout_metrics["prediction_freeze_time"] = prediction_freeze_time
        _write_prediction_csv(
            run_root / "predictions" / f"{spec.run_id}__heldout.csv",
            prepared.artifact,
            prepared.split.heldout,
            heldout_probabilities,
            heldout_targets,
        )
        heldout_plan_stats = heldout_plan.statistics if heldout_plan else _empty_relation_stats(
            spec.dataset, "heldout", len(prepared.split.heldout), int(config["max_context_size"])
        )

    end_wall = time.perf_counter()
    gpu_peak = int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else 0
    cpu_peak_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    train_count = len(train_indices) * max(0, epochs - start_epoch)
    result = running_metadata | {
        "end_time": _utc_now(),
        "status": "COMPLETED",
        "train_metrics": {
            "epoch_losses": epoch_losses,
            "best_epoch": best_epoch,
            "best_source_validation_macro_f1": best_validation,
            "n_train_samples": len(train_indices),
        },
        "source_validation_metrics": source_metrics,
        "heldout_metrics": heldout_metrics,
        "relation_coverage": {
            "train": train_plan.statistics if train_plan else _empty_relation_stats(
                spec.dataset, "train", len(train_indices), int(config["max_context_size"])
            ),
            "source_validation": val_plan.statistics if val_plan else _empty_relation_stats(
                spec.dataset, "source_validation", len(val_indices), int(config["max_context_size"])
            ),
            "heldout": heldout_plan_stats,
        },
        "hyperedge_group_statistics": {
            "train": train_plan.statistics if train_plan else None,
            "source_validation": val_plan.statistics if val_plan else None,
            "heldout": heldout_plan_stats,
        },
        "split_sizes": {
            "train": len(train_indices),
            "source_validation": len(val_indices),
            "heldout": len(prepared.split.heldout),
        },
        "wall_time_seconds": end_wall - start_wall,
        "training_wall_time_seconds": training_wall,
        "inference_wall_time_seconds": inference_wall,
        "peak_gpu_memory_bytes": gpu_peak,
        "peak_cpu_rss_kib": cpu_peak_kib,
        "training_samples_per_second": train_count / max(training_wall, 1e-12),
        "inference_samples_per_second": (
            len(prepared.split.heldout) / inference_wall if inference_wall > 0 else None
        ),
        "context_construction_overhead_seconds": relation_overhead,
        "smoke": smoke,
        "heldout_evaluated": evaluate_heldout,
    }
    atomic_write_json(run_root / "metrics" / f"{spec.run_id}.json", {
        "source_validation": source_metrics,
        "heldout": heldout_metrics,
    })
    atomic_write_json(metadata_path, result)
    return result


def _possibly_cap_source_indices(
    prepared: PreparedProtocol,
    config: dict[str, Any],
    spec: RunSpec,
    smoke: bool,
) -> tuple[np.ndarray, np.ndarray]:
    if not smoke:
        return prepared.split.train, prepared.split.source_validation
    return (
        _stable_cap(prepared.artifact, prepared.split.train, int(config["smoke"]["max_train_samples"]), spec),
        _stable_cap(
            prepared.artifact,
            prepared.split.source_validation,
            int(config["smoke"]["max_validation_samples"]),
            spec,
        ),
    )


def _stable_cap(
    artifact: FrozenArtifact, indices: np.ndarray, limit: int, spec: RunSpec
) -> np.ndarray:
    if len(indices) <= limit:
        return indices.copy()
    sample_ids = artifact.metadata.iloc[indices]["sample_id"].astype(str).to_numpy()
    order = sorted(
        range(len(indices)),
        key=lambda position: canonical_hash(
            [artifact.dataset, spec.protocol, "smoke_cap", sample_ids[position]]
        ),
    )
    return np.sort(indices[np.asarray(order[:limit], dtype=np.int64)])


def _relation_metadata(artifact: FrozenArtifact, indices: np.ndarray) -> pd.DataFrame:
    allowed = ["sample_id"]
    for field in ("rx_id", "source_date_id"):
        if field in artifact.metadata:
            allowed.append(field)
    # Passing only whitelisted physical fields makes target leakage structurally
    # impossible even before the explicit validator executes.
    return artifact.metadata.iloc[indices][allowed].reset_index(drop=True).copy()


def _make_plan(
    metadata: pd.DataFrame,
    spec: RunSpec,
    partition: str,
    config: dict[str, Any],
) -> RelationPlan | None:
    if spec.model_stage == "m0":
        return None
    return build_relation_plan(
        metadata=metadata,
        dataset=spec.dataset,
        partition=partition,
        relation_types=spec.relation_types,
        seed=spec.seed,
        max_context_size=int(config["max_context_size"]),
        retention=spec.relation_retention,
        shuffled=spec.shuffled_relations,
    )


def _forward_anchor_batch(
    model: nn.Module,
    prepared: PreparedProtocol,
    partition_indices: np.ndarray,
    plan: RelationPlan | None,
    anchors: np.ndarray,
    device: torch.device,
) -> tuple[torch.Tensor, float]:
    if plan is None:
        features = feature_tensor(
            prepared.artifact, partition_indices[anchors], prepared.standardizer, device
        )
        return model(features), 0.0
    started = time.perf_counter()
    context = build_context_batch(plan, anchors)
    context_seconds = time.perf_counter() - started
    features = feature_tensor(
        prepared.artifact,
        partition_indices[context.support_positions],
        prepared.standardizer,
        device,
    )
    return model(features, to_torch_context(context, device)), context_seconds


def predict_probabilities(
    model: nn.Module,
    prepared: PreparedProtocol,
    partition_indices: np.ndarray,
    plan: RelationPlan | None,
    batch_size: int,
    seed: int,
    device: torch.device,
) -> tuple[np.ndarray, float]:
    model.eval()
    output = np.empty((len(partition_indices), len(prepared.artifact.class_names)), dtype=np.float32)
    context_seconds = 0.0
    with torch.no_grad():
        for anchors in anchor_batches(plan, len(partition_indices), batch_size, seed, 0, False):
            logits, elapsed = _forward_anchor_batch(
                model, prepared, partition_indices, plan, anchors, device
            )
            context_seconds += elapsed
            output[anchors] = torch.softmax(logits, dim=1).detach().cpu().numpy()
    require_finite_probabilities(output)
    return output, context_seconds


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True


def _capture_rng_state() -> dict[str, Any]:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
    }


def _restore_rng_state(state: dict[str, Any]) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch"])
    if torch.cuda.is_available() and state.get("cuda"):
        torch.cuda.set_rng_state_all(state["cuda"])


def _resolved_run_config(
    config: dict[str, Any], spec: RunSpec, smoke: bool, evaluate_heldout: bool
) -> dict[str, Any]:
    return {
        "schema_version": config["schema_version"],
        "experiment_name": config["experiment_name"],
        "run_spec": asdict(spec),
        "protocol": copy.deepcopy(config["protocols"][spec.protocol]),
        "artifact_dir": config["artifacts"][spec.dataset],
        "relation_whitelist": copy.deepcopy(config["relation_whitelist"]),
        "split_seed": config["split_seed"],
        "source_validation_fraction": config["source_validation_fraction"],
        "max_context_size": config["max_context_size"],
        "training": copy.deepcopy(config["training"]),
        "smoke": smoke,
        "smoke_config": copy.deepcopy(config["smoke"]) if smoke else None,
        "evaluate_heldout": evaluate_heldout,
    }


def _write_prediction_csv(
    path: Path,
    artifact: FrozenArtifact,
    indices: np.ndarray,
    probabilities: np.ndarray,
    targets: np.ndarray,
) -> None:
    predicted = probabilities.argmax(axis=1)
    metadata = artifact.metadata.iloc[indices]
    data: dict[str, Any] = {
        "sample_id": metadata["sample_id"].astype(str).to_numpy(),
        "domain_id": metadata["domain_id"].astype(str).to_numpy(),
        "true_label_index": targets,
        "true_label": [artifact.class_names[int(value)] for value in targets],
        "predicted_label_index": predicted,
        "predicted_label": [artifact.class_names[int(value)] for value in predicted],
    }
    for index, class_name in enumerate(artifact.class_names):
        suffix = "".join(character if character.isalnum() else "_" for character in class_name)
        data[f"probability_{suffix}"] = probabilities[:, index]
    _atomic_write_dataframe(path, pd.DataFrame(data))


def _atomic_write_dataframe(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False, quoting=csv.QUOTE_MINIMAL)
    os.replace(temporary, path)


def _atomic_save_npz(path: Path, **arrays: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    os.replace(temporary, path)


def _record_failure(run_root: Path, spec: RunSpec, error: Exception) -> dict[str, Any]:
    path = run_root / "metadata" / f"{spec.run_id}.json"
    existing: dict[str, Any] = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    result = existing | {
        "run_id": spec.run_id,
        "dataset": spec.dataset,
        "protocol": spec.protocol,
        "model_stage": spec.model_stage,
        "seed": spec.seed,
        "relation_types": list(spec.relation_types),
        "relation_retention": spec.relation_retention,
        "status": "FAILED",
        "end_time": _utc_now(),
        "failure_reason": repr(error),
    }
    atomic_write_json(path, result)
    return result


def _empty_relation_stats(
    dataset: str, partition: str, node_count: int, max_context_size: int
) -> dict[str, Any]:
    return {
        "dataset": dataset,
        "partition": partition,
        "node_count": node_count,
        "relation_types": [],
        "relation_coverage": 0.0,
        "isolated_node_count": node_count,
        "isolated_node_fraction": 1.0,
        "max_context_size": max_context_size,
        "per_relation_type": {},
    }


def _require_committed_freeze() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    required = (
        "papers/paper3_dynamic_hypergraph_sa/pilot/m0_m2_frozen_pilot_protocol.md",
        "papers/paper3_dynamic_hypergraph_sa/pilot/pilot_configuration_freeze.md",
        "configs/paper3/static_relational/pilot.yaml",
    )
    for relative in required:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", relative],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise IntegrityViolation(f"Held-out evaluation requires committed freeze file: {relative}")
    status = subprocess.check_output(
        [
            "git",
            "status",
            "--porcelain",
            "--",
            "src/openew/paper3/static_relational",
            "scripts/paper3/static_relational",
            "configs/paper3/static_relational",
            "papers/paper3_dynamic_hypergraph_sa/pilot/m0_m2_frozen_pilot_protocol.md",
            "papers/paper3_dynamic_hypergraph_sa/pilot/pilot_configuration_freeze.md",
        ],
        cwd=repo_root,
        text=True,
    )
    if status.strip():
        raise IntegrityViolation(
            "Held-out evaluation requires a clean committed protocol/config/source freeze"
        )


def _git_sha() -> str:
    repo_root = Path(__file__).resolve().parents[4]
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
