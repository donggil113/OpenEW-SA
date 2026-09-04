"""Post-hoc composition stresses for P2, T3A, and RX-NORM."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
import torch

from openew.paper3.wisig.checkpoint import atomic_json
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig.metrics import classification_metrics
from openew.paper3.wisig_v2.controls import oracle_support_for_query, transmitter_pure_oracle_pool
from openew.paper3.wisig_v2.models import IndependentClassifier, T3AAdapter
from openew.paper3.wisig_v2.runner import (
    RunConfig,
    _encode_backbone,
    _independent_probabilities,
    _load_base_model,
    _stream_statistics,
    remap_bundle_to_split_targets,
)
from openew.paper3.wisig_v2.support import freeze_support_query

from .contracts import ADDENDUM_SEEDS, EXPECTED_RECEIVERS, EvidenceCategory, require_posthoc_output_path, verify_frozen_v2_inputs
from .inference import _load_record, _record_paths

ORACLE_CONDITIONS = ("SAME_CLASS_EXCLUDED_ORACLE", "SAME_CLASS_ONLY_ORACLE", "TRANSMITTER_PURE_ORACLE")


def oracle_supports_by_label(
    support: Sequence[int],
    labels: np.ndarray,
    sample_ids: np.ndarray,
    *,
    seed: int,
    k: int = 32,
) -> dict[str, dict[int, tuple[int, ...]]]:
    """Construct declared label-dependent audit supports, never deployable supports."""

    classes = sorted(set(int(labels[index]) for index in support))
    pure = transmitter_pure_oracle_pool(support, labels, sample_ids, budget=k, seed=seed)
    return {
        "SAME_CLASS_EXCLUDED_ORACLE": {label: oracle_support_for_query(support, labels, query_label=label, mode="same_class_excluded", sample_ids=sample_ids, seed=seed, k=k) for label in classes},
        "SAME_CLASS_ONLY_ORACLE": {label: oracle_support_for_query(support, labels, query_label=label, mode="same_class_only", sample_ids=sample_ids, seed=seed, k=k) for label in classes},
        "TRANSMITTER_PURE_ORACLE": {label: tuple(pure[:k]) for label in classes},
    }


def _condition_probabilities_t3a(
    model: IndependentClassifier,
    bundle: ManyRxBundle,
    query: np.ndarray,
    supports: dict[int, tuple[int, ...]],
    filter_k: int,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    result = np.full((len(query), len(bundle.transmitter_ids)), np.nan, dtype=np.float32)
    evaluable = np.zeros(len(query), dtype=bool)
    query_embeddings = _encode_backbone(model, bundle, query, device, 1024)
    for label, support in supports.items():
        rows = np.flatnonzero(bundle.labels[query] == label)
        if not len(rows) or not support:
            continue
        support_embeddings = torch.from_numpy(_encode_backbone(model, bundle, support, device, 1024)).to(device)
        query_tensor = torch.from_numpy(query_embeddings[rows]).to(device)
        logits = T3AAdapter(model.classifier, filter_k).predict(query_tensor, support_embeddings)
        result[rows] = torch.softmax(logits, dim=-1).cpu().numpy()
        evaluable[rows] = True
    return result, evaluable


def _condition_probabilities_rxnorm(
    model: IndependentClassifier,
    bundle: ManyRxBundle,
    query: np.ndarray,
    supports: dict[int, tuple[int, ...]],
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    result = np.full((len(query), len(bundle.transmitter_ids)), np.nan, dtype=np.float32)
    evaluable = np.zeros(len(query), dtype=bool)
    for label, support in supports.items():
        rows = np.flatnonzero(bundle.labels[query] == label)
        if not len(rows) or not support:
            continue
        stats = _stream_statistics(bundle.features, np.asarray(support, dtype=np.int64))
        result[rows] = _independent_probabilities(model, bundle, query[rows], device, 1024, stats)
        evaluable[rows] = True
    return result, evaluable


def run_tta_composition_diagnostic(
    converted_root: str | Path,
    split_root: str | Path,
    run_root: str | Path,
    output_root: str | Path,
    *,
    v2_root: str | Path,
) -> pd.DataFrame:
    """Evaluate oracle composition for same-information T3A and RX-NORM."""

    output_root = require_posthoc_output_path(output_root, v2_root)
    output_root.mkdir(parents=True, exist_ok=True)
    verify_frozen_v2_inputs(v2_root, converted_root)
    original = ManyRxBundle.load(converted_root)
    split_root, run_root = Path(split_root), Path(run_root)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows: list[dict[str, Any]] = []
    for stage in ("T3A", "RX_NORM"):
        for record_path in _record_paths(run_root, stage):
            record = _load_record(record_path)
            protocol, seed = str(record["protocol_id"]), int(record["config"]["seed"])
            record_out = output_root / "records" / "composition_tta" / f"{stage.lower()}__{protocol}__s{seed}.json"
            if record_out.exists():
                rows.extend(json.loads(record_out.read_text(encoding="utf-8"))["rows"])
                continue
            bundle = remap_bundle_to_split_targets(original, split_root / protocol / "split_summary.json")
            split_indices = bundle.split_indices(split_root / protocol / "split_manifest.csv")
            test = split_indices["test"]
            receiver = str(bundle.receiver_ids[test[0]])
            split = freeze_support_query(test, bundle.sample_ids, bundle.receiver_ids, receiver_id=receiver, support_budget=128, seed=seed)
            query = np.asarray(split.query_indices, dtype=np.int64)
            support_sets = oracle_supports_by_label(split.support_indices, bundle.labels, bundle.sample_ids, seed=seed)
            train_receivers = len(set(bundle.receiver_ids[split_indices["train"]].astype(str)))
            model, _, _ = _load_base_model(RunConfig(protocol, stage, seed), run_root, len(bundle.transmitter_ids), train_receivers, device)
            if not isinstance(model, IndependentClassifier):
                raise TypeError(f"{stage} base model is not independent")
            result_rows: list[dict[str, Any]] = []
            for condition in ORACLE_CONDITIONS:
                supports = support_sets[condition]
                if stage == "T3A":
                    selected = record.get("selected_t3a_filter_source_validation_only")
                    if selected is None:
                        raise RuntimeError("T3A record lacks source-only filter K")
                    probabilities, evaluable = _condition_probabilities_t3a(model, bundle, query, supports, int(selected), device)
                else:
                    probabilities, evaluable = _condition_probabilities_rxnorm(model, bundle, query, supports, device)
                if not evaluable.any() or not np.isfinite(probabilities[evaluable]).all():
                    raise RuntimeError(f"{stage} {condition} has no finite evaluable query")
                peer_counts = [len(supports[int(label)]) for label in bundle.labels[query][evaluable]]
                result_rows.append({
                    "protocol_id": protocol,
                    "receiver_id": receiver,
                    "seed": seed,
                    "method": stage.replace("_", "-"),
                    "condition": condition,
                    "evidence_category": EvidenceCategory.ORACLE_DIAGNOSTIC.value,
                    "query_count": len(query),
                    "evaluable_query_count": int(evaluable.sum()),
                    "mean_peer_count": float(np.mean(peer_counts)),
                    "labels_used_to_construct_support": True,
                    **classification_metrics(bundle.labels[query][evaluable], probabilities[evaluable]),
                })
            atomic_json({"status": "COMPLETE", "retrained": False, "rows": result_rows}, record_out)
            rows.extend(result_rows)
    frame = pd.DataFrame(rows).sort_values(["method", "condition", "protocol_id", "seed"])
    expected = 2 * EXPECTED_RECEIVERS * len(ADDENDUM_SEEDS) * len(ORACLE_CONDITIONS)
    if len(frame) != expected:
        raise RuntimeError(f"composition rows {len(frame)} != {expected}")
    frame.to_csv(output_root / "tta_rxnorm_composition_receiver_seed_results.csv", index=False, lineterminator="\n")
    return frame
