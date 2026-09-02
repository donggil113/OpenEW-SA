"""Deterministic, shard-bounded conversion of the official WiSig ManyRx object."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import resource
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import numpy as np

from .archive import sha256_file, write_json_atomic
from .ids import opaque_sample_id
from .provenance import PARSER_VERSION, canonical_json_bytes, public_field_provenance, source_path_hash
from .restricted_loader import restricted_load
from .schema import ACQUISITION_FIELDS, ANNOTATION_FIELDS, AcquisitionRow, AnnotationRow


REQUIRED_KEYS = frozenset({"tx_list", "rx_list", "capture_date_list", "equalized_list", "max_sig", "data"})


@dataclass(frozen=True)
class ConversionConfig:
    equalized_index: int = 0
    shard_size: int = 8192
    output_dtype: str = "float32"
    expected_signal_length: int = 256
    expected_iq_channels: int = 2
    center_frequency_hz: int = 2_462_000_000
    bandwidth_hz: int = 20_000_000
    sample_rate_hz: int = 25_000_000

    def validate(self) -> "ConversionConfig":
        if self.equalized_index not in (0, 1):
            raise ValueError("equalized_index must be 0 or 1")
        if self.shard_size <= 0:
            raise ValueError("shard_size must be positive")
        if self.output_dtype != "float32":
            raise ValueError("the frozen v1 converter requires float32 output")
        if self.expected_signal_length <= 0 or self.expected_iq_channels != 2:
            raise ValueError("invalid expected signal geometry")
        return self

    def deterministic_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "equalized_index": self.equalized_index,
            "shard_size": self.shard_size,
            "output_dtype": self.output_dtype,
            "expected_signal_length": self.expected_signal_length,
            "expected_iq_channels": self.expected_iq_channels,
            "center_frequency_hz": self.center_frequency_hz,
            "bandwidth_hz": self.bandwidth_hz,
            "sample_rate_hz": self.sample_rate_hz,
            "parser_version": PARSER_VERSION,
        }

    @property
    def config_hash(self) -> str:
        return hashlib.sha256(canonical_json_bytes(self.deterministic_dict())).hexdigest()


def validate_compact_structure(dataset: object, config: ConversionConfig) -> dict[str, Any]:
    if not isinstance(dataset, dict):
        raise ValueError("ManyRx root must be a dictionary")
    missing = REQUIRED_KEYS - set(dataset)
    extra = set(dataset) - REQUIRED_KEYS
    if missing or extra:
        raise ValueError(f"unexpected ManyRx keys: missing={sorted(missing)}, extra={sorted(extra)}")
    for key in ("tx_list", "rx_list", "capture_date_list", "equalized_list"):
        if not isinstance(dataset[key], list) or not dataset[key]:
            raise ValueError(f"{key} must be a non-empty list")
        if key != "equalized_list" and not all(isinstance(value, str) for value in dataset[key]):
            raise ValueError(f"{key} identifiers must remain exact strings")
        if len(set(dataset[key])) != len(dataset[key]):
            raise ValueError(f"{key} contains duplicates")
    if any(isinstance(value, bool) or not isinstance(value, (int, str)) for value in dataset["equalized_list"]):
        raise ValueError("equalized_list must contain only exact integer/string variant identifiers")
    if config.equalized_index >= len(dataset["equalized_list"]):
        raise ValueError("selected equalized_index is unavailable")
    data = dataset["data"]
    if not isinstance(data, list) or len(data) != len(dataset["tx_list"]):
        raise ValueError("data transmitter axis does not match tx_list")
    cell_count = 0
    packet_count = 0
    nonfinite_count = 0
    shapes: set[tuple[int, ...]] = set()
    dtypes: set[str] = set()
    for tx_i, by_rx in enumerate(data):
        if not isinstance(by_rx, list) or len(by_rx) != len(dataset["rx_list"]):
            raise ValueError(f"data receiver axis mismatch at transmitter index {tx_i}")
        for rx_i, by_day in enumerate(by_rx):
            if not isinstance(by_day, list) or len(by_day) != len(dataset["capture_date_list"]):
                raise ValueError(f"data day axis mismatch at tx={tx_i}, rx={rx_i}")
            for day_i, by_equalization in enumerate(by_day):
                if not isinstance(by_equalization, list) or len(by_equalization) != len(dataset["equalized_list"]):
                    raise ValueError(f"data equalization axis mismatch at tx={tx_i}, rx={rx_i}, day={day_i}")
                array = by_equalization[config.equalized_index]
                if not isinstance(array, np.ndarray) or array.dtype.hasobject:
                    raise ValueError("signal cells must be non-object NumPy arrays")
                if array.ndim != 3 or tuple(array.shape[1:]) != (
                    config.expected_signal_length,
                    config.expected_iq_channels,
                ):
                    raise ValueError(f"unexpected signal cell shape {array.shape}")
                cell_count += 1
                packet_count += len(array)
                nonfinite_count += int(array.size - np.isfinite(array).sum())
                shapes.add(tuple(int(x) for x in array.shape))
                dtypes.add(str(array.dtype))
    return {
        "transmitter_count": len(dataset["tx_list"]),
        "receiver_count": len(dataset["rx_list"]),
        "day_count": len(dataset["capture_date_list"]),
        "equalization_variant_count": len(dataset["equalized_list"]),
        "selected_equalized_value": dataset["equalized_list"][config.equalized_index],
        "cell_count": cell_count,
        "packet_count": packet_count,
        "nonfinite_value_count": nonfinite_count,
        "cell_shapes": [list(shape) for shape in sorted(shapes)],
        "source_dtypes": sorted(dtypes),
    }


def iter_records(dataset: dict[str, Any], config: ConversionConfig) -> Iterator[tuple[np.ndarray, dict[str, Any], dict[str, Any], dict[str, Any]]]:
    record_index = 0
    for tx_i, transmitter_id in enumerate(dataset["tx_list"]):
        for rx_i, receiver_id in enumerate(dataset["rx_list"]):
            for day_i, day_id in enumerate(dataset["capture_date_list"]):
                array = dataset["data"][tx_i][rx_i][day_i][config.equalized_index]
                for packet_index in range(len(array)):
                    internal_identity = {
                        "day_index": day_i,
                        "equalized_index": config.equalized_index,
                        "packet_index": packet_index,
                        "receiver_index": rx_i,
                        "transmitter_index": tx_i,
                    }
                    sample_id = opaque_sample_id(internal_identity)
                    acquisition = {
                        "sample_id": sample_id,
                        "receiver_id": receiver_id,
                        "day_id": day_id,
                        "packet_index": packet_index,
                        "source_record_index": record_index,
                        "center_frequency_hz": config.center_frequency_hz,
                        "bandwidth_hz": config.bandwidth_hz,
                        "sample_rate_hz": config.sample_rate_hz,
                        "data_quality_flags": "" if np.isfinite(array[packet_index]).all() else "NONFINITE_SOURCE",
                    }
                    annotation = {
                        "sample_id": sample_id,
                        "task_name": "transmitter_fingerprinting",
                        "transmitter_id": transmitter_id,
                    }
                    provenance = {
                        "sample_id": sample_id,
                        "source_path_hash": "SET_BY_CONVERTER",
                        "source_path_target_bearing": True,
                        "internal_source_identity": internal_identity,
                    }
                    yield np.asarray(array[packet_index], dtype=np.float32), acquisition, annotation, provenance
                    record_index += 1


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_shard(
    output_root: Path,
    shard_index: int,
    features: list[np.ndarray],
    acquisitions: list[dict[str, Any]],
    annotations: list[dict[str, Any]],
    provenance: list[dict[str, Any]],
) -> dict[str, Any]:
    name = f"shard_{shard_index:05d}"
    final = output_root / "shards" / name
    temporary = output_root / "shards" / f".{name}.tmp"
    if final.exists():
        manifest = json.loads((final / "manifest.json").read_text(encoding="utf-8"))
        if int(manifest["row_count"]) != len(features):
            raise RuntimeError(f"existing shard row mismatch: {final}")
        return manifest
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir(parents=True)
    feature_name = "features.npy"
    acquisition_name = "acquisition_metadata.csv"
    annotation_name = "annotations.csv"
    provenance_name = "restricted_provenance.jsonl"
    for index, row in enumerate(acquisitions):
        row["feature_shard"] = name
        row["feature_row"] = index
        AcquisitionRow(**row).validate()
    for row in annotations:
        AnnotationRow(**row).validate()
    with (temporary / feature_name).open("wb") as stream:
        np.save(stream, np.stack(features).astype(np.float32, copy=False), allow_pickle=False)
    _write_csv(temporary / acquisition_name, ACQUISITION_FIELDS, acquisitions)
    _write_csv(temporary / annotation_name, ANNOTATION_FIELDS, annotations)
    with (temporary / provenance_name).open("w", encoding="utf-8", newline="\n") as stream:
        for row in provenance:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n")
    hashes = {
        filename: sha256_file(temporary / filename)
        for filename in (feature_name, acquisition_name, annotation_name, provenance_name)
    }
    manifest = {
        "schema_version": 1,
        "name": name,
        "row_count": len(features),
        "feature_shape": [len(features), *features[0].shape],
        "feature_dtype": "float32",
        "files": hashes,
    }
    (temporary / "manifest.json").write_bytes(canonical_json_bytes(manifest))
    os.replace(temporary, final)
    return manifest


def convert_manyrx(
    source_pickle: str | Path,
    output_root: str | Path,
    *,
    source_archive_sha256: str,
    config: ConversionConfig | None = None,
) -> dict[str, Any]:
    config = (config or ConversionConfig()).validate()
    source_pickle = Path(source_pickle).resolve()
    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "shards").mkdir(exist_ok=True)
    deterministic_manifest_path = output_root / "dataset_manifest.json"
    source_pickle_sha256 = sha256_file(source_pickle)
    if deterministic_manifest_path.exists():
        manifest = json.loads(deterministic_manifest_path.read_text(encoding="utf-8"))
        if (
            manifest.get("config_hash") == config.config_hash
            and manifest.get("source_pickle_sha256") == source_pickle_sha256
            and manifest.get("source_archive_sha256") == source_archive_sha256
            and manifest.get("status") == "COMPLETE"
        ):
            return manifest
        raise RuntimeError("existing conversion manifest is incompatible; refusing overwrite")

    start = time.perf_counter()
    started_utc = datetime.now(timezone.utc).isoformat()
    dataset = restricted_load(source_pickle)
    structure = validate_compact_structure(dataset, config)
    if structure["nonfinite_value_count"]:
        raise ValueError("source contains non-finite signal values")
    source_hash = source_path_hash(source_pickle)
    completed = []
    skip_rows = 0
    for directory in sorted((output_root / "shards").glob("shard_*")):
        existing = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        completed.append(existing)
        skip_rows += int(existing["row_count"])

    features: list[np.ndarray] = []
    acquisitions: list[dict[str, Any]] = []
    annotations: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    shard_index = len(completed)
    seen = 0
    for feature, acquisition, annotation, audit in iter_records(dataset, config):
        if seen < skip_rows:
            seen += 1
            continue
        audit["source_path_hash"] = source_hash
        features.append(feature)
        acquisitions.append(acquisition)
        annotations.append(annotation)
        provenance.append(audit)
        seen += 1
        if len(features) == config.shard_size:
            completed.append(_write_shard(output_root, shard_index, features, acquisitions, annotations, provenance))
            write_json_atomic(output_root / "conversion_state.json", {"committed_rows": seen, "next_shard": shard_index + 1})
            features, acquisitions, annotations, provenance = [], [], [], []
            shard_index += 1
    if features:
        completed.append(_write_shard(output_root, shard_index, features, acquisitions, annotations, provenance))
        write_json_atomic(output_root / "conversion_state.json", {"committed_rows": seen, "next_shard": shard_index + 1})

    if seen != structure["packet_count"]:
        raise RuntimeError(f"converted row mismatch: {seen} != {structure['packet_count']}")
    manifest = {
        "status": "COMPLETE",
        "schema_version": 1,
        "dataset": "WiSig ManyRx",
        "source_archive_sha256": source_archive_sha256,
        "source_pickle_sha256": source_pickle_sha256,
        "source_path_hash": source_hash,
        "source_path_target_bearing": True,
        "config": config.deterministic_dict(),
        "config_hash": config.config_hash,
        "structure": structure,
        "sample_count": seen,
        "shard_count": len(completed),
        "shards": completed,
        "acquisition_fields": list(ACQUISITION_FIELDS),
        "annotation_fields": list(ANNOTATION_FIELDS),
        "relation_whitelist": ["receiver_id"],
        "split_only_fields": ["day_id"],
        "temporal_status": "TARGET_NESTED_SEQUENCE",
        "field_provenance": public_field_provenance(),
    }
    deterministic_manifest_path.write_bytes(canonical_json_bytes(manifest))
    elapsed = time.perf_counter() - start
    runtime = {
        "status": "COMPLETE",
        "started_utc": started_utc,
        "ended_utc": datetime.now(timezone.utc).isoformat(),
        "wall_seconds": elapsed,
        "rows_per_second": seen / elapsed if elapsed else None,
        "source_load_requires_whole_object": True,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    write_json_atomic(output_root / "conversion_runtime.json", runtime)
    return manifest
