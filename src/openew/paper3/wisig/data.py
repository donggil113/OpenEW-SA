"""In-memory index over external sharded ManyRx features and frozen splits."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd

from .archive import sha256_file
from .validation import load_converted_tables


@dataclass
class ManyRxBundle:
    features: np.ndarray
    sample_ids: np.ndarray
    receiver_ids: np.ndarray
    day_ids: np.ndarray
    labels: np.ndarray
    transmitter_ids: tuple[str, ...]
    sample_index: dict[str, int]
    manifest_sha256: str

    @classmethod
    def load(cls, root: str | Path) -> "ManyRxBundle":
        root = Path(root)
        manifest_path = root / "dataset_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        acquisition, annotation = load_converted_tables(root)
        if not acquisition["sample_id"].equals(annotation["sample_id"]):
            annotation = acquisition[["sample_id"]].merge(annotation, on="sample_id", validate="one_to_one")
        arrays = [
            np.load(root / "shards" / shard["name"] / "features.npy", allow_pickle=False)
            for shard in manifest["shards"]
        ]
        features = np.concatenate(arrays, axis=0).astype(np.float32, copy=False)
        if len(features) != int(manifest["sample_count"]):
            raise ValueError("feature and manifest row counts differ")
        targets = tuple(sorted(str(value) for value in annotation["transmitter_id"].unique()))
        target_index = {value: index for index, value in enumerate(targets)}
        labels = annotation["transmitter_id"].map(target_index).to_numpy(dtype=np.int64)
        sample_ids = acquisition["sample_id"].astype(str).to_numpy()
        return cls(
            features=features,
            sample_ids=sample_ids,
            receiver_ids=acquisition["receiver_id"].astype(str).to_numpy(),
            day_ids=acquisition["day_id"].astype(str).to_numpy(),
            labels=labels,
            transmitter_ids=targets,
            sample_index={value: index for index, value in enumerate(sample_ids)},
            manifest_sha256=sha256_file(manifest_path),
        )

    def split_indices(self, split_manifest: str | Path) -> dict[str, np.ndarray]:
        frame = pd.read_csv(split_manifest, dtype={"sample_id": "string", "split": "string"}, keep_default_na=False)
        if frame["sample_id"].duplicated().any():
            raise ValueError("duplicate sample IDs in split manifest")
        unknown = [value for value in frame["sample_id"] if value not in self.sample_index]
        if unknown:
            raise ValueError(f"split manifest contains {len(unknown)} unknown sample IDs")
        result = {
            role: np.asarray([self.sample_index[str(value)] for value in group["sample_id"]], dtype=np.int64)
            for role, group in frame.groupby("split", sort=True)
        }
        if set(result) != {"train", "validation", "test"}:
            raise ValueError("split manifest must contain train, validation, and test")
        if sum(len(value) for value in result.values()) != len(frame):
            raise ValueError("split partition accounting failed")
        return result

    def receiver_codes(self, indices: np.ndarray) -> tuple[np.ndarray, tuple[str, ...]]:
        values = tuple(sorted(set(str(self.receiver_ids[index]) for index in indices)))
        mapping = {value: index for index, value in enumerate(values)}
        return np.asarray([mapping[str(self.receiver_ids[index])] for index in indices], dtype=np.int64), values


def normalize_packet_batch(features: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    """Frozen per-packet RMS scaling; no domain or target statistics are used."""

    values = np.asarray(features, dtype=np.float32)
    rms = np.sqrt(np.mean(np.square(values), axis=(1, 2), keepdims=True))
    return values / np.maximum(rms, epsilon)


def deterministic_batches(indices: np.ndarray, batch_size: int, seed: int, *, shuffle: bool) -> Iterator[np.ndarray]:
    values = np.asarray(indices, dtype=np.int64).copy()
    if shuffle:
        rng = np.random.default_rng(seed)
        rng.shuffle(values)
    for offset in range(0, len(values), batch_size):
        yield values[offset : offset + batch_size]
