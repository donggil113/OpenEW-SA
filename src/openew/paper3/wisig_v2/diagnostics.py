"""Post-unblinding oracle composition and fixed sensitivity diagnostics."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
import torch

from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig.metrics import classification_metrics

from .controls import oracle_support_for_query, transmitter_pure_oracle_pool
from .hashing import stable_digest
from .models import ReceiverSupportClassifier
from .runner import RunConfig, _encode_backbone, _context_probabilities, remap_bundle_to_split_targets
from .support import SupportQuerySplit, freeze_support_query


def _load_p2(record_path: Path, class_count: int, device: torch.device) -> ReceiverSupportClassifier:
    model = ReceiverSupportClassifier(class_count, attention=True).to(device)
    checkpoint = torch.load(record_path.parent / "checkpoint.pt", map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model_state"]); model.eval()
    return model


@torch.no_grad()
def _variable_oracle_probabilities(
    model: ReceiverSupportClassifier,
    bundle: ManyRxBundle,
    query_indices: np.ndarray,
    peer_lists: Sequence[Sequence[int]],
    device: torch.device,
    batch_size: int = 1024,
) -> np.ndarray:
    if len(query_indices) != len(peer_lists):
        raise ValueError("one peer list is required per query")
    universe = sorted({int(index) for peers in peer_lists for index in peers})
    if not universe:
        raise ValueError("oracle peer universe is empty")
    embeddings = _encode_backbone(model, bundle, universe, device, batch_size)
    position = {index: offset for offset, index in enumerate(universe)}
    width = max(len(peers) for peers in peer_lists)
    if width <= 0:
        raise ValueError("oracle context is empty")
    rows: list[np.ndarray] = []
    for start in range(0, len(query_indices), batch_size):
        stop = min(start + batch_size, len(query_indices))
        query = query_indices[start:stop]
        anchor = torch.from_numpy(_encode_backbone(model, bundle, query, device, batch_size)).to(device)
        peer_tensor = np.zeros((len(query), width, 64), dtype=np.float32)
        mask = np.zeros((len(query), width), dtype=bool)
        for row, peers in enumerate(peer_lists[start:stop]):
            for column, index in enumerate(peers):
                peer_tensor[row, column] = embeddings[position[int(index)]]; mask[row, column] = True
        output = model.predict_from_embeddings(anchor, torch.from_numpy(peer_tensor).to(device), torch.from_numpy(mask).to(device))
        rows.append(torch.softmax(output.logits, dim=-1).cpu().numpy())
    return np.concatenate(rows)


def run_oracle_composition_diagnostics(
    converted_root: str | Path,
    split_root: str | Path,
    run_root: str | Path,
    destination: str | Path,
) -> pd.DataFrame:
    split_root, run_root, destination = Path(split_root), Path(run_root), Path(destination)
    original = ManyRxBundle.load(converted_root)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows: list[dict[str, Any]] = []
    p2_records = sorted((run_root / "runs").glob("receiver_loso_*__p2__s*__b128__k32__r100__raw/run.json"))
    if len(p2_records) != 32 * 5:
        raise RuntimeError(f"expected 160 P2 primary records, found {len(p2_records)}")
    for record_path in p2_records:
        record = json.loads(record_path.read_text(encoding="utf-8")); protocol = record["protocol_id"]; seed = int(record["config"]["seed"])
        bundle = remap_bundle_to_split_targets(original, split_root / protocol / "split_summary.json")
        test = bundle.split_indices(split_root / protocol / "split_manifest.csv")["test"]
        receiver = str(bundle.receiver_ids[test[0]])
        split = freeze_support_query(test, bundle.sample_ids, bundle.receiver_ids, receiver_id=receiver, support_budget=128, seed=seed)
        query = np.asarray(split.query_indices, dtype=np.int64); support = tuple(split.support_indices)
        model = _load_p2(record_path, len(bundle.transmitter_ids), device)
        pure = transmitter_pure_oracle_pool(support, bundle.labels, bundle.sample_ids, budget=128, seed=seed)
        pure_label = int(bundle.labels[pure[0]])
        conditions: dict[str, list[tuple[int, ...]]] = {
            "TRANSMITTER_PURE_ORACLE": [tuple(pure[:32])] * len(query),
            "SAME_CLASS_EXCLUDED_ORACLE": [oracle_support_for_query(support, bundle.labels, query_label=int(bundle.labels[index]), mode="same_class_excluded", sample_ids=bundle.sample_ids, seed=seed, k=32) for index in query],
            "SAME_CLASS_ONLY_ORACLE": [oracle_support_for_query(support, bundle.labels, query_label=int(bundle.labels[index]), mode="same_class_only", sample_ids=bundle.sample_ids, seed=seed, k=32) for index in query],
        }
        for condition, peers in conditions.items():
            nonempty = np.asarray([bool(values) for values in peers])
            probabilities = np.full((len(query), len(bundle.transmitter_ids)), np.nan, dtype=np.float32)
            if nonempty.any():
                probabilities[nonempty] = _variable_oracle_probabilities(model, bundle, query[nonempty], [peers[index] for index in np.flatnonzero(nonempty)], device)
            valid_prob = probabilities[nonempty]
            metrics = classification_metrics(bundle.labels[query[nonempty]], valid_prob) if nonempty.any() else {key: float("nan") for key in ("macro_f1", "accuracy", "balanced_accuracy", "ece")}
            predicted = valid_prob.argmax(axis=1) if len(valid_prob) else np.asarray([], dtype=int)
            rows.append(
                {
                    "protocol_id": protocol,
                    "receiver_id": receiver,
                    "seed": seed,
                    "condition": condition,
                    "query_count": len(query),
                    "evaluable_query_count": int(nonempty.sum()),
                    "mean_peer_count": float(np.mean([len(values) for values in peers])),
                    "pure_support_label": pure_label if condition == "TRANSMITTER_PURE_ORACLE" else None,
                    "prediction_fraction_pure_support_label": float(np.mean(predicted == pure_label)) if condition == "TRANSMITTER_PURE_ORACLE" and len(predicted) else None,
                    **metrics,
                    "deployable": False,
                    "labels_used_to_construct_context": True,
                }
            )
    frame = pd.DataFrame(rows).sort_values(["condition", "protocol_id", "seed"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False, lineterminator="\n")
    return frame


def run_p2_sensitivities(
    converted_root: str | Path,
    split_root: str | Path,
    run_root: str | Path,
    destination_root: str | Path,
) -> dict[str, pd.DataFrame]:
    split_root, run_root, destination_root = Path(split_root), Path(run_root), Path(destination_root)
    original = ManyRxBundle.load(converted_root)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    budget_rows: list[dict[str, Any]] = []; k_rows: list[dict[str, Any]] = []
    records = sorted((run_root / "runs").glob("receiver_loso_*__p2__s*__b128__k32__r100__raw/run.json"))
    if len(records) != 160:
        raise RuntimeError("P2 sensitivities require all 160 primary P2 checkpoints")
    for record_path in records:
        record = json.loads(record_path.read_text(encoding="utf-8")); protocol = record["protocol_id"]; seed = int(record["config"]["seed"])
        bundle = remap_bundle_to_split_targets(original, split_root / protocol / "split_summary.json")
        test = bundle.split_indices(split_root / protocol / "split_manifest.csv")["test"]
        receiver = str(bundle.receiver_ids[test[0]]); model = _load_p2(record_path, len(bundle.transmitter_ids), device)
        max_split = freeze_support_query(test, bundle.sample_ids, bundle.receiver_ids, receiver_id=receiver, support_budget=256, seed=seed)
        common_query = max_split.query_indices
        for budget in (16, 32, 64, 128, 256):
            support = max_split.support_indices[:budget]
            split = SupportQuerySplit(receiver, tuple(support), tuple(common_query), budget).validate()
            config = RunConfig(protocol, "P2", seed, support_budget=budget, context_k=min(32, budget), evaluate_target_predictions=True)
            probabilities, diagnostics = _context_probabilities(model, bundle, split, support, device, config)
            budget_rows.append({"protocol_id": protocol, "receiver_id": receiver, "seed": seed, "support_budget": budget, "context_k": min(32, budget), **classification_metrics(bundle.labels[np.asarray(common_query)], probabilities), **diagnostics, "common_query_budget": 256})
        primary_split = freeze_support_query(test, bundle.sample_ids, bundle.receiver_ids, receiver_id=receiver, support_budget=128, seed=seed)
        for k in (8, 16, 32, 64):
            config = RunConfig(protocol, "P2", seed, support_budget=128, context_k=k, evaluate_target_predictions=True)
            probabilities, diagnostics = _context_probabilities(model, bundle, primary_split, primary_split.support_indices, device, config)
            k_rows.append({"protocol_id": protocol, "receiver_id": receiver, "seed": seed, "support_budget": 128, "context_k": k, **classification_metrics(bundle.labels[np.asarray(primary_split.query_indices)], probabilities), **diagnostics})
    destination_root.mkdir(parents=True, exist_ok=True)
    outputs = {"support_budget": pd.DataFrame(budget_rows), "context_k": pd.DataFrame(k_rows)}
    outputs["support_budget"].to_csv(destination_root / "support_budget_results.csv", index=False, lineterminator="\n")
    outputs["context_k"].to_csv(destination_root / "context_k_results.csv", index=False, lineterminator="\n")
    return outputs
