"""Blinded, classifier-only supervised receiver adaptation oracle."""

from __future__ import annotations

import hashlib
import json
import os
import resource
import time
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

from openew.paper3.wisig.archive import sha256_file
from openew.paper3.wisig.checkpoint import atomic_json, atomic_torch_save
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig.metrics import classification_metrics
from openew.paper3.wisig.models import IndependentClassifier
from openew.paper3.wisig_v2.blinding import write_blind_predictions
from openew.paper3.wisig_v2.runner import RunConfig, _encode_backbone, remap_bundle_to_split_targets, set_determinism
from openew.paper3.wisig_v2.support import freeze_support_query

from .contracts import BENCHMARK_SEEDS, PRIMARY_SUPPORT_BUDGET


@dataclass(frozen=True, order=True)
class OracleHyperparameters:
    learning_rate: float
    steps: int

    def validate(self) -> "OracleHyperparameters":
        if self.learning_rate not in (1e-4, 5e-4, 1e-3) or self.steps not in (5, 20):
            raise ValueError("oracle hyperparameters are outside preregistered grid")
        return self


ORACLE_CANDIDATES = tuple(OracleHyperparameters(rate, steps) for rate in (1e-4, 5e-4, 1e-3) for steps in (5, 20))


def _model_for_checkpoint(checkpoint_path: Path, class_count: int, device: torch.device) -> IndependentClassifier:
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    model = IndependentClassifier(class_count, wide=False).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model


def adapt_linear_classifier(
    classifier: nn.Linear,
    support_embeddings: torch.Tensor,
    support_labels: torch.Tensor,
    hyperparameters: OracleHyperparameters,
) -> tuple[nn.Linear, list[float]]:
    """Fit a copied linear head; the source model and backbone remain immutable."""
    hyperparameters.validate()
    if not isinstance(classifier, nn.Linear):
        raise TypeError("SUP-FT requires P0's linear classifier")
    if support_embeddings.ndim != 2 or support_embeddings.shape[1] != classifier.in_features:
        raise ValueError("support embedding shape does not match classifier")
    if support_labels.ndim != 1 or len(support_labels) != len(support_embeddings):
        raise ValueError("support labels do not align")
    if len(support_labels) == 0:
        raise ValueError("supervised oracle requires labeled support")
    if int(support_labels.min()) < 0 or int(support_labels.max()) >= classifier.out_features:
        raise ValueError("support label outside classifier class space")
    head = deepcopy(classifier)
    head.train()
    optimizer = torch.optim.AdamW(head.parameters(), lr=hyperparameters.learning_rate, weight_decay=0.0)
    losses: list[float] = []
    for _ in range(hyperparameters.steps):
        optimizer.zero_grad(set_to_none=True)
        logits = head(support_embeddings.detach())
        loss = F.cross_entropy(logits, support_labels)
        if not torch.isfinite(loss):
            raise FloatingPointError("non-finite supervised adaptation loss")
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    head.eval()
    return head, losses


@torch.no_grad()
def _head_probabilities(head: nn.Linear, embeddings: torch.Tensor, batch_size: int = 4096) -> np.ndarray:
    rows: list[np.ndarray] = []
    for offset in range(0, len(embeddings), batch_size):
        logits = head(embeddings[offset : offset + batch_size])
        if not torch.isfinite(logits).all():
            raise FloatingPointError("non-finite supervised-oracle output")
        rows.append(torch.softmax(logits, dim=-1).cpu().numpy())
    return np.concatenate(rows).astype(np.float32, copy=False)


def select_oracle_hyperparameters(
    model: IndependentClassifier,
    bundle: ManyRxBundle,
    validation_indices: np.ndarray,
    *,
    seed: int,
    device: torch.device,
    candidates: Sequence[OracleHyperparameters] = ORACLE_CANDIDATES,
) -> tuple[OracleHyperparameters, list[dict[str, Any]]]:
    """Nested source-receiver simulation; target receiver is absent."""
    receivers = sorted({str(bundle.receiver_ids[index]) for index in validation_indices})
    if len(receivers) < 2:
        raise ValueError("oracle selection requires multiple source-validation receivers")
    splits = [freeze_support_query(validation_indices, bundle.sample_ids, bundle.receiver_ids, receiver_id=receiver, support_budget=PRIMARY_SUPPORT_BUDGET, seed=seed) for receiver in receivers]
    encoded: list[tuple[object, np.ndarray, torch.Tensor, torch.Tensor]] = []
    for split in splits:
        support = np.asarray(split.support_indices, dtype=np.int64)
        query = np.asarray(split.query_indices, dtype=np.int64)
        support_embeddings = torch.from_numpy(_encode_backbone(model, bundle, support, device, 1024)).to(device)
        query_embeddings = torch.from_numpy(_encode_backbone(model, bundle, query, device, 1024)).to(device)
        encoded.append((split, query, support_embeddings, query_embeddings))
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate.validate()
        scores: list[float] = []
        for split, query, support_embeddings, query_embeddings in encoded:
            support = np.asarray(split.support_indices, dtype=np.int64)
            labels = torch.from_numpy(bundle.labels[support]).long().to(device)
            head, losses = adapt_linear_classifier(model.classifier, support_embeddings, labels, candidate)
            probabilities = _head_probabilities(head, query_embeddings)
            score = float(classification_metrics(bundle.labels[query], probabilities)["macro_f1"])
            scores.append(score)
            rows.append({
                "receiver_id": split.receiver_id,
                "learning_rate": candidate.learning_rate,
                "steps": candidate.steps,
                "macro_f1": score,
                "loss_start": losses[0],
                "loss_end": losses[-1],
                "support_count": len(support),
                "query_count": len(query),
            })
    grouped: dict[OracleHyperparameters, float] = {}
    for candidate in candidates:
        values = [row["macro_f1"] for row in rows if row["learning_rate"] == candidate.learning_rate and row["steps"] == candidate.steps]
        grouped[candidate] = float(np.mean(values))
    selected = max(candidates, key=lambda row: (grouped[row], -ORACLE_CANDIDATES.index(row)))
    return selected, rows


def _p0_run_id(protocol: str, seed: int) -> str:
    return f"{protocol}__p0__s{seed}__b128__k32__r100__raw"


def oracle_run_id(protocol: str, seed: int) -> str:
    return f"{protocol}__sup_ft_128__s{seed}"


def _config_hash(protocol: str, seed: int) -> str:
    payload = json.dumps({"method": "SUP_FT_128", "protocol": protocol, "seed": seed, "support": 128, "candidates": [asdict(row) for row in ORACLE_CANDIDATES], "scope": "linear_classifier_only"}, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def run_oracle_record(
    converted_root: str | Path,
    split_root: str | Path,
    frozen_run_root: str | Path,
    output_root: str | Path,
    *,
    protocol: str,
    seed: int,
    bundle: ManyRxBundle | None = None,
    source_only: bool = False,
    resume: bool = True,
) -> dict[str, Any]:
    if seed not in BENCHMARK_SEEDS:
        raise ValueError("seed is not frozen")
    converted_root, split_root, frozen_run_root, output_root = map(Path, (converted_root, split_root, frozen_run_root, output_root))
    output = output_root / "runs" / oracle_run_id(protocol, seed)
    record_path = output / "run.json"
    config_hash = _config_hash(protocol, seed)
    split_path = split_root / protocol / "split_manifest.csv"
    checkpoint_path = frozen_run_root / "runs" / _p0_run_id(protocol, seed) / "checkpoint.pt"
    compatibility = {"config_hash": config_hash, "split_sha256": sha256_file(split_path), "base_checkpoint_sha256": sha256_file(checkpoint_path)}
    if resume and record_path.exists():
        prior = json.loads(record_path.read_text(encoding="utf-8"))
        if prior.get("status") == "COMPLETE" and all(prior.get(key) == value for key, value in compatibility.items()) and prior.get("source_only") is source_only:
            return prior
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    record: dict[str, Any] = {"run_id": oracle_run_id(protocol, seed), "status": "RUNNING", "protocol_id": protocol, "seed": seed, "method": "SUP_FT_128", "source_only": source_only, "target_metrics": None, **compatibility, "start_time": datetime.now(timezone.utc).isoformat()}
    atomic_json(record, record_path)
    try:
        set_determinism(seed)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        original = bundle or ManyRxBundle.load(converted_root)
        local = remap_bundle_to_split_targets(original, split_root / protocol / "split_summary.json")
        roles = local.split_indices(split_path)
        model = _model_for_checkpoint(checkpoint_path, len(local.transmitter_ids), device)
        selected, selection_rows = select_oracle_hyperparameters(model, local, roles["validation"], seed=seed, device=device)
        selection_path = output / "source_validation_selection.json"
        atomic_json({"selected": asdict(selected), "rows": selection_rows, "target_receiver_used": False}, selection_path)
        prediction_sha: str | None = None
        target_count = 0
        support_count = 0
        adapted_parameters = model.classifier.weight.numel() + model.classifier.bias.numel()
        losses: list[float] = []
        if not source_only:
            target_receiver = str(local.receiver_ids[roles["test"][0]])
            split = freeze_support_query(roles["test"], local.sample_ids, local.receiver_ids, receiver_id=target_receiver, support_budget=128, seed=seed)
            support = np.asarray(split.support_indices, dtype=np.int64)
            query = np.asarray(split.query_indices, dtype=np.int64)
            support_embeddings = torch.from_numpy(_encode_backbone(model, local, support, device, 1024)).to(device)
            query_embeddings = torch.from_numpy(_encode_backbone(model, local, query, device, 1024)).to(device)
            head, losses = adapt_linear_classifier(model.classifier, support_embeddings, torch.from_numpy(local.labels[support]).long().to(device), selected)
            probabilities = _head_probabilities(head, query_embeddings)
            prediction_sha = write_blind_predictions(output / "predictions_blind.npz", local.sample_ids[query], probabilities)
            atomic_torch_save({"classifier_state": head.state_dict(), "selected": asdict(selected), "base_checkpoint_sha256": compatibility["base_checkpoint_sha256"]}, output / "adapted_classifier.pt")
            target_count, support_count = len(query), len(support)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        record.update({
            "status": "COMPLETE", "end_time": datetime.now(timezone.utc).isoformat(), "wall_seconds": time.perf_counter() - started,
            "device": str(device), "selected_source_validation_only": asdict(selected), "selection_sha256": sha256_file(selection_path),
            "support_count": support_count, "query_count": target_count, "prediction_sha256": prediction_sha,
            "target_labels_used_for_adaptation": not source_only, "target_labels_used_for_metrics": False,
            "query_used_for_adaptation": False, "adapted_parameter_count": adapted_parameters,
            "adaptation_loss_start": losses[0] if losses else None, "adaptation_loss_end": losses[-1] if losses else None,
            "peak_cpu_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else 0,
        })
        atomic_json(record, record_path)
        return record
    except Exception as exc:
        record.update({"status": "FAILED", "failure_reason": f"{type(exc).__name__}: {exc}", "end_time": datetime.now(timezone.utc).isoformat(), "wall_seconds": time.perf_counter() - started})
        atomic_json(record, record_path)
        raise
