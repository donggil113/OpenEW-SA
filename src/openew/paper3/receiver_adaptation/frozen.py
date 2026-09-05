"""Read-only integrity gates for reuse of frozen WiSig V2 evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

EXPECTED_V2_RUNS = 2_080
EXPECTED_V2_ANALYSIS_MANIFEST_SHA256 = "10ecae25fec123be839b11ea9c44334e41877dfa1eb261665c4d437870172d43"
EXPECTED_ADDENDUM_MANIFEST_SHA256 = "62e9e7e3ee44a356f978841b3d599d6ece0d3e73bcb8c11a6bcc94672677c678"
EXPECTED_DATA_MANIFEST_SHA256 = "ffd98dcb8182435c1aaf416c3bb137e6f56f353811e7d1d7a6fc0cc4817ae4b6"
EXPECTED_RAW_ARCHIVE_SHA256 = "d2b23108c3f6f63a10ebbb149d7b08d6e1c1961cf5184926fbab452def3049de"
EXPECTED_METHODS = frozenset({"P0", "P0_WIDE", "DG_CORAL", "DG_GROUPDRO", "DG_DANN", "SOURCE_NORM", "P1", "P2", "P2_SHUFFLED", "P2_NULL", "P2_MISMATCHED_RX", "RX_NORM", "T3A"})


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class FrozenV2Audit:
    status: str
    run_count: int
    complete_count: int
    failed_count: int
    methods: tuple[str, ...]
    receivers: tuple[str, ...]
    seeds: tuple[int, ...]
    run_registry_sha256: str
    prediction_manifest_sha256: str
    checkpoint_manifest_sha256: str
    analysis_manifest_sha256: str
    addendum_manifest_sha256: str
    data_manifest_sha256: str
    raw_archive_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verify_frozen_v2(v2_root: str | Path, *, converted_root: str | Path, raw_archive: str | Path, addendum_root: str | Path) -> FrozenV2Audit:
    """Fully reconcile immutable V2 records without reading target metrics."""
    v2_root, converted_root = Path(v2_root), Path(converted_root)
    run_root = v2_root / "experiments" / "confirmatory_v2" / "runs"
    analysis_root = v2_root / "analysis" / "confirmatory_v2"
    records: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, str]] = []
    checkpoint_rows: list[dict[str, str]] = []
    for path in sorted(run_root.glob("*/run.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        if row.get("status") != "COMPLETE":
            raise RuntimeError(f"frozen V2 run is not COMPLETE: {path}")
        if row.get("held_out_metrics") is not None or row.get("target_labels_loaded_for_metrics") is not False:
            raise RuntimeError(f"run record violates target blinding: {path}")
        prediction = path.parent / "predictions_blind.npz"
        if not prediction.exists():
            raise FileNotFoundError(f"missing frozen prediction: {prediction}")
        prediction_sha = sha256_file(prediction)
        if prediction_sha != row.get("target_prediction_sha256"):
            raise RuntimeError(f"frozen prediction hash mismatch: {prediction}")
        prediction_rows.append({"run_id": str(row["run_id"]), "sha256": prediction_sha})
        checkpoint = path.parent / "checkpoint.pt"
        if checkpoint.exists():
            checkpoint_rows.append({"run_id": str(row["run_id"]), "sha256": sha256_file(checkpoint)})
        records.append({
            "run_id": str(row["run_id"]), "config_hash": str(row["config_hash"]),
            "split_sha256": str(row["split_sha256"]), "data_manifest_sha256": str(row["data_manifest_sha256"]),
            "git_sha": str(row["git_sha"]), "method": str(row["model_stage"]),
            "protocol": str(row["protocol_id"]), "seed": int(row["config"]["seed"]),
        })
    if len(records) != EXPECTED_V2_RUNS:
        raise RuntimeError(f"expected {EXPECTED_V2_RUNS} V2 runs, found {len(records)}")
    if len({row["config_hash"] for row in records}) != len(records):
        raise RuntimeError("duplicate frozen V2 config hash")
    methods = tuple(sorted({row["method"] for row in records}))
    if set(methods) != EXPECTED_METHODS:
        raise RuntimeError(f"unexpected frozen method set: {methods}")
    protocols = sorted({row["protocol"] for row in records})
    if protocols != [f"receiver_loso_{index:02d}" for index in range(32)]:
        raise RuntimeError("frozen receiver protocol grid changed")
    analysis_sha = sha256_file(analysis_root / "analysis_manifest.json")
    addendum_sha = sha256_file(Path(addendum_root) / "analysis_manifest.json")
    data_sha = sha256_file(converted_root / "dataset_manifest.json")
    raw_sha = sha256_file(raw_archive)
    expected = ((analysis_sha, EXPECTED_V2_ANALYSIS_MANIFEST_SHA256), (addendum_sha, EXPECTED_ADDENDUM_MANIFEST_SHA256), (data_sha, EXPECTED_DATA_MANIFEST_SHA256), (raw_sha, EXPECTED_RAW_ARCHIVE_SHA256))
    if any(actual != wanted for actual, wanted in expected):
        raise RuntimeError("one or more frozen WiSig artifact hashes changed")
    import pandas as pd
    frame = pd.read_csv(analysis_root / "primary_receiver_averaged_results.csv", dtype={"receiver_id": "string"})
    receivers = tuple(sorted(str(value) for value in frame["receiver_id"].unique()))
    return FrozenV2Audit(
        "PASS", len(records), len(records), 0, methods, receivers,
        tuple(sorted({row["seed"] for row in records})), _canonical_hash(records),
        _canonical_hash(prediction_rows), _canonical_hash(checkpoint_rows), analysis_sha,
        addendum_sha, data_sha, raw_sha,
    )
