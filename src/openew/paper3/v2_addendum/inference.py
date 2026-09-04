"""Checkpoint-reusing post-hoc V2 inference diagnostics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
import torch

from openew.paper3.wisig.archive import sha256_file
from openew.paper3.wisig.checkpoint import atomic_json
from openew.paper3.wisig.context import build_context_episodes
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig.metrics import classification_metrics
from openew.paper3.wisig_v2.blinding import read_blind_predictions
from openew.paper3.wisig_v2.models import IndependentClassifier, ReceiverSupportClassifier, T3AAdapter
from openew.paper3.wisig_v2.runner import (
    RunConfig,
    _context_probabilities,
    _encode_backbone,
    _load_base_model,
    remap_bundle_to_split_targets,
)
from openew.paper3.wisig_v2.statistics import descriptive_summary, receiver_bootstrap
from openew.paper3.wisig_v2.support import SupportQuerySplit, freeze_support_query

from .contracts import (
    ADDENDUM_SEEDS,
    EXPECTED_RECEIVERS,
    PRIMARY_CONTEXT_K,
    PRIMARY_SUPPORT_BUDGET,
    SUPPORT_BUDGETS,
    EvidenceCategory,
    require_posthoc_output_path,
    verify_frozen_v2_inputs,
)


def _record_paths(run_root: Path, stage: str) -> list[Path]:
    values = sorted((run_root / "runs").glob(f"receiver_loso_*__{stage.lower()}__s*__b128__k32__r100__raw/run.json"))
    expected = EXPECTED_RECEIVERS * len(ADDENDUM_SEEDS)
    if len(values) != expected:
        raise RuntimeError(f"expected {expected} {stage} records, found {len(values)}")
    return values


def _load_record(path: Path) -> dict[str, Any]:
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("status") != "COMPLETE" or record.get("held_out_metrics") is not None:
        raise RuntimeError(f"frozen blind record is invalid: {path}")
    if record.get("target_labels_loaded_for_metrics") is not False:
        raise RuntimeError(f"frozen blind record exposed labels: {path}")
    return record


def _device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _load_p2(record_path: Path, class_count: int, device: torch.device) -> ReceiverSupportClassifier:
    model = ReceiverSupportClassifier(class_count, attention=True).to(device)
    checkpoint = torch.load(record_path.parent / "checkpoint.pt", map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model


@torch.no_grad()
def _probabilities_from_peer_lists(
    model: ReceiverSupportClassifier,
    embeddings: np.ndarray,
    global_indices: np.ndarray,
    query_indices: np.ndarray,
    peer_lists: Sequence[Sequence[int]],
    device: torch.device,
    *,
    batch_size: int = 1024,
) -> np.ndarray:
    if len(query_indices) != len(peer_lists):
        raise ValueError("one peer list is required per query")
    position = {int(index): offset for offset, index in enumerate(global_indices)}
    if any(int(index) not in position for peers in peer_lists for index in peers):
        raise ValueError("peer is outside the encoded receiver partition")
    width = max((len(peers) for peers in peer_lists), default=0)
    if width <= 0:
        raise ValueError("all peer lists are empty")
    rows: list[np.ndarray] = []
    for start in range(0, len(query_indices), batch_size):
        stop = min(start + batch_size, len(query_indices))
        query = query_indices[start:stop]
        anchors = torch.from_numpy(np.asarray([embeddings[position[int(i)]] for i in query], dtype=np.float32)).to(device)
        peers = np.zeros((len(query), width, embeddings.shape[1]), dtype=np.float32)
        mask = np.zeros((len(query), width), dtype=bool)
        for row, values in enumerate(peer_lists[start:stop]):
            for column, value in enumerate(values):
                peers[row, column] = embeddings[position[int(value)]]
                mask[row, column] = True
        output = model.predict_from_embeddings(anchors, torch.from_numpy(peers).to(device), torch.from_numpy(mask).to(device))
        rows.append(torch.softmax(output.logits, dim=-1).cpu().numpy())
    result = np.concatenate(rows)
    if not np.isfinite(result).all():
        raise FloatingPointError("non-finite addendum probabilities")
    return result


@torch.no_grad()
def _full_partition_probabilities(
    model: ReceiverSupportClassifier,
    embeddings: np.ndarray,
    global_indices: np.ndarray,
    query_indices: np.ndarray,
    device: torch.device,
    *,
    batch_size: int = 1024,
) -> np.ndarray:
    """Exact attentive context over every other receiver-partition sample in O(N)."""

    if model.scorer is None:
        raise TypeError("full-partition diagnostic requires attentive P2")
    encoded = torch.from_numpy(embeddings).to(device)
    scores = model.scorer(encoded).squeeze(-1)
    maximum = scores.max()
    weights = torch.exp(scores - maximum)
    weighted_sum = (weights[:, None] * encoded).sum(dim=0)
    weight_sum = weights.sum()
    position = {int(index): offset for offset, index in enumerate(global_indices)}
    rows: list[np.ndarray] = []
    for start in range(0, len(query_indices), batch_size):
        indices = query_indices[start : start + batch_size]
        offsets = torch.as_tensor([position[int(index)] for index in indices], device=device)
        anchors = encoded[offsets]
        anchor_weights = weights[offsets]
        denominator = (weight_sum - anchor_weights).clamp_min(1e-12)
        context = (weighted_sum[None, :] - anchor_weights[:, None] * anchors) / denominator[:, None]
        logits = model.fusion(torch.cat([anchors, context], dim=-1))
        rows.append(torch.softmax(logits, dim=-1).cpu().numpy())
    result = np.concatenate(rows)
    if not np.isfinite(result).all():
        raise FloatingPointError("non-finite full-partition probabilities")
    return result


def _chunk_peers(
    indices: np.ndarray,
    receiver_ids: np.ndarray,
    sample_ids: np.ndarray,
    query_indices: np.ndarray,
    *,
    seed: int,
) -> list[tuple[int, ...]]:
    episodes = build_context_episodes(indices, receiver_ids, sample_ids, context_size=33, seed=seed, partition="test", shuffled=False)
    lookup: dict[int, tuple[int, ...]] = {}
    for episode in episodes.episodes:
        for anchor in episode:
            lookup[int(anchor)] = tuple(int(peer) for peer in episode if int(peer) != int(anchor))
    result = [lookup[int(query)] for query in query_indices]
    if any(len(values) > PRIMARY_CONTEXT_K for values in result):
        raise RuntimeError("query-coupled chunk exceeded frozen context width")
    return result


def _metric_row(
    *,
    protocol: str,
    receiver: str,
    seed: int,
    condition: str,
    labels: np.ndarray,
    probabilities: np.ndarray,
    query_ids: np.ndarray,
    category: EvidenceCategory,
) -> dict[str, Any]:
    digest = hashlib.sha256()
    digest.update(np.asarray(query_ids, dtype="S").tobytes())
    digest.update(np.asarray(probabilities, dtype=np.float32).tobytes())
    return {
        "protocol_id": protocol,
        "receiver_id": receiver,
        "seed": seed,
        "condition": condition,
        "evidence_category": category.value,
        "query_count": len(labels),
        "prediction_payload_sha256": digest.hexdigest(),
        **classification_metrics(labels, probabilities),
    }


def run_query_coupling_diagnostic(
    converted_root: str | Path,
    split_root: str | Path,
    run_root: str | Path,
    output_root: str | Path,
    *,
    v2_root: str | Path,
) -> pd.DataFrame:
    """Evaluate A1/A2/A3 without retraining or altering frozen V2 outputs."""

    output_root = require_posthoc_output_path(output_root, v2_root)
    output_root.mkdir(parents=True, exist_ok=True)
    verify_frozen_v2_inputs(v2_root, converted_root)
    split_root, run_root = Path(split_root), Path(run_root)
    original = ManyRxBundle.load(converted_root)
    device = _device()
    rows: list[dict[str, Any]] = []
    for record_path in _record_paths(run_root, "P2"):
        record = _load_record(record_path)
        protocol, seed = str(record["protocol_id"]), int(record["config"]["seed"])
        record_out = output_root / "records" / "query_coupling" / f"{protocol}__s{seed}.json"
        if record_out.exists():
            rows.extend(json.loads(record_out.read_text(encoding="utf-8"))["rows"])
            continue
        bundle = remap_bundle_to_split_targets(original, split_root / protocol / "split_summary.json")
        test = bundle.split_indices(split_root / protocol / "split_manifest.csv")["test"]
        receiver = str(bundle.receiver_ids[test[0]])
        split = freeze_support_query(test, bundle.sample_ids, bundle.receiver_ids, receiver_id=receiver, support_budget=128, seed=seed)
        query = np.asarray(split.query_indices, dtype=np.int64)
        query_ids = bundle.sample_ids[query]
        labels = bundle.labels[query]
        blind = read_blind_predictions(record_path.parent / "predictions_blind.npz")
        if not np.array_equal(blind["sample_ids"].astype(str), query_ids.astype(str)):
            raise RuntimeError(f"A1 query IDs differ from frozen prediction order: {protocol} seed {seed}")
        model = _load_p2(record_path, len(bundle.transmitter_ids), device)
        embeddings = _encode_backbone(model, bundle, test, device, 1024)
        coupled = _probabilities_from_peer_lists(model, embeddings, test, query, _chunk_peers(test, bundle.receiver_ids, bundle.sample_ids, query, seed=seed), device)
        full = _full_partition_probabilities(model, embeddings, test, query, device)
        result_rows = [
            _metric_row(protocol=protocol, receiver=receiver, seed=seed, condition="DISJOINT_NATURAL", labels=labels, probabilities=blind["probabilities"], query_ids=query_ids, category=EvidenceCategory.DEPLOYABLE_METHOD),
            _metric_row(protocol=protocol, receiver=receiver, seed=seed, condition="QUERY_COUPLED_CHUNK", labels=labels, probabilities=coupled, query_ids=query_ids, category=EvidenceCategory.LABEL_FREE_CONTROL),
            _metric_row(protocol=protocol, receiver=receiver, seed=seed, condition="FULL_RECEIVER_PARTITION", labels=labels, probabilities=full, query_ids=query_ids, category=EvidenceCategory.LABEL_FREE_CONTROL),
        ]
        atomic_json({"status": "COMPLETE", "retrained": False, "labels_used_for_context": False, "rows": result_rows}, record_out)
        rows.extend(result_rows)
    frame = pd.DataFrame(rows).sort_values(["condition", "protocol_id", "seed"])
    if len(frame) != EXPECTED_RECEIVERS * len(ADDENDUM_SEEDS) * 3:
        raise RuntimeError("query-coupling record count mismatch")
    frame.to_csv(output_root / "query_coupling_receiver_seed_results.csv", index=False, lineterminator="\n")
    return frame


def run_t3a_support_budget_diagnostic(
    converted_root: str | Path,
    split_root: str | Path,
    run_root: str | Path,
    output_root: str | Path,
    *,
    v2_root: str | Path,
) -> pd.DataFrame:
    """Evaluate frozen T3A at all preregistered banks on P2's common queries."""

    output_root = require_posthoc_output_path(output_root, v2_root)
    output_root.mkdir(parents=True, exist_ok=True)
    verify_frozen_v2_inputs(v2_root, converted_root)
    split_root, run_root = Path(split_root), Path(run_root)
    original = ManyRxBundle.load(converted_root)
    device = _device()
    rows: list[dict[str, Any]] = []
    for record_path in _record_paths(run_root, "T3A"):
        record = _load_record(record_path)
        protocol, seed = str(record["protocol_id"]), int(record["config"]["seed"])
        record_out = output_root / "records" / "support_budget_t3a" / f"{protocol}__s{seed}.json"
        if record_out.exists():
            rows.extend(json.loads(record_out.read_text(encoding="utf-8"))["rows"])
            continue
        bundle = remap_bundle_to_split_targets(original, split_root / protocol / "split_summary.json")
        split_indices = bundle.split_indices(split_root / protocol / "split_manifest.csv")
        test = split_indices["test"]
        receiver = str(bundle.receiver_ids[test[0]])
        maximum = freeze_support_query(test, bundle.sample_ids, bundle.receiver_ids, receiver_id=receiver, support_budget=256, seed=seed)
        query = np.asarray(maximum.query_indices, dtype=np.int64)
        config = RunConfig(protocol, "T3A", seed)
        train_receivers = len(set(bundle.receiver_ids[split_indices["train"]].astype(str)))
        model, _, _ = _load_base_model(config, run_root, len(bundle.transmitter_ids), train_receivers, device)
        if not isinstance(model, IndependentClassifier):
            raise TypeError("T3A base checkpoint is not an independent classifier")
        support_embeddings = _encode_backbone(model, bundle, maximum.support_indices, device, 1024)
        query_embeddings = torch.from_numpy(_encode_backbone(model, bundle, query, device, 1024)).to(device)
        selected = record.get("selected_t3a_filter_source_validation_only")
        if selected is None:
            raise RuntimeError("frozen T3A record lacks source-only filter selection")
        result_rows: list[dict[str, Any]] = []
        for budget in SUPPORT_BUDGETS:
            support = torch.from_numpy(support_embeddings[:budget]).to(device)
            probabilities = torch.softmax(T3AAdapter(model.classifier, int(selected)).predict(query_embeddings, support), dim=-1).cpu().numpy()
            result_rows.append({
                "protocol_id": protocol,
                "receiver_id": receiver,
                "seed": seed,
                "method": "T3A",
                "support_budget": budget,
                "common_query_budget": 256,
                "query_count": len(query),
                "filter_k_source_validation_only": int(selected),
                "evidence_category": EvidenceCategory.LABEL_FREE_CONTROL.value,
                **classification_metrics(bundle.labels[query], probabilities),
            })
        atomic_json({"status": "COMPLETE", "retrained": False, "rows": result_rows}, record_out)
        rows.extend(result_rows)
    frame = pd.DataFrame(rows).sort_values(["support_budget", "protocol_id", "seed"])
    expected = EXPECTED_RECEIVERS * len(ADDENDUM_SEEDS) * len(SUPPORT_BUDGETS)
    if len(frame) != expected:
        raise RuntimeError(f"T3A support-budget rows {len(frame)} != {expected}")
    frame.to_csv(output_root / "t3a_support_budget_receiver_seed_results.csv", index=False, lineterminator="\n")
    return frame


def audit_equalized_intersection(
    raw_root: str | Path,
    equalized_a_root: str | Path,
    equalized_b_root: str | Path,
    split_root: str | Path,
    destination: str | Path,
) -> dict[str, Any]:
    """Audit opaque-ID intersection before any equalized model run."""

    raw = ManyRxBundle.load(raw_root)
    equal_a = ManyRxBundle.load(equalized_a_root)
    equal_b = ManyRxBundle.load(equalized_b_root)
    raw_ids, a_ids, b_ids = set(raw.sample_ids.astype(str)), set(equal_a.sample_ids.astype(str)), set(equal_b.sample_ids.astype(str))
    common = raw_ids & a_ids & b_ids
    if a_ids != b_ids:
        pass_agreement = False
    else:
        pass_agreement = True
    per_receiver: list[dict[str, Any]] = []
    class_values: set[str] = set()
    minimum_coverage = 1.0
    all_support = True
    split_root = Path(split_root)
    for protocol_dir in sorted(split_root.glob("receiver_loso_*")):
        summary = json.loads((protocol_dir / "split_summary.json").read_text(encoding="utf-8"))
        bundle = remap_bundle_to_split_targets(raw, protocol_dir / "split_summary.json")
        test = bundle.split_indices(protocol_dir / "split_manifest.csv")["test"]
        receiver = str(summary["assignment_metadata"]["test_receiver"])
        test_common = np.asarray([index for index in test if str(bundle.sample_ids[index]) in common], dtype=np.int64)
        coverage = len(test_common) / len(test) if len(test) else 0.0
        minimum_coverage = min(minimum_coverage, coverage)
        support_ok = len(test_common) > PRIMARY_SUPPORT_BUDGET
        all_support &= support_ok
        class_values.update(str(bundle.transmitter_ids[int(label)]) for label in np.unique(bundle.labels[test_common]) if int(label) >= 0)
        per_receiver.append({"protocol_id": protocol_dir.name, "receiver_id": receiver, "raw_test_count": len(test), "intersection_test_count": len(test_common), "coverage": coverage, "support_128_feasible": support_ok})
    eligible = pass_agreement and len(per_receiver) == 32 and len(class_values) == 6 and minimum_coverage >= 0.80 and all_support
    payload = {
        "status": "PASS" if eligible else "INELIGIBLE",
        "diagnostic_authorized": eligible,
        "raw_count": len(raw_ids),
        "equalized_a_count": len(a_ids),
        "equalized_b_count": len(b_ids),
        "intersection_count": len(common),
        "raw_only_count": len(raw_ids - common),
        "equalized_a_only_count": len(a_ids - raw_ids),
        "equalized_b_only_count": len(b_ids - raw_ids),
        "equalized_pass_ids_identical": pass_agreement,
        "receiver_count": len(per_receiver),
        "class_count": len(class_values),
        "minimum_receiver_test_coverage": minimum_coverage,
        "all_receiver_support_128_feasible": all_support,
        "per_receiver": per_receiver,
        "raw_manifest_sha256": sha256_file(Path(raw_root) / "dataset_manifest.json"),
        "equalized_a_manifest_sha256": sha256_file(Path(equalized_a_root) / "dataset_manifest.json"),
        "equalized_b_manifest_sha256": sha256_file(Path(equalized_b_root) / "dataset_manifest.json"),
    }
    destination = Path(destination)
    if destination.exists():
        existing = json.loads(destination.read_text(encoding="utf-8"))
        if existing != payload:
            raise RuntimeError("equalized intersection audit is create-once and changed")
    else:
        atomic_json(payload, destination)
    return payload


def summarize_receiver_deltas(frame: pd.DataFrame, left: str, right: str) -> dict[str, Any]:
    """Average seeds in receiver, then summarize/cluster-bootstrap receivers."""

    required = {"receiver_id", "seed", "condition", "macro_f1"}
    if not required.issubset(frame.columns):
        raise ValueError(f"missing columns: {sorted(required - set(frame.columns))}")
    pivot = frame.pivot_table(index=["receiver_id", "seed"], columns="condition", values="macro_f1", aggfunc="first")
    if left not in pivot or right not in pivot or pivot[[left, right]].isna().any().any():
        raise ValueError("comparison is not fully paired")
    receiver = (pivot[left] - pivot[right]).groupby("receiver_id").mean()
    return {
        "comparison": f"{left}_MINUS_{right}",
        **descriptive_summary(receiver.to_numpy()),
        "positive_receivers": int((receiver > 0).sum()),
        "negative_receivers": int((receiver < 0).sum()),
        "bootstrap": receiver_bootstrap(receiver.to_numpy(), replicates=10_000, seed=20_260_903),
    }
