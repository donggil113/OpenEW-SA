"""Deterministic field-level provenance records for the WiSig converter."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PARSER_VERSION = "openew-wisig-manyrx-converter/1.0.0"


def source_path_hash(path: str | Path) -> str:
    return hashlib.sha256(str(Path(path).resolve()).encode("utf-8")).hexdigest()


def public_field_provenance() -> dict[str, dict[str, Any]]:
    direct = {
        "source_type": "official_manyrx_compact_pickle",
        "parser_version": PARSER_VERSION,
        "confidence": "VERIFIED",
    }
    return {
        "sample_id": {**direct, "extraction_method": "opaque_sha256_from_internal_source_record"},
        "receiver_id": {**direct, "extraction_method": "official_rx_list_index"},
        "day_id": {**direct, "extraction_method": "official_capture_date_list_index", "eligibility": "SPLIT_ONLY"},
        "packet_index": {**direct, "extraction_method": "row_index_within_target_nested_compact_array", "eligibility": "AUDIT_ONLY"},
        "source_record_index": {**direct, "extraction_method": "deterministic_converter_order", "eligibility": "AUDIT_ONLY"},
        "center_frequency_hz": {**direct, "extraction_method": "official_dataset_constant", "value": 2_462_000_000},
        "bandwidth_hz": {**direct, "extraction_method": "official_wifi_channel_bandwidth", "value": 20_000_000},
        "sample_rate_hz": {**direct, "extraction_method": "official_capture_rate", "value": 25_000_000},
        "data_quality_flags": {**direct, "extraction_method": "converter_finite_shape_checks"},
        "transmitter_id": {
            **direct,
            "extraction_method": "official_tx_list_index",
            "eligibility": "ANNOTATION_ONLY",
            "target": True,
        },
    }


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")
