"""Checkpointed source-selected WiSig static receiver-context experiment runner."""

from __future__ import annotations

import csv
import hashlib
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
from typing import Any, Iterator, Sequence

import numpy as np
import torch
import torch.nn.functional as F

from .archive import sha256_file
from .checkpoint import atomic_json, atomic_torch_save, compatible_completion
from .context import ContextEpisodes, build_context_episodes, episode_statistics, pad_episode_batch
from .data import ManyRxBundle, deterministic_batches, normalize_packet_batch
from .losses import GroupDROState, source_coral_loss
from .metrics import classification_metrics, per_group_macro_f1
from .models import IndependentClassifier, ReceiverContextClassifier, capacity_match_report, trainable_parameter_count
from .provenance import canonical_json_bytes


MODEL_STAGES = (
    "P0",
    "P0_WIDE",
    "DG_CORAL",
    "DG_GROUPDRO",
    "P1",
    "P2",
    "P2_SHUFFLED",
    "P2_NULL",
)
SEEDS = (829, 1829, 2829, 3829, 4829)


@dataclass(frozen=True)
class RunConfig:
    protocol_id: str
    model_stage: str
    seed: int
    context_size: int = 32
    relation_retention: float = 1.0
    max_epochs: int = 20
    patience: int = 8
    learning_rate: float = 5e-4
    weight_decay: float = 1e-4
    sample_batch_size: int = 1024
    episode_node_budget: int = 1024
    coral_weight: float = 0.1
    groupdro_eta: float = 0.01
    evaluate_target: bool = False
    smoke: bool = False

    def validate(self) -> "RunConfig":
        if self.model_stage not in MODEL_STAGES:
            raise ValueError(f"unknown model stage {self.model_stage}")
        if self.seed not in SEEDS:
            raise ValueError(f"seed must be one of {SEEDS}")
        if self.context_size not in (8, 32, 128):
            raise ValueError("context_size must be one of 8, 32, 128")
        if self.relation_retention not in (0.0, 0.25, 0.5, 0.75, 1.0):
            raise ValueError("relation_retention is not prespecified")
        if self.max_epochs <= 0 or self.max_epochs > 50 or self.patience <= 0:
            raise ValueError("invalid training budget")
        if self.model_stage == "P2_NULL" and self.relation_retention != 0.0:
            raise ValueError("P2_NULL requires zero relation retention")
        return self

    @property
    def config_hash(self) -> str:
        return hashlib.sha256(canonical_json_bytes(asdict(self))).hexdigest()


def set_determinism(seed: int) -> dict[str, int]:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True, warn_only=True)
    return {"python_seed": seed, "numpy_seed": seed, "torch_seed": seed, "cuda_seed": seed}


def git_sha(repository: str | Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()


def _make_model(stage: str, class_count: int) -> torch.nn.Module:
    if stage == "P0_WIDE":
        return IndependentClassifier(class_count, wide=True)
    if stage in {"P0", "DG_CORAL", "DG_GROUPDRO"}:
        return IndependentClassifier(class_count, wide=False)
    return ReceiverContextClassifier(class_count, attention=stage in {"P2", "P2_SHUFFLED", "P2_NULL"})


def _to_tensor(features: np.ndarray, device: torch.device) -> torch.Tensor:
    return torch.from_numpy(normalize_packet_batch(features)).to(device=device, dtype=torch.float32, non_blocking=True)


def _independent_epoch(
    model: IndependentClassifier,
    bundle: ManyRxBundle,
    indices: np.ndarray,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    config: RunConfig,
    epoch: int,
    domain_codes_by_global: np.ndarray,
    groupdro: GroupDROState | None,
) -> dict[str, float]:
    model.train()
    total_loss = 0.0
    total = 0
    for batch in deterministic_batches(indices, config.sample_batch_size, config.seed + epoch * 100003, shuffle=True):
        x = _to_tensor(bundle.features[batch], device)
        y = torch.from_numpy(bundle.labels[batch]).to(device)
        optimizer.zero_grad(set_to_none=True)
        embeddings = model.backbone(x)
        logits = model.classifier(embeddings)
        per_sample = F.cross_entropy(logits, y, reduction="none")
        if config.model_stage == "DG_CORAL":
            domains = torch.from_numpy(domain_codes_by_global[batch]).to(device)
            loss = per_sample.mean() + config.coral_weight * source_coral_loss(embeddings, domains)
        elif config.model_stage == "DG_GROUPDRO":
            assert groupdro is not None
            domains = torch.from_numpy(domain_codes_by_global[batch]).to(device)
            loss = groupdro.objective(per_sample, domains)
        else:
            loss = per_sample.mean()
        if not torch.isfinite(loss):
            raise FloatingPointError("non-finite training loss")
        loss.backward()
        optimizer.step()
        total_loss += float(loss.detach()) * len(batch)
        total += len(batch)
    return {"loss": total_loss / total, "sample_count": float(total)}


def _episode_batches(episodes: ContextEpisodes, node_budget: int, seed: int, shuffle: bool) -> Iterator[list[tuple[int, ...]]]:
    values = list(episodes.episodes)
    if shuffle:
        rng = random.Random(seed)
        rng.shuffle(values)
    batch: list[tuple[int, ...]] = []
    nodes = 0
    for episode in values:
        if batch and nodes + len(episode) > node_budget:
            yield batch
            batch, nodes = [], 0
        batch.append(episode)
        nodes += len(episode)
    if batch:
        yield batch


def _context_epoch(
    model: ReceiverContextClassifier,
    bundle: ManyRxBundle,
    episodes: ContextEpisodes,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    config: RunConfig,
    epoch: int,
) -> dict[str, float]:
    model.train()
    total_loss = 0.0
    total = 0
    for batch_episodes in _episode_batches(episodes, config.episode_node_budget, config.seed + epoch * 100003, True):
        indices, valid, retained = pad_episode_batch(
            batch_episodes,
            sample_ids=bundle.sample_ids,
            retention=config.relation_retention,
            seed=config.seed,
        )
        x = _to_tensor(bundle.features[indices], device)
        valid_tensor = torch.from_numpy(valid).to(device)
        retained_tensor = torch.from_numpy(retained).to(device)
        labels = torch.from_numpy(bundle.labels[indices]).to(device)
        optimizer.zero_grad(set_to_none=True)
        output = model(x, valid_tensor, retained_tensor)
        loss = F.cross_entropy(output.logits[valid_tensor], labels[valid_tensor])
        if not torch.isfinite(loss):
            raise FloatingPointError("non-finite context training loss")
        loss.backward()
        optimizer.step()
        count = int(valid.sum())
        total_loss += float(loss.detach()) * count
        total += count
    return {"loss": total_loss / total, "sample_count": float(total)}


@torch.no_grad()
def _evaluate_independent(
    model: IndependentClassifier,
    bundle: ManyRxBundle,
    indices: np.ndarray,
    device: torch.device,
    batch_size: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    model.eval()
    probabilities: list[np.ndarray] = []
    ordered: list[np.ndarray] = []
    started = time.perf_counter()
    for batch in deterministic_batches(indices, batch_size, 0, shuffle=False):
        logits = model(_to_tensor(bundle.features[batch], device))
        probabilities.append(torch.softmax(logits, dim=-1).cpu().numpy())
        ordered.append(batch)
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    elapsed = time.perf_counter() - started
    return np.concatenate(ordered), np.concatenate(probabilities), {"inference_seconds": elapsed, "samples_per_second": len(indices) / elapsed}


@torch.no_grad()
def _evaluate_context(
    model: ReceiverContextClassifier,
    bundle: ManyRxBundle,
    episodes: ContextEpisodes,
    device: torch.device,
    config: RunConfig,
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    model.eval()
    probabilities: list[np.ndarray] = []
    ordered: list[np.ndarray] = []
    entropies: list[float] = []
    effective: list[float] = []
    started = time.perf_counter()
    for batch_episodes in _episode_batches(episodes, config.episode_node_budget, 0, False):
        indices, valid, retained = pad_episode_batch(batch_episodes, sample_ids=bundle.sample_ids, retention=config.relation_retention, seed=config.seed)
        valid_tensor = torch.from_numpy(valid).to(device)
        output = model(
            _to_tensor(bundle.features[indices], device),
            valid_tensor,
            torch.from_numpy(retained).to(device),
        )
        probabilities.append(torch.softmax(output.logits[valid_tensor], dim=-1).cpu().numpy())
        ordered.append(indices[valid])
        if output.attention_weights is not None:
            weights = output.attention_weights.cpu().numpy()
            for row in weights:
                positive = row[row > 0]
                entropy = -float(np.sum(positive * np.log(positive))) if len(positive) else 0.0
                entropies.append(entropy)
                effective.append(float(np.exp(entropy)) if len(positive) else 0.0)
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    elapsed = time.perf_counter() - started
    count = sum(len(value) for value in ordered)
    diagnostics = {
        "inference_seconds": elapsed,
        "samples_per_second": count / elapsed,
        "attention_entropy_mean": float(np.mean(entropies)) if entropies else 0.0,
        "effective_peer_count_mean": float(np.mean(effective)) if effective else 0.0,
    }
    return np.concatenate(ordered), np.concatenate(probabilities), diagnostics


def _prediction_record(bundle: ManyRxBundle, indices: np.ndarray, probabilities: np.ndarray) -> list[dict[str, Any]]:
    predictions = probabilities.argmax(axis=1)
    return [
        {
            "sample_id": str(bundle.sample_ids[index]),
            "true_transmitter_index": int(bundle.labels[index]),
            "predicted_transmitter_index": int(prediction),
            "receiver_id": str(bundle.receiver_ids[index]),
            "day_id": str(bundle.day_ids[index]),
            **{f"p_{class_index}": float(probability) for class_index, probability in enumerate(row)},
        }
        for index, prediction, row in zip(indices, predictions, probabilities)
    ]


def _write_predictions(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    os.replace(temporary, path)


def run_experiment(
    repository: str | Path,
    converted_root: str | Path,
    split_root: str | Path,
    run_root: str | Path,
    config: RunConfig,
    *,
    bundle: ManyRxBundle | None = None,
    resume: bool = True,
) -> dict[str, Any]:
    config = config.validate()
    repository, split_root, run_root = Path(repository), Path(split_root), Path(run_root)
    split_directory = split_root / config.protocol_id
    split_manifest = split_directory / "split_manifest.csv"
    split_sha = sha256_file(split_manifest)
    sha = git_sha(repository)
    bundle = bundle or ManyRxBundle.load(converted_root)
    run_id = f"{config.protocol_id}__{config.model_stage.lower()}__s{config.seed}__c{config.context_size}__r{int(config.relation_retention*100):03d}"
    output = run_root / "runs" / run_id
    record_path = output / "run.json"
    compatibility = {
        "config_hash": config.config_hash,
        "git_sha": sha,
        "split_sha256": split_sha,
        "data_manifest_sha256": bundle.manifest_sha256,
    }
    if resume and (complete := compatible_completion(record_path, compatibility)) is not None:
        return complete
    output.mkdir(parents=True, exist_ok=True)
    started_utc = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    seed_record = set_determinism(config.seed)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    record: dict[str, Any] = {
        "run_id": run_id,
        "status": "RUNNING",
        "failure_reason": None,
        "protocol_id": config.protocol_id,
        "model_stage": config.model_stage,
        "seed": config.seed,
        "relation_types": ["receiver_id"] if config.model_stage in {"P1", "P2", "P2_SHUFFLED", "P2_NULL"} else [],
        "relation_retention": config.relation_retention,
        "context_size": config.context_size,
        "config": asdict(config),
        "config_hash": config.config_hash,
        "git_sha": sha,
        "split_sha256": split_sha,
        "data_manifest_sha256": bundle.manifest_sha256,
        "start_time": started_utc,
        "device": str(device),
        "seeds": seed_record,
    }
    atomic_json(record, record_path)
    try:
        split_indices = bundle.split_indices(split_manifest)
        train_indices = split_indices["train"]
        if config.smoke:
            # Stable source-only subset; never selected from held-out behavior.
            train_indices = np.asarray(sorted(train_indices, key=lambda index: hashlib.sha256(f"smoke:{bundle.sample_ids[index]}".encode()).digest())[: min(16384, len(train_indices))])
        model = _make_model(config.model_stage, len(bundle.transmitter_ids)).to(device)
        if not capacity_match_report(len(bundle.transmitter_ids))["within_five_percent"]:
            raise RuntimeError("P0-WIDE capacity match is outside the frozen five-percent tolerance")
        optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
        domain_codes_by_global = np.full(len(bundle.features), -1, dtype=np.int64)
        train_codes, receiver_values = bundle.receiver_codes(train_indices)
        domain_codes_by_global[train_indices] = train_codes
        groupdro = GroupDROState(len(receiver_values), config.groupdro_eta, device) if config.model_stage == "DG_GROUPDRO" else None
        context_stage = config.model_stage in {"P1", "P2", "P2_SHUFFLED", "P2_NULL"}
        shuffled = config.model_stage == "P2_SHUFFLED"
        episodes: dict[str, ContextEpisodes] = {}
        if context_stage:
            for role, indices in split_indices.items():
                if role == "test" and not config.evaluate_target:
                    continue
                role_indices = train_indices if role == "train" else indices
                episodes[role] = build_context_episodes(
                    role_indices,
                    bundle.receiver_ids,
                    bundle.sample_ids,
                    context_size=config.context_size,
                    seed=config.seed,
                    partition=role,
                    shuffled=shuffled,
                )
        best_score = -math.inf
        best_epoch = 0
        stale = 0
        history: list[dict[str, Any]] = []
        checkpoint = output / "checkpoint.pt"
        for epoch in range(config.max_epochs):
            epoch_started = time.perf_counter()
            if context_stage:
                train_metrics = _context_epoch(model, bundle, episodes["train"], optimizer, device, config, epoch)  # type: ignore[arg-type]
                val_order, val_prob, val_compute = _evaluate_context(model, bundle, episodes["validation"], device, config)  # type: ignore[arg-type]
            else:
                train_metrics = _independent_epoch(model, bundle, train_indices, optimizer, device, config, epoch, domain_codes_by_global, groupdro)  # type: ignore[arg-type]
                val_order, val_prob, val_compute = _evaluate_independent(model, bundle, split_indices["validation"], device, config.sample_batch_size)  # type: ignore[arg-type]
            val_metrics = classification_metrics(bundle.labels[val_order], val_prob)
            row = {"epoch": epoch + 1, "train": train_metrics, "source_validation": val_metrics, "epoch_seconds": time.perf_counter() - epoch_started}
            history.append(row)
            if val_metrics["macro_f1"] > best_score + 1e-8:
                best_score = val_metrics["macro_f1"]
                best_epoch = epoch + 1
                stale = 0
                atomic_torch_save(
                    {
                        "model_state": model.state_dict(),
                        "optimizer_state": optimizer.state_dict(),
                        "epoch": best_epoch,
                        "source_validation_macro_f1": best_score,
                        "config_hash": config.config_hash,
                    },
                    checkpoint,
                )
            else:
                stale += 1
            atomic_json({"history": history, "best_epoch": best_epoch, "best_source_validation_macro_f1": best_score}, output / "history.json")
            if stale >= config.patience:
                break
        saved = torch.load(checkpoint, map_location=device, weights_only=True)
        model.load_state_dict(saved["model_state"])
        if context_stage:
            val_order, val_prob, val_compute = _evaluate_context(model, bundle, episodes["validation"], device, config)  # type: ignore[arg-type]
        else:
            val_order, val_prob, val_compute = _evaluate_independent(model, bundle, split_indices["validation"], device, config.sample_batch_size)  # type: ignore[arg-type]
        source_validation = classification_metrics(bundle.labels[val_order], val_prob)
        source_validation["per_receiver_macro_f1"] = per_group_macro_f1(bundle.labels[val_order], val_prob, bundle.receiver_ids[val_order])  # type: ignore[assignment]
        source_validation["per_day_macro_f1"] = per_group_macro_f1(bundle.labels[val_order], val_prob, bundle.day_ids[val_order])  # type: ignore[assignment]
        held_out: dict[str, Any] | None = None
        prediction_hash = None
        if config.evaluate_target:
            if context_stage:
                target_order, target_prob, target_compute = _evaluate_context(model, bundle, episodes["test"], device, config)  # type: ignore[arg-type]
            else:
                target_order, target_prob, target_compute = _evaluate_independent(model, bundle, split_indices["test"], device, config.sample_batch_size)  # type: ignore[arg-type]
            held_out = classification_metrics(bundle.labels[target_order], target_prob)
            held_out["per_receiver_macro_f1"] = per_group_macro_f1(bundle.labels[target_order], target_prob, bundle.receiver_ids[target_order])
            held_out["per_day_macro_f1"] = per_group_macro_f1(bundle.labels[target_order], target_prob, bundle.day_ids[target_order])
            held_out["compute"] = target_compute
            predictions_path = output / "predictions.csv"
            _write_predictions(predictions_path, _prediction_record(bundle, target_order, target_prob))
            prediction_hash = sha256_file(predictions_path)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        record.update(
            {
                "status": "COMPLETE",
                "end_time": datetime.now(timezone.utc).isoformat(),
                "wall_seconds": time.perf_counter() - started,
                "parameter_count": trainable_parameter_count(model),
                "capacity_match": capacity_match_report(len(bundle.transmitter_ids)),
                "epochs_completed": len(history),
                "best_epoch": best_epoch,
                "train_metrics": history[-1]["train"],
                "source_validation_metrics": source_validation,
                "source_validation_compute": val_compute,
                "held_out_metrics": held_out,
                "prediction_sha256": prediction_hash,
                "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else 0,
                "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                "relation_statistics": {role: episode_statistics(value) for role, value in episodes.items()},
            }
        )
        atomic_json(record, record_path)
        return record
    except Exception as exc:
        record.update(
            {
                "status": "FAILED",
                "failure_reason": f"{type(exc).__name__}: {exc}",
                "end_time": datetime.now(timezone.utc).isoformat(),
                "wall_seconds": time.perf_counter() - started,
            }
        )
        atomic_json(record, record_path)
        raise
