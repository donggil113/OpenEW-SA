"""Prediction blinding and one-time receiver-level unblinding."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .hashing import canonical_json_bytes, sha256_file


FORBIDDEN_BLIND_KEYS = frozenset({"label", "labels", "target", "true_label", "true_transmitter_index", "transmitter_id", "macro_f1", "accuracy", "balanced_accuracy", "ece"})


def validate_blind_prediction_payload(payload: Mapping[str, Any]) -> None:
    forbidden = sorted(set(payload) & FORBIDDEN_BLIND_KEYS)
    if forbidden:
        raise ValueError(f"blind prediction payload leaks target information: {forbidden}")
    required = {"sample_ids", "probabilities"}
    if not required.issubset(payload):
        raise ValueError(f"blind prediction payload missing {sorted(required - set(payload))}")
    sample_ids = np.asarray(payload["sample_ids"])
    probabilities = np.asarray(payload["probabilities"])
    if probabilities.ndim != 2 or sample_ids.ndim != 1 or len(sample_ids) != len(probabilities):
        raise ValueError("blind prediction dimensions are inconsistent")
    if not np.isfinite(probabilities).all():
        raise FloatingPointError("blind predictions contain non-finite values")


def write_blind_predictions(path: str | Path, sample_ids: np.ndarray, probabilities: np.ndarray) -> str:
    payload = {"sample_ids": np.asarray(sample_ids, dtype="U64"), "probabilities": np.asarray(probabilities, dtype=np.float32)}
    validate_blind_prediction_payload(payload)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp.npz")
    np.savez_compressed(temporary, **payload)
    os.replace(temporary, path)
    return sha256_file(path)


def read_blind_predictions(path: str | Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        payload = {key: archive[key] for key in archive.files}
    validate_blind_prediction_payload(payload)
    return payload


def create_unblinding_manifest(
    destination: str | Path,
    *,
    preregistration_sha: str,
    plan_sha: str,
    prediction_hashes: Mapping[str, str],
    completed_primary_runs: int,
    expected_primary_runs: int,
) -> dict[str, Any]:
    if completed_primary_runs != expected_primary_runs:
        raise RuntimeError("cannot unblind before all preregistered primary runs complete")
    payload = {
        "schema_version": 1,
        "status": "UNBLINDED_ONCE",
        "unblinding_time_utc": datetime.now(timezone.utc).isoformat(),
        "preregistration_sha256": preregistration_sha,
        "frozen_plan_sha256": plan_sha,
        "completed_primary_runs": completed_primary_runs,
        "expected_primary_runs": expected_primary_runs,
        "prediction_manifest_sha256": __import__("hashlib").sha256(canonical_json_bytes(dict(sorted(prediction_hashes.items())))).hexdigest(),
    }
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError("unblinding manifest already exists; V2 permits one unblinding event")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(canonical_json_bytes(payload))
    return payload
