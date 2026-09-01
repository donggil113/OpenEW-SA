"""Frozen-artifact loading, Paper 1 holdouts, and source-only preprocessing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from openew.paper3.relational_audit import read_metadata_preserve_strings
from openew.training.splits import infer_jammer_type


TARGET_COLUMNS = {
    "jamshield": "abnormal_event_label",
    "deepsense": "occupancy_label",
    "electrosense": "situation_label",
}


@dataclass(frozen=True)
class SplitIndices:
    train: np.ndarray
    source_validation: np.ndarray
    heldout: np.ndarray
    partition_by_row: np.ndarray
    hashes: dict[str, str]


@dataclass
class FrozenArtifact:
    dataset: str
    artifact_dir: Path
    metadata: pd.DataFrame
    features: np.ndarray
    labels_json: dict[str, Any]
    label_column: str
    class_names: tuple[str, ...]

    def label_indices(self, indices: np.ndarray) -> np.ndarray:
        mapping = {value: index for index, value in enumerate(self.class_names)}
        values = self.metadata.iloc[np.asarray(indices, dtype=np.int64)][self.label_column].astype(str)
        missing = sorted(set(values) - set(mapping))
        if missing:
            raise ValueError(f"Unknown {self.dataset} target values: {missing}")
        return values.map(mapping).to_numpy(dtype=np.int64)


@dataclass(frozen=True)
class Standardizer:
    mean: np.ndarray
    scale: np.ndarray
    sample_shape: tuple[int, ...]

    def transform(self, values: np.ndarray) -> np.ndarray:
        array = np.asarray(values, dtype=np.float32)
        flat = array.reshape(len(array), -1)
        transformed = (flat - self.mean) / self.scale
        return transformed.reshape((len(array), *self.sample_shape)).astype(np.float32, copy=False)

    def to_json(self) -> dict[str, Any]:
        return {
            "mean": self.mean.astype(float).tolist(),
            "scale": self.scale.astype(float).tolist(),
            "sample_shape": list(self.sample_shape),
        }


def load_frozen_artifact(dataset: str, artifact_dir: str | Path) -> FrozenArtifact:
    dataset_key = str(dataset).lower()
    if dataset_key not in TARGET_COLUMNS:
        raise ValueError(f"Unsupported dataset: {dataset}")
    root = Path(artifact_dir)
    metadata = read_metadata_preserve_strings(root / "metadata.csv")
    labels_json = json.loads((root / "labels.json").read_text(encoding="utf-8"))
    features = np.load(root / "features.npy", mmap_mode="r", allow_pickle=False)
    if len(metadata) != int(features.shape[0]):
        raise ValueError(f"Feature/metadata mismatch in {root}: {features.shape[0]} != {len(metadata)}")
    if dataset_key == "electrosense":
        metadata = _add_electrosense_source_date(metadata, labels_json)
    label_column = TARGET_COLUMNS[dataset_key]
    if label_column not in metadata:
        raise ValueError(f"Missing target column {label_column}: {root}")
    configured_names = labels_json.get("class_names") or []
    if isinstance(configured_names, dict):
        configured_names = configured_names.get(label_column, [])
    class_names = tuple(str(value) for value in configured_names)
    if not class_names:
        class_names = tuple(sorted(metadata[label_column].astype(str).unique()))
    if dataset_key == "deepsense" and any(len(value) != 4 for value in class_names):
        raise ValueError("DeepSense symbolic occupancy labels lost their four-character representation")
    return FrozenArtifact(
        dataset=dataset_key,
        artifact_dir=root,
        metadata=metadata,
        features=features,
        labels_json=labels_json,
        label_column=label_column,
        class_names=class_names,
    )


def _add_electrosense_source_date(
    metadata: pd.DataFrame, labels_json: dict[str, Any]
) -> pd.DataFrame:
    descriptors = labels_json.get("source_files", [])
    expected = sum(int(item.get("row_count", 0)) for item in descriptors)
    if expected != len(metadata):
        raise ValueError(f"ElectroSense source descriptor rows {expected} != metadata rows {len(metadata)}")
    values: list[str] = []
    for descriptor in descriptors:
        values.extend([str(descriptor.get("date_id", ""))] * int(descriptor["row_count"]))
    if len(values) != len(metadata) or any(not value for value in values):
        raise ValueError("ElectroSense source_date_id reconstruction is incomplete")
    frame = metadata.copy()
    frame["source_date_id"] = pd.Series(values, dtype="string")
    return frame


def build_frozen_split(
    artifact: FrozenArtifact,
    protocol_name: str,
    protocol: dict[str, Any],
    source_validation_fraction: float,
    split_seed: int,
) -> SplitIndices:
    metadata = artifact.metadata
    strategy = protocol["split_strategy"]
    domains = metadata["domain_id"].astype(str)
    if strategy == "domain_holdout":
        heldout_values = {str(value) for value in protocol.get("holdout_domains", [])}
        heldout_values.update(str(value) for value in protocol.get("holdout_benign_domains", []))
        heldout_mask = domains.isin(heldout_values).to_numpy()
    elif strategy == "jammer_type_holdout":
        jammer_types = {str(value).lower() for value in protocol.get("holdout_jammer_types", [])}
        benign = {str(value) for value in protocol.get("holdout_benign_domains", [])}
        heldout_mask = (
            metadata["domain_id"].map(infer_jammer_type).isin(jammer_types)
            | domains.isin(benign)
        ).to_numpy()
    else:
        raise ValueError(f"Unsupported frozen split strategy: {strategy}")
    heldout = np.flatnonzero(heldout_mask).astype(np.int64)
    source = np.flatnonzero(~heldout_mask).astype(np.int64)
    if not len(source) or not len(heldout):
        raise ValueError(f"Empty source or held-out partition for {protocol_name}")

    labels = artifact.metadata.iloc[source][artifact.label_column].astype(str).to_numpy()
    source_domains = domains.iloc[source].to_numpy(dtype=str)
    validation_local: list[int] = []
    strata = sorted(set(zip(source_domains.tolist(), labels.tolist())))
    sample_ids = metadata.iloc[source]["sample_id"].astype(str).to_numpy()
    for domain, label in strata:
        local = np.flatnonzero((source_domains == domain) & (labels == label))
        if len(local) < 2:
            continue
        count = max(1, min(len(local) - 1, int(round(len(local) * source_validation_fraction))))
        ordered = sorted(
            local.tolist(),
            key=lambda position: _stable_digest(
                artifact.dataset,
                protocol_name,
                domain,
                label,
                sample_ids[position],
                str(split_seed),
            ),
        )
        validation_local.extend(ordered[:count])
    validation_local_array = np.asarray(sorted(set(validation_local)), dtype=np.int64)
    source_validation = source[validation_local_array]
    train_mask = np.ones(len(source), dtype=bool)
    train_mask[validation_local_array] = False
    train = source[train_mask]
    if not len(train) or not len(source_validation):
        raise ValueError(f"Source-only validation split failed for {protocol_name}")

    partition = np.full(len(metadata), "unassigned", dtype="U20")
    partition[train] = "train"
    partition[source_validation] = "source_validation"
    partition[heldout] = "heldout"
    if np.any(partition == "unassigned"):
        raise ValueError(f"Split is not exhaustive for {protocol_name}")
    _assert_disjoint(train, source_validation, heldout)
    hashes = {
        "train": _indices_hash(metadata, train),
        "source_validation": _indices_hash(metadata, source_validation),
        "heldout": _indices_hash(metadata, heldout),
    }
    hashes["combined"] = _stable_digest(*(f"{key}:{hashes[key]}" for key in sorted(hashes)))
    return SplitIndices(train, source_validation, heldout, partition, hashes)


def _assert_disjoint(*arrays: np.ndarray) -> None:
    sets = [set(np.asarray(array, dtype=np.int64).tolist()) for array in arrays]
    for left in range(len(sets)):
        for right in range(left + 1, len(sets)):
            if sets[left] & sets[right]:
                raise ValueError(f"Split contamination between partitions {left} and {right}")


def _indices_hash(metadata: pd.DataFrame, indices: np.ndarray) -> str:
    digest = hashlib.sha256()
    for index in np.asarray(indices, dtype=np.int64):
        digest.update(str(int(index)).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(metadata.iloc[index]["sample_id"]).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _stable_digest(*parts: str) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def fit_standardizer(features: np.ndarray, train_indices: np.ndarray, chunk_size: int = 2048) -> Standardizer:
    sample_shape = tuple(int(value) for value in features.shape[1:])
    width = int(np.prod(sample_shape))
    total = np.zeros(width, dtype=np.float64)
    squared = np.zeros(width, dtype=np.float64)
    count = 0
    indices = np.asarray(train_indices, dtype=np.int64)
    for start in range(0, len(indices), chunk_size):
        block = np.asarray(features[indices[start : start + chunk_size]], dtype=np.float32).reshape(-1, width)
        total += block.sum(axis=0, dtype=np.float64)
        squared += np.square(block, dtype=np.float64).sum(axis=0, dtype=np.float64)
        count += len(block)
    if count == 0:
        raise ValueError("Cannot fit preprocessing on an empty training partition")
    mean = total / count
    variance = np.maximum(squared / count - np.square(mean), 0.0)
    scale = np.sqrt(variance)
    scale[scale == 0.0] = 1.0
    return Standardizer(mean.astype(np.float32), scale.astype(np.float32), sample_shape)


def feature_tensor(
    artifact: FrozenArtifact,
    indices: np.ndarray,
    standardizer: Standardizer,
    device: torch.device,
) -> torch.Tensor:
    transformed = standardizer.transform(np.asarray(artifact.features[np.asarray(indices, dtype=np.int64)]))
    return torch.as_tensor(transformed, dtype=torch.float32, device=device)


def balanced_class_weights(artifact: FrozenArtifact, train_indices: np.ndarray) -> torch.Tensor:
    labels = artifact.label_indices(train_indices)
    counts = np.bincount(labels, minlength=len(artifact.class_names)).astype(np.float64)
    weights = np.zeros(len(counts), dtype=np.float32)
    populated = counts > 0
    weights[populated] = len(labels) / (len(counts) * counts[populated])
    return torch.as_tensor(weights, dtype=torch.float32)
