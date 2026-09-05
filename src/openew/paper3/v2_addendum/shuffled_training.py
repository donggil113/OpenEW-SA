"""Exact-P2 source training with label-free shuffled receiver contexts."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch

from openew.paper3.wisig.checkpoint import atomic_json, atomic_torch_save
from openew.paper3.wisig.context import build_context_episodes
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig.metrics import classification_metrics
from openew.paper3.wisig_v2.hashing import canonical_json_bytes
from openew.paper3.wisig_v2.models import ReceiverSupportClassifier, trainable_parameter_count
from openew.paper3.wisig_v2.runner import RunConfig, _context_epoch, _evaluate_condition_on_role, remap_bundle_to_split_targets, set_determinism

from .contracts import ADDENDUM_SEEDS, EvidenceCategory, require_posthoc_output_path, validate_seed, verify_frozen_v2_inputs


@dataclass(frozen=True)
class ShuffledTrainingConfig:
    protocol_id: str
    seed: int
    max_epochs: int = 30
    patience: int = 8
    learning_rate: float = 5e-4
    weight_decay: float = 1e-4
    sample_batch_size: int = 1024
    episode_node_budget: int = 1056
    context_k: int = 32
    support_budget: int = 128

    def validate(self) -> "ShuffledTrainingConfig":
        validate_seed(self.seed)
        if not self.protocol_id.startswith("receiver_loso_"):
            raise ValueError("shuffled training is limited to frozen receiver LOSO")
        if (self.max_epochs, self.patience, self.learning_rate, self.weight_decay, self.sample_batch_size, self.episode_node_budget, self.context_k, self.support_budget) != (30, 8, 5e-4, 1e-4, 1024, 1056, 32, 128):
            raise ValueError("shuffled training hyperparameters must equal frozen V2")
        return self

    @property
    def config_hash(self) -> str:
        payload = {**asdict(self), "training_context": "SHUFFLED_RECEIVER", "analysis_status": "POSTHOC"}
        return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def run_shuffled_training(
    repository: str | Path,
    converted_root: str | Path,
    split_root: str | Path,
    output_root: str | Path,
    config: ShuffledTrainingConfig,
    *,
    v2_root: str | Path,
    bundle: ManyRxBundle | None = None,
) -> dict[str, Any]:
    config = config.validate()
    output_root = require_posthoc_output_path(output_root, v2_root)
    verify_frozen_v2_inputs(v2_root, converted_root)
    repository, split_root = Path(repository), Path(split_root)
    run_dir = output_root / "shuffled_training" / "runs" / f"{config.protocol_id}__s{config.seed}"
    record_path = run_dir / "run.json"
    if record_path.exists():
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if record.get("status") == "COMPLETE" and record.get("config_hash") == config.config_hash:
            return record
    run_dir.mkdir(parents=True, exist_ok=True)
    original = bundle or ManyRxBundle.load(converted_root)
    local = remap_bundle_to_split_targets(original, split_root / config.protocol_id / "split_summary.json")
    roles = local.split_indices(split_root / config.protocol_id / "split_manifest.csv")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    set_determinism(config.seed)
    model = ReceiverSupportClassifier(len(local.transmitter_ids), attention=True).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    train_config = RunConfig(config.protocol_id, "P2", config.seed)
    episodes = build_context_episodes(roles["train"], local.receiver_ids, local.sample_ids, context_size=33, seed=config.seed, partition="train", shuffled=True)
    record: dict[str, Any] = {
        "status": "RUNNING",
        "analysis_status": "POSTHOC_MECHANISTIC",
        "protocol_id": config.protocol_id,
        "seed": config.seed,
        "config": asdict(config),
        "config_hash": config.config_hash,
        "training_context": "SHUFFLED_RECEIVER_LABEL_FREE",
        "labels_used_to_construct_training_context": False,
        "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip(),
        "start_time": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(record, record_path)
    checkpoint_path = run_dir / "checkpoint.pt"
    history: list[dict[str, Any]] = []
    best, best_epoch, stale = -math.inf, 0, 0
    started = time.perf_counter()
    try:
        for epoch in range(config.max_epochs):
            train_metrics = _context_epoch(model, local, episodes, optimizer, device, train_config, epoch)
            order, probabilities, _ = _evaluate_condition_on_role("P2", model, local, roles["validation"], roles["train"], device, train_config)
            validation = classification_metrics(local.labels[order], probabilities)
            history.append({"epoch": epoch + 1, "train": train_metrics, "source_validation": validation})
            if validation["macro_f1"] > best + 1e-8:
                best, best_epoch, stale = float(validation["macro_f1"]), epoch + 1, 0
                atomic_torch_save({"model_state": model.state_dict(), "optimizer_state": optimizer.state_dict(), "epoch": best_epoch, "source_validation_macro_f1": best, "config_hash": config.config_hash}, checkpoint_path)
            else:
                stale += 1
            atomic_json({"history": history, "best_epoch": best_epoch, "best_source_validation_macro_f1": best}, run_dir / "history.json")
            if stale >= config.patience:
                break
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
        model.load_state_dict(checkpoint["model_state"])
        evaluations: dict[str, Any] = {}
        for condition in ("P2", "P2_SHUFFLED", "P2_NULL"):
            order, probabilities, diagnostics = _evaluate_condition_on_role(condition, model, local, roles["test"], roles["validation"], device, train_config)
            evaluations[condition] = {
                "condition": {"P2": "NATURAL", "P2_SHUFFLED": "SHUFFLED", "P2_NULL": "NULL"}[condition],
                "evidence_category": EvidenceCategory.DEPLOYABLE_METHOD.value if condition == "P2" else EvidenceCategory.LABEL_FREE_CONTROL.value,
                "query_count": len(order),
                "metrics": classification_metrics(local.labels[order], probabilities),
                "receiver_diagnostics": diagnostics,
            }
        record.update({
            "status": "COMPLETE",
            "end_time": datetime.now(timezone.utc).isoformat(),
            "wall_seconds": time.perf_counter() - started,
            "epochs_completed": len(history),
            "best_epoch": best_epoch,
            "best_source_validation_macro_f1": best,
            "parameter_count": trainable_parameter_count(model),
            "evaluations": evaluations,
        })
        atomic_json(record, record_path)
        return record
    except Exception as exc:
        record.update({"status": "FAILED", "failure_reason": f"{type(exc).__name__}: {exc}", "end_time": datetime.now(timezone.utc).isoformat(), "wall_seconds": time.perf_counter() - started})
        atomic_json(record, record_path)
        raise


def run_shuffled_suite(
    repository: str | Path,
    converted_root: str | Path,
    split_root: str | Path,
    output_root: str | Path,
    *,
    v2_root: str | Path,
    worker_index: int = 0,
    worker_count: int = 1,
) -> list[dict[str, Any]]:
    if worker_count <= 0 or not 0 <= worker_index < worker_count:
        raise ValueError("invalid worker partition")
    protocols = sorted(path.name for path in Path(split_root).glob("receiver_loso_*"))
    if len(protocols) != 32:
        raise RuntimeError(f"expected 32 LOSO protocols, found {len(protocols)}")
    bundle = ManyRxBundle.load(converted_root)
    jobs = [(protocol, seed) for protocol in protocols for seed in ADDENDUM_SEEDS]
    selected = [job for offset, job in enumerate(jobs) if offset % worker_count == worker_index]
    return [run_shuffled_training(repository, converted_root, split_root, output_root, ShuffledTrainingConfig(protocol, seed), v2_root=v2_root, bundle=bundle) for protocol, seed in selected]
