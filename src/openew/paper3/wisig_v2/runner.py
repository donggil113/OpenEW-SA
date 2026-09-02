"""Checkpointed, target-blinded WiSig V2 training and receiver-support inference."""

from __future__ import annotations

import hashlib
import math
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

from openew.paper3.wisig.archive import sha256_file
from openew.paper3.wisig.checkpoint import atomic_json, atomic_torch_save, compatible_completion
from openew.paper3.wisig.context import ContextEpisodes, build_context_episodes, pad_episode_batch
from openew.paper3.wisig.data import ManyRxBundle, deterministic_batches, normalize_packet_batch
from openew.paper3.wisig.losses import GroupDROState, source_coral_loss
from openew.paper3.wisig.metrics import classification_metrics, per_group_macro_f1

from .blinding import write_blind_predictions
from .contracts import PRIMARY_CONTEXT_K, PRIMARY_SEEDS, PRIMARY_SUPPORT_BUDGET, method_registry
from .controls import choose_mismatched_receiver, day_matched_support, shuffled_receiver_support
from .hashing import canonical_json_bytes, stable_digest
from .models import (
    DANNClassifier,
    IndependentClassifier,
    NormalizationStatistics,
    ReceiverSupportClassifier,
    T3AAdapter,
    apply_iq_normalization,
    make_model,
    trainable_parameter_count,
)
from .support import SupportQuerySplit, build_query_context_indices, freeze_all_test_receivers, freeze_support_query, support_query_statistics


TRAINED_STAGES = frozenset({"P0", "P0_WIDE", "DG_CORAL", "DG_GROUPDRO", "DG_DANN", "SOURCE_NORM", "P1", "P2"})
DERIVED_STAGES = frozenset({"P2_SHUFFLED", "P2_NULL", "P2_MISMATCHED_RX", "RX_NORM", "T3A"})
T3A_FILTER_CANDIDATES = (1, 5, 20, 50, 100, -1)


@dataclass(frozen=True)
class RunConfig:
    protocol_id: str
    model_stage: str
    seed: int
    support_budget: int = PRIMARY_SUPPORT_BUDGET
    context_k: int = PRIMARY_CONTEXT_K
    context_retention: float = 1.0
    max_epochs: int = 30
    patience: int = 8
    learning_rate: float = 5e-4
    weight_decay: float = 1e-4
    sample_batch_size: int = 1024
    episode_node_budget: int = 1056
    coral_weight: float = 0.1
    groupdro_eta: float = 0.01
    dann_reversal: float = 0.1
    blind_target_metrics: bool = True
    evaluate_target_predictions: bool = True
    smoke: bool = False
    data_variant: str = "raw"

    def validate(self) -> "RunConfig":
        registry = method_registry()
        if self.model_stage not in registry or registry[self.model_stage].status != "IMPLEMENTED":
            raise ValueError(f"model stage is not executable: {self.model_stage}")
        if self.seed not in PRIMARY_SEEDS:
            raise ValueError(f"seed must be one of {PRIMARY_SEEDS}")
        if self.support_budget not in (16, 32, 64, 128, 256):
            raise ValueError("support budget is not preregistered")
        if self.context_k not in (8, 16, 32, 64):
            raise ValueError("context k is not preregistered")
        if self.context_k > self.support_budget and self.model_stage in {"P1", "P2", *DERIVED_STAGES}:
            raise ValueError("context k cannot exceed support budget")
        if self.context_retention not in (0.0, 0.25, 0.5, 0.75, 1.0):
            raise ValueError("context retention is not preregistered")
        if self.max_epochs <= 0 or self.max_epochs > 50 or self.patience <= 0:
            raise ValueError("invalid training budget")
        if self.evaluate_target_predictions and not self.blind_target_metrics:
            raise ValueError("full-suite target predictions must remain blinded")
        if self.data_variant not in {"raw", "official_equalized"}:
            raise ValueError("unknown WiSig data variant")
        return self

    @property
    def config_hash(self) -> str:
        return hashlib.sha256(canonical_json_bytes(asdict(self))).hexdigest()


def set_determinism(seed: int) -> dict[str, int]:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True, warn_only=True)
    return {"python_seed": seed, "numpy_seed": seed, "torch_seed": seed, "cuda_seed": seed}


def git_sha(repository: str | Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()


def _to_tensor(features: np.ndarray, device: torch.device, statistics: NormalizationStatistics | None = None) -> torch.Tensor:
    values = apply_iq_normalization(features, statistics) if statistics is not None else normalize_packet_batch(features)
    return torch.from_numpy(np.asarray(values, dtype=np.float32)).to(device=device, non_blocking=True)


def _stream_statistics(features: np.ndarray, indices: np.ndarray, batch_size: int = 4096) -> NormalizationStatistics:
    total = 0
    sum_channels = np.zeros(2, dtype=np.float64)
    sum_squares = 0.0
    for batch in deterministic_batches(indices, batch_size, 0, shuffle=False):
        values = np.asarray(features[batch], dtype=np.float64)
        sum_channels += values.sum(axis=(0, 1))
        total += values.shape[0] * values.shape[1]
    means = sum_channels / total
    for batch in deterministic_batches(indices, batch_size, 0, shuffle=False):
        values = np.asarray(features[batch], dtype=np.float64)
        sum_squares += float(np.square(values - means.reshape(1, 1, 2)).sum())
    rms = math.sqrt(sum_squares / (total * 2))
    return NormalizationStatistics(float(means[0]), float(means[1]), float(rms), len(indices)).validate()


def _receiver_codes(bundle: ManyRxBundle, indices: np.ndarray) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    codes, values = bundle.receiver_codes(indices)
    global_codes = np.full(len(bundle.features), -1, dtype=np.int64)
    global_codes[indices] = codes
    return codes, global_codes, values


def _independent_epoch(
    model: torch.nn.Module,
    bundle: ManyRxBundle,
    indices: np.ndarray,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    config: RunConfig,
    epoch: int,
    domain_codes: np.ndarray,
    groupdro: GroupDROState | None,
    statistics: NormalizationStatistics | None,
) -> dict[str, float]:
    model.train()
    total_loss = 0.0
    total = 0
    for batch in deterministic_batches(indices, config.sample_batch_size, config.seed + epoch * 100003, shuffle=True):
        x = _to_tensor(bundle.features[batch], device, statistics)
        y = torch.from_numpy(bundle.labels[batch]).to(device)
        domains = torch.from_numpy(domain_codes[batch]).to(device)
        optimizer.zero_grad(set_to_none=True)
        if config.model_stage == "DG_DANN":
            assert isinstance(model, DANNClassifier)
            logits, domain_logits = model(x, reversal=config.dann_reversal)
            loss = F.cross_entropy(logits, y) + F.cross_entropy(domain_logits, domains)
        else:
            assert isinstance(model, IndependentClassifier)
            embeddings = model.backbone(x)
            logits = model.classifier(embeddings)
            per_sample = F.cross_entropy(logits, y, reduction="none")
            if config.model_stage == "DG_CORAL":
                loss = per_sample.mean() + config.coral_weight * source_coral_loss(embeddings, domains)
            elif config.model_stage == "DG_GROUPDRO":
                assert groupdro is not None
                loss = groupdro.objective(per_sample, domains)
            else:
                loss = per_sample.mean()
        if not torch.isfinite(loss):
            raise FloatingPointError("non-finite training loss")
        loss.backward(); optimizer.step()
        total_loss += float(loss.detach()) * len(batch); total += len(batch)
    return {"loss": total_loss / max(total, 1), "sample_count": float(total)}


def _episode_batches(episodes: ContextEpisodes, node_budget: int, seed: int, shuffle: bool) -> Iterator[list[tuple[int, ...]]]:
    values = list(episodes.episodes)
    if shuffle:
        random.Random(seed).shuffle(values)
    batch: list[tuple[int, ...]] = []
    nodes = 0
    for episode in values:
        if batch and nodes + len(episode) > node_budget:
            yield batch; batch = []; nodes = 0
        batch.append(episode); nodes += len(episode)
    if batch:
        yield batch


def _context_epoch(
    model: ReceiverSupportClassifier,
    bundle: ManyRxBundle,
    episodes: ContextEpisodes,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    config: RunConfig,
    epoch: int,
) -> dict[str, float]:
    model.train(); total_loss = 0.0; total = 0
    for episode_batch in _episode_batches(episodes, config.episode_node_budget, config.seed + epoch * 100003, True):
        indices, valid, _ = pad_episode_batch(episode_batch, sample_ids=bundle.sample_ids, retention=1.0, seed=config.seed)
        valid_tensor = torch.from_numpy(valid).to(device)
        labels = torch.from_numpy(bundle.labels[indices]).to(device)
        optimizer.zero_grad(set_to_none=True)
        output = model.forward_source_episodes(_to_tensor(bundle.features[indices], device), valid_tensor)
        loss = F.cross_entropy(output.logits[valid_tensor], labels[valid_tensor])
        if not torch.isfinite(loss):
            raise FloatingPointError("non-finite context training loss")
        loss.backward(); optimizer.step()
        count = int(valid.sum()); total_loss += float(loss.detach()) * count; total += count
    return {"loss": total_loss / max(total, 1), "sample_count": float(total)}


@torch.no_grad()
def _encode_backbone(
    model: IndependentClassifier | ReceiverSupportClassifier | DANNClassifier,
    bundle: ManyRxBundle,
    indices: Sequence[int] | np.ndarray,
    device: torch.device,
    batch_size: int,
    statistics: NormalizationStatistics | None = None,
) -> np.ndarray:
    model.eval(); rows: list[np.ndarray] = []
    values = np.asarray(indices, dtype=np.int64)
    for batch in deterministic_batches(values, batch_size, 0, shuffle=False):
        rows.append(model.backbone(_to_tensor(bundle.features[batch], device, statistics)).cpu().numpy())
    return np.concatenate(rows, axis=0) if rows else np.empty((0, 64), dtype=np.float32)


@torch.no_grad()
def _independent_probabilities(
    model: IndependentClassifier | DANNClassifier,
    bundle: ManyRxBundle,
    indices: Sequence[int] | np.ndarray,
    device: torch.device,
    batch_size: int,
    statistics: NormalizationStatistics | None = None,
) -> np.ndarray:
    model.eval(); rows: list[np.ndarray] = []
    values = np.asarray(indices, dtype=np.int64)
    for batch in deterministic_batches(values, batch_size, 0, shuffle=False):
        x = _to_tensor(bundle.features[batch], device, statistics)
        logits = model(x, reversal=0.0)[0] if isinstance(model, DANNClassifier) else model(x)
        rows.append(torch.softmax(logits, dim=-1).cpu().numpy())
    result = np.concatenate(rows, axis=0)
    if not np.isfinite(result).all():
        raise FloatingPointError("non-finite independent probabilities")
    return result


def _control_support(
    condition: str,
    bundle: ManyRxBundle,
    role_indices: np.ndarray,
    donor_indices: np.ndarray,
    split: SupportQuerySplit,
    *,
    budget: int,
    seed: int,
) -> tuple[int, ...]:
    if condition in {"P1", "P2"}:
        return split.support_indices
    if condition == "P2_NULL":
        return ()
    query_days = [str(bundle.day_ids[index]) for index in split.query_indices]
    donor_receivers = sorted({str(bundle.receiver_ids[index]) for index in donor_indices})
    if condition == "P2_MISMATCHED_RX":
        receiver = choose_mismatched_receiver(split.receiver_id, donor_receivers, seed=seed)
        candidates = [int(index) for index in donor_indices if str(bundle.receiver_ids[int(index)]) == receiver]
        return day_matched_support(candidates, query_days, bundle.sample_ids, bundle.day_ids, budget=budget, seed=seed, namespace="wisig-v2-mismatched")
    if condition == "P2_SHUFFLED":
        return shuffled_receiver_support(donor_indices, bundle.receiver_ids, bundle.sample_ids, bundle.day_ids, query_days, excluded_receiver=split.receiver_id, budget=budget, seed=seed)
    raise ValueError(f"unsupported context condition {condition}")


@torch.no_grad()
def _context_probabilities(
    model: ReceiverSupportClassifier,
    bundle: ManyRxBundle,
    split: SupportQuerySplit,
    support_indices: Sequence[int],
    device: torch.device,
    config: RunConfig,
) -> tuple[np.ndarray, dict[str, float | int]]:
    model.eval()
    query = np.asarray(split.query_indices, dtype=np.int64)
    support = np.asarray(support_indices, dtype=np.int64)
    if len(support):
        support_embeddings_np = _encode_backbone(model, bundle, support, device, config.sample_batch_size)
        support_position = {int(index): position for position, index in enumerate(support)}
    else:
        support_embeddings_np = np.zeros((1, 64), dtype=np.float32)
        support_position = {}
    probabilities: list[np.ndarray] = []
    entropies: list[float] = []
    effective: list[float] = []
    start = time.perf_counter()
    for query_batch in deterministic_batches(query, config.sample_batch_size, 0, shuffle=False):
        anchors = torch.from_numpy(_encode_backbone(model, bundle, query_batch, device, config.sample_batch_size)).to(device)
        if len(support):
            peer_global = build_query_context_indices(query_batch, support, bundle.sample_ids, split.receiver_id, k=config.context_k, seed=config.seed, retention=config.context_retention)
            positions = np.zeros(peer_global.shape, dtype=np.int64)
            mask = peer_global >= 0
            for row, column in zip(*np.nonzero(mask)):
                positions[row, column] = support_position[int(peer_global[row, column])]
            peer_embeddings = torch.from_numpy(support_embeddings_np[positions]).to(device)
            peer_mask = torch.from_numpy(mask).to(device)
        else:
            peer_embeddings = torch.zeros((len(query_batch), config.context_k, 64), dtype=anchors.dtype, device=device)
            peer_mask = torch.zeros((len(query_batch), config.context_k), dtype=torch.bool, device=device)
        output = model.predict_from_embeddings(anchors, peer_embeddings, peer_mask)
        probabilities.append(torch.softmax(output.logits, dim=-1).cpu().numpy())
        if output.attention is not None:
            weights = output.attention.detach().cpu().numpy()
            for row in weights:
                positive = row[row > 0]
                entropy = -float(np.sum(positive * np.log(positive))) if len(positive) else 0.0
                entropies.append(entropy); effective.append(float(np.exp(entropy)) if len(positive) else 0.0)
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    elapsed = time.perf_counter() - start
    return np.concatenate(probabilities), {
        "support_count": len(support),
        "query_count": len(query),
        "context_k": config.context_k,
        "context_retention": config.context_retention,
        "isolated_query_count": len(query) if not len(support) or config.context_retention == 0 else 0,
        "attention_entropy_mean": float(np.mean(entropies)) if entropies else 0.0,
        "effective_peer_count_mean": float(np.mean(effective)) if effective else 0.0,
        "inference_seconds": elapsed,
        "samples_per_second": len(query) / max(elapsed, 1e-12),
    }


def _role_splits(bundle: ManyRxBundle, indices: np.ndarray, budget: int, seed: int) -> dict[str, SupportQuerySplit]:
    return dict(freeze_all_test_receivers(indices, bundle.sample_ids, bundle.receiver_ids, budget=budget, seed=seed))


def _evaluate_condition_on_role(
    condition: str,
    model: torch.nn.Module,
    bundle: ManyRxBundle,
    role_indices: np.ndarray,
    donor_indices: np.ndarray,
    device: torch.device,
    config: RunConfig,
    *,
    source_statistics: NormalizationStatistics | None = None,
    t3a_filter_k: int | None = None,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    role_splits = _role_splits(bundle, role_indices, config.support_budget, config.seed)
    all_indices: list[np.ndarray] = []
    all_probabilities: list[np.ndarray] = []
    receiver_diagnostics: dict[str, Any] = {}
    for receiver, split in role_splits.items():
        query = np.asarray(split.query_indices, dtype=np.int64)
        if condition in {"P1", "P2", "P2_SHUFFLED", "P2_NULL", "P2_MISMATCHED_RX"}:
            assert isinstance(model, ReceiverSupportClassifier)
            support = _control_support(condition, bundle, role_indices, donor_indices, split, budget=config.support_budget, seed=config.seed)
            probabilities, diagnostics = _context_probabilities(model, bundle, split, support, device, config)
        elif condition == "T3A":
            assert isinstance(model, IndependentClassifier) and isinstance(model.classifier, torch.nn.Linear)
            if t3a_filter_k is None:
                raise ValueError("T3A evaluation requires a source-validation-selected filter_k")
            filter_k = int(t3a_filter_k)
            support_embeddings = torch.from_numpy(_encode_backbone(model, bundle, split.support_indices, device, config.sample_batch_size, source_statistics)).to(device)
            query_embeddings = torch.from_numpy(_encode_backbone(model, bundle, query, device, config.sample_batch_size, source_statistics)).to(device)
            logits = T3AAdapter(model.classifier, int(filter_k)).predict(query_embeddings, support_embeddings)
            probabilities = torch.softmax(logits, dim=-1).cpu().numpy()
            diagnostics = {"support_count": split.support_count, "query_count": split.query_count, "t3a_filter_k": int(filter_k)}
        elif condition == "RX_NORM":
            assert isinstance(model, IndependentClassifier)
            target_statistics = _stream_statistics(bundle.features, np.asarray(split.support_indices, dtype=np.int64))
            probabilities = _independent_probabilities(model, bundle, query, device, config.sample_batch_size, target_statistics)
            diagnostics = {"support_count": split.support_count, "query_count": split.query_count, "normalization": asdict(target_statistics)}
        else:
            assert isinstance(model, (IndependentClassifier, DANNClassifier))
            probabilities = _independent_probabilities(model, bundle, query, device, config.sample_batch_size, source_statistics)
            diagnostics = {"support_count_frozen_but_not_used": split.support_count, "query_count": split.query_count}
        all_indices.append(query); all_probabilities.append(probabilities)
        receiver_diagnostics[receiver] = {**support_query_statistics(split), **diagnostics}
    return np.concatenate(all_indices), np.concatenate(all_probabilities), receiver_diagnostics


@torch.no_grad()
def _select_t3a_filter(
    model: IndependentClassifier,
    bundle: ManyRxBundle,
    validation_indices: np.ndarray,
    device: torch.device,
    config: RunConfig,
    statistics: NormalizationStatistics | None,
) -> int:
    splits = _role_splits(bundle, validation_indices, config.support_budget, config.seed)
    scores: dict[int, list[float]] = {value: [] for value in T3A_FILTER_CANDIDATES}
    for split in splits.values():
        support_embeddings = torch.from_numpy(_encode_backbone(model, bundle, split.support_indices, device, config.sample_batch_size, statistics)).to(device)
        query_indices = np.asarray(split.query_indices, dtype=np.int64)
        query_embeddings = torch.from_numpy(_encode_backbone(model, bundle, query_indices, device, config.sample_batch_size, statistics)).to(device)
        for filter_k in T3A_FILTER_CANDIDATES:
            probabilities = torch.softmax(T3AAdapter(model.classifier, filter_k).predict(query_embeddings, support_embeddings), dim=-1).cpu().numpy()
            scores[filter_k].append(float(classification_metrics(bundle.labels[query_indices], probabilities)["macro_f1"]))
    return max(T3A_FILTER_CANDIDATES, key=lambda value: (float(np.mean(scores[value])), -T3A_FILTER_CANDIDATES.index(value)))


def _checkpoint_base(condition: str) -> str:
    if condition in {"P2_SHUFFLED", "P2_NULL", "P2_MISMATCHED_RX"}:
        return "P2"
    if condition == "T3A":
        return "P0"
    if condition == "RX_NORM":
        return "SOURCE_NORM"
    return condition


def run_id(config: RunConfig) -> str:
    return f"{config.protocol_id}__{config.model_stage.lower()}__s{config.seed}__b{config.support_budget}__k{config.context_k}__r{int(config.context_retention*100):03d}__{config.data_variant}"


def _base_run_id(config: RunConfig) -> str:
    base = _checkpoint_base(config.model_stage)
    primary = RunConfig(**{**asdict(config), "model_stage": base, "support_budget": PRIMARY_SUPPORT_BUDGET, "context_k": PRIMARY_CONTEXT_K, "context_retention": 1.0})
    return run_id(primary)


def _load_base_model(
    config: RunConfig,
    run_root: Path,
    class_count: int,
    source_domain_count: int,
    device: torch.device,
) -> tuple[torch.nn.Module, Path, dict[str, Any]]:
    base = _checkpoint_base(config.model_stage)
    model = make_model(base, class_count, source_domain_count=source_domain_count).to(device)
    checkpoint_path = run_root / "runs" / _base_run_id(config) / "checkpoint.pt"
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"required base checkpoint missing: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model_state"])
    return model, checkpoint_path, checkpoint


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
    split_manifest = split_root / config.protocol_id / "split_manifest.csv"
    split_sha = sha256_file(split_manifest); sha = git_sha(repository)
    bundle = bundle or ManyRxBundle.load(converted_root)
    identifier = run_id(config); output = run_root / "runs" / identifier; record_path = output / "run.json"
    compatibility = {"config_hash": config.config_hash, "git_sha": sha, "split_sha256": split_sha, "data_manifest_sha256": bundle.manifest_sha256}
    if resume and (complete := compatible_completion(record_path, compatibility)) is not None:
        return complete
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter(); device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    seeds = set_determinism(config.seed)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    record: dict[str, Any] = {
        "run_id": identifier,
        "status": "RUNNING",
        "protocol_id": config.protocol_id,
        "model_stage": config.model_stage,
        "information_regime": method_registry()[config.model_stage].regime.value,
        "config": asdict(config),
        "config_hash": config.config_hash,
        "git_sha": sha,
        "split_sha256": split_sha,
        "data_manifest_sha256": bundle.manifest_sha256,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "device": str(device),
        "seeds": seeds,
        "target_metrics_blinded": True,
    }
    atomic_json(record, record_path)
    try:
        split_indices = bundle.split_indices(split_manifest)
        train_indices = split_indices["train"]
        if config.smoke:
            train_indices = np.asarray(sorted(train_indices, key=lambda index: stable_digest(bundle.sample_ids[index], namespace="wisig-v2-smoke"))[: min(16384, len(train_indices))], dtype=np.int64)
        _, domain_codes, receiver_values = _receiver_codes(bundle, train_indices)
        source_statistics: NormalizationStatistics | None = None
        base_checkpoint_hash: str | None = None
        history: list[dict[str, Any]] = []
        if config.model_stage in TRAINED_STAGES:
            model = make_model(config.model_stage, len(bundle.transmitter_ids), source_domain_count=len(receiver_values)).to(device)
            if config.model_stage == "SOURCE_NORM":
                source_statistics = _stream_statistics(bundle.features, train_indices)
            optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
            groupdro = GroupDROState(len(receiver_values), config.groupdro_eta, device) if config.model_stage == "DG_GROUPDRO" else None
            episodes = build_context_episodes(train_indices, bundle.receiver_ids, bundle.sample_ids, context_size=config.context_k + 1, seed=config.seed, partition="train", shuffled=False) if config.model_stage in {"P1", "P2"} else None
            best_score = -math.inf; best_epoch = 0; stale = 0; checkpoint_path = output / "checkpoint.pt"
            for epoch in range(config.max_epochs):
                if episodes is not None:
                    train_metrics = _context_epoch(model, bundle, episodes, optimizer, device, config, epoch)  # type: ignore[arg-type]
                else:
                    train_metrics = _independent_epoch(model, bundle, train_indices, optimizer, device, config, epoch, domain_codes, groupdro, source_statistics)
                validation_condition = config.model_stage
                val_order, val_prob, val_diagnostics = _evaluate_condition_on_role(validation_condition, model, bundle, split_indices["validation"], split_indices["train"], device, config, source_statistics=source_statistics)
                val_metrics = classification_metrics(bundle.labels[val_order], val_prob)
                history.append({"epoch": epoch + 1, "train": train_metrics, "source_validation": val_metrics})
                if val_metrics["macro_f1"] > best_score + 1e-8:
                    best_score = val_metrics["macro_f1"]; best_epoch = epoch + 1; stale = 0
                    atomic_torch_save({"model_state": model.state_dict(), "optimizer_state": optimizer.state_dict(), "epoch": best_epoch, "source_validation_macro_f1": best_score, "config_hash": config.config_hash, "source_normalization": asdict(source_statistics) if source_statistics else None}, checkpoint_path)
                else:
                    stale += 1
                atomic_json({"history": history, "best_epoch": best_epoch, "best_source_validation_macro_f1": best_score}, output / "history.json")
                if stale >= config.patience:
                    break
            checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
            model.load_state_dict(checkpoint["model_state"])
        else:
            model, checkpoint_path, checkpoint = _load_base_model(config, run_root, len(bundle.transmitter_ids), len(receiver_values), device)
            base_checkpoint_hash = sha256_file(checkpoint_path)
            if config.model_stage == "RX_NORM":
                raw = checkpoint.get("source_normalization")
                if raw:
                    source_statistics = NormalizationStatistics(**raw).validate()

        selected_t3a_filter: int | None = None
        if config.model_stage == "T3A":
            assert isinstance(model, IndependentClassifier)
            selected_t3a_filter = _select_t3a_filter(model, bundle, split_indices["validation"], device, config, source_statistics)

        val_order, val_prob, val_diag = _evaluate_condition_on_role(config.model_stage, model, bundle, split_indices["validation"], split_indices["train"], device, config, source_statistics=source_statistics, t3a_filter_k=selected_t3a_filter)
        source_validation = classification_metrics(bundle.labels[val_order], val_prob)
        source_validation["per_receiver_macro_f1"] = per_group_macro_f1(bundle.labels[val_order], val_prob, bundle.receiver_ids[val_order])
        target_prediction_hash: str | None = None
        target_diag: dict[str, Any] | None = None
        target_count = 0
        if config.evaluate_target_predictions:
            target_order, target_prob, target_diag = _evaluate_condition_on_role(config.model_stage, model, bundle, split_indices["test"], split_indices["validation"], device, config, source_statistics=source_statistics, t3a_filter_k=selected_t3a_filter)
            target_count = len(target_order)
            target_prediction_hash = write_blind_predictions(output / "predictions_blind.npz", bundle.sample_ids[target_order], target_prob)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        record.update(
            {
                "status": "COMPLETE",
                "end_time": datetime.now(timezone.utc).isoformat(),
                "wall_seconds": time.perf_counter() - started,
                "parameter_count": trainable_parameter_count(model),
                "epochs_completed": len(history),
                "best_epoch": checkpoint.get("epoch"),
                "source_validation_metrics": source_validation,
                "source_validation_receiver_diagnostics": val_diag,
                "held_out_metrics": None,
                "target_prediction_count": target_count,
                "target_prediction_sha256": target_prediction_hash,
                "target_receiver_diagnostics": target_diag,
                "base_checkpoint_sha256": base_checkpoint_hash,
                "selected_t3a_filter_source_validation_only": selected_t3a_filter,
                "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else 0,
                "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                "target_labels_loaded_for_metrics": False,
            }
        )
        atomic_json(record, record_path)
        return record
    except Exception as exc:
        record.update({"status": "FAILED", "failure_reason": f"{type(exc).__name__}: {exc}", "end_time": datetime.now(timezone.utc).isoformat(), "wall_seconds": time.perf_counter() - started})
        atomic_json(record, record_path)
        raise
