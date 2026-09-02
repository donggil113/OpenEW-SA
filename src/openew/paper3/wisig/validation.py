"""Full-row QA, proxy diagnostics, and pass reproducibility checks for ManyRx."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import normalized_mutual_info_score

from .archive import sha256_file, write_json_atomic
from .schema import ACQUISITION_FIELDS, ANNOTATION_FIELDS


def load_converted_tables(root: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    root = Path(root)
    manifest = json.loads((root / "dataset_manifest.json").read_text(encoding="utf-8"))
    acquisitions: list[pd.DataFrame] = []
    annotations: list[pd.DataFrame] = []
    string_acquisition = {name: "string" for name in ("sample_id", "receiver_id", "day_id", "data_quality_flags", "feature_shard")}
    string_annotation = {name: "string" for name in ANNOTATION_FIELDS}
    for shard in manifest["shards"]:
        directory = root / "shards" / shard["name"]
        acquisitions.append(pd.read_csv(directory / "acquisition_metadata.csv", dtype=string_acquisition, keep_default_na=False))
        annotations.append(pd.read_csv(directory / "annotations.csv", dtype=string_annotation, keep_default_na=False))
    acquisition = pd.concat(acquisitions, ignore_index=True)
    annotation = pd.concat(annotations, ignore_index=True)
    return acquisition, annotation


def compare_deterministic_passes(left: str | Path, right: str | Path) -> dict[str, Any]:
    excluded = frozenset({"conversion_runtime.json", "conversion_state.json"})
    def inventory(root: Path) -> dict[str, tuple[int, str]]:
        return {
            path.relative_to(root).as_posix(): (path.stat().st_size, sha256_file(path))
            for path in sorted(root.rglob("*"))
            if path.is_file() and path.name not in excluded
        }
    left_path, right_path = Path(left), Path(right)
    a, b = inventory(left_path), inventory(right_path)
    mismatches = sorted(key for key in a.keys() | b.keys() if a.get(key) != b.get(key))
    return {
        "left_file_count": len(a),
        "right_file_count": len(b),
        "relative_paths_equal": set(a) == set(b),
        "byte_identical": not mismatches,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "excluded_nondeterministic_runtime_files": sorted(excluded),
    }


def run_sample_level_qa(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    manifest = json.loads((root / "dataset_manifest.json").read_text(encoding="utf-8"))
    acquisition, annotation = load_converted_tables(root)
    expected = int(manifest["sample_count"])
    feature_rows = 0
    nonfinite = 0
    wrong_shape = 0
    hash_mismatches: list[str] = []
    expected_shape = (
        int(manifest["config"]["expected_signal_length"]),
        int(manifest["config"]["expected_iq_channels"]),
    )
    for shard in manifest["shards"]:
        directory = root / "shards" / shard["name"]
        for filename, expected_hash in shard["files"].items():
            if sha256_file(directory / filename) != expected_hash:
                hash_mismatches.append(f"{shard['name']}/{filename}")
        features = np.load(directory / "features.npy", mmap_mode="r", allow_pickle=False)
        feature_rows += len(features)
        wrong_shape += int(tuple(features.shape[1:]) != expected_shape)
        for offset in range(0, len(features), 2048):
            block = np.asarray(features[offset : offset + 2048])
            nonfinite += int(block.size - np.isfinite(block).sum())
    acquisition_ids = acquisition["sample_id"]
    annotation_ids = annotation["sample_id"]
    acquisition_set = set(acquisition_ids)
    annotation_set = set(annotation_ids)
    forbidden_acquisition_columns = sorted(set(acquisition) & set(ANNOTATION_FIELDS[1:]))
    exact_path_columns = sorted(column for column in acquisition if "path" in column.lower() or "filename" in column.lower())
    whitespace_cells = 0
    for column in ("sample_id", "receiver_id", "day_id", "feature_shard"):
        whitespace_cells += int((acquisition[column].str.strip() != acquisition[column]).sum())
    for column in ANNOTATION_FIELDS:
        whitespace_cells += int((annotation[column].str.strip() != annotation[column]).sum())
    checks = {
        "manifest_complete": manifest.get("status") == "COMPLETE",
        "manifest_row_count_matches": len(acquisition) == len(annotation) == feature_rows == expected,
        "sample_ids_unique": acquisition_ids.nunique(dropna=False) == expected,
        "annotation_ids_unique": annotation_ids.nunique(dropna=False) == expected,
        "annotation_ids_match": acquisition_set == annotation_set,
        "feature_hashes_match": not hash_mismatches,
        "features_finite": nonfinite == 0,
        "feature_shapes_valid": wrong_shape == 0,
        "receiver_values_valid": acquisition["receiver_id"].nunique() == manifest["structure"]["receiver_count"],
        "day_values_valid": acquisition["day_id"].nunique() == manifest["structure"]["day_count"],
        "target_absent_from_acquisition": not forbidden_acquisition_columns,
        "exact_source_paths_absent": not exact_path_columns,
        "outer_whitespace_absent": whitespace_cells == 0,
        "quality_flags_clear": (acquisition["data_quality_flags"] == "").all(),
    }
    checks = {name: bool(value) for name, value in checks.items()}
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "sample_count": expected,
        "acquisition_row_count": len(acquisition),
        "annotation_row_count": len(annotation),
        "feature_row_count": feature_rows,
        "receiver_count": int(acquisition["receiver_id"].nunique()),
        "day_count": int(acquisition["day_id"].nunique()),
        "transmitter_count": int(annotation["transmitter_id"].nunique()),
        "nonfinite_feature_value_count": nonfinite,
        "wrong_shape_shard_count": wrong_shape,
        "hash_mismatches": hash_mismatches,
        "forbidden_acquisition_columns": forbidden_acquisition_columns,
        "exact_path_columns": exact_path_columns,
        "whitespace_cell_count": whitespace_cells,
    }


def _entropy(values: pd.Series) -> float:
    probabilities = values.value_counts(normalize=True, dropna=False).to_numpy(dtype=float)
    return -float(sum(p * math.log2(p) for p in probabilities if p > 0))


def audit_proxy_field(field: str, values: pd.Series, targets: pd.Series, base_policy: str) -> dict[str, Any]:
    normalized_values = values.fillna("[MISSING]").astype(str)
    normalized_targets = targets.astype(str)
    table = pd.crosstab(normalized_values, normalized_targets, dropna=False)
    group_sizes = table.sum(axis=1).to_numpy(dtype=float)
    group_max = table.max(axis=1).to_numpy(dtype=float)
    purity = np.divide(group_max, group_sizes, out=np.zeros_like(group_sizes), where=group_sizes > 0)
    total = float(group_sizes.sum())
    weighted_purity = float(group_max.sum() / total) if total else 0.0
    pure_mass = float(group_sizes[(table.gt(0).sum(axis=1).to_numpy() == 1)].sum() / total) if total else 0.0
    near_mass = float(group_sizes[purity >= 0.95].sum() / total) if total else 0.0
    nmi = float(normalized_mutual_info_score(normalized_values, normalized_targets)) if len(set(normalized_targets)) > 1 else 0.0
    conditional = 0.0
    for value, group in pd.DataFrame({"value": normalized_values, "target": normalized_targets}).groupby("value", sort=False):
        conditional += len(group) / len(values) * _entropy(group["target"])
    if nmi >= 0.8 or (weighted_purity >= 0.95 and pure_mass >= 0.8) or near_mass >= 0.9:
        classification = "FORBIDDEN_TARGET_PROXY"
    else:
        classification = base_policy
    return {
        "field": field,
        "base_policy": base_policy,
        "classification": classification,
        "row_count": len(values),
        "coverage": float(values.notna().mean()),
        "unique_count": int(normalized_values.nunique()),
        "target_entropy": _entropy(normalized_targets),
        "conditional_target_entropy": conditional,
        "normalized_mutual_information": nmi,
        "weighted_group_purity": weighted_purity,
        "one_to_one_target_mapping_rate": pure_mass,
        "near_deterministic_group_rate": near_mass,
        "group_size_min": int(group_sizes.min()) if len(group_sizes) else 0,
        "group_size_median": float(np.median(group_sizes)) if len(group_sizes) else 0.0,
        "group_size_max": int(group_sizes.max()) if len(group_sizes) else 0,
        "audit_only_label_access": True,
    }


def run_target_proxy_audit(root: str | Path) -> dict[str, Any]:
    acquisition, annotation = load_converted_tables(root)
    joined = acquisition.merge(annotation[["sample_id", "transmitter_id"]], on="sample_id", validate="one_to_one")
    field_policies = {
        "receiver_id": "RELATION_ALLOWED",
        "day_id": "SPLIT_ONLY",
        "packet_index": "AUDIT_ONLY",
        "source_record_index": "AUDIT_ONLY",
        "center_frequency_hz": "MODEL_FEATURE_ALLOWED",
        "bandwidth_hz": "MODEL_FEATURE_ALLOWED",
        "sample_rate_hz": "MODEL_FEATURE_ALLOWED",
        "data_quality_flags": "AUDIT_ONLY",
        "feature_shard": "STORAGE_ONLY",
        "feature_row": "STORAGE_ONLY",
    }
    rows = [audit_proxy_field(field, joined[field], joined["transmitter_id"], policy) for field, policy in field_policies.items()]
    receiver = next(row for row in rows if row["field"] == "receiver_id")
    model_visible_failures = [
        row["field"] for row in rows
        if row["classification"] == "FORBIDDEN_TARGET_PROXY"
        and row["base_policy"] in {"RELATION_ALLOWED", "MODEL_FEATURE_ALLOWED"}
    ]
    return {
        "status": "PASS" if not model_visible_failures and receiver["classification"] == "RELATION_ALLOWED" else "FAIL",
        "target": "transmitter_id",
        "target_loaded_in_audit_process_only": True,
        "relation_whitelist": ["receiver_id"],
        "split_only_fields": ["day_id"],
        "model_visible_proxy_failures": model_visible_failures,
        "diagnostics": rows,
        "notes": [
            "source_record_index and storage shard coordinates reflect deterministic target-nested conversion order and are never model inputs",
            "packet order is not interpreted as physical time",
        ],
    }


def write_support_outputs(root: str | Path, analysis_root: str | Path) -> dict[str, Any]:
    root, analysis_root = Path(root), Path(analysis_root)
    analysis_root.mkdir(parents=True, exist_ok=True)
    acquisition, annotation = load_converted_tables(root)
    joined = acquisition[["sample_id", "receiver_id", "day_id"]].merge(annotation, on="sample_id", validate="one_to_one")
    cube = (
        joined.groupby(["transmitter_id", "receiver_id", "day_id"], observed=True)
        .size()
        .rename("packet_count")
        .reset_index()
        .sort_values(["transmitter_id", "receiver_id", "day_id"], kind="stable")
    )
    parquet_status = "PASS"
    parquet_error = None
    try:
        cube.to_parquet(analysis_root / "support_cube.parquet", index=False)
    except ImportError as exc:
        parquet_status = "DEPENDENCY_UNAVAILABLE"
        parquet_error = str(exc)
        cube.to_csv(analysis_root / "support_cube.csv.gz", index=False, compression="gzip", lineterminator="\n")
    counts = cube["packet_count"].to_numpy()
    per_tx_rx = cube.groupby("transmitter_id")["receiver_id"].nunique()
    per_tx_day = cube.groupby("transmitter_id")["day_id"].nunique()
    per_rx_tx = cube.groupby("receiver_id")["transmitter_id"].nunique()
    per_day_tx = cube.groupby("day_id")["transmitter_id"].nunique()
    summary = {
        "row_count": len(joined),
        "nonzero_combinations": len(cube),
        "possible_combinations": int(joined["transmitter_id"].nunique() * joined["receiver_id"].nunique() * joined["day_id"].nunique()),
        "combination_coverage": float(len(cube) / (joined["transmitter_id"].nunique() * joined["receiver_id"].nunique() * joined["day_id"].nunique())),
        "minimum_support": int(counts.min()),
        "median_support": float(np.median(counts)),
        "maximum_support": int(counts.max()),
        "receiver_coverage_per_transmitter_min": int(per_tx_rx.min()),
        "receiver_coverage_per_transmitter_median": float(per_tx_rx.median()),
        "receiver_coverage_per_transmitter_max": int(per_tx_rx.max()),
        "day_coverage_per_transmitter_min": int(per_tx_day.min()),
        "day_coverage_per_transmitter_max": int(per_tx_day.max()),
        "transmitters_per_receiver_min": int(per_rx_tx.min()),
        "transmitters_per_receiver_max": int(per_rx_tx.max()),
        "transmitters_per_day_min": int(per_day_tx.min()),
        "transmitters_per_day_max": int(per_day_tx.max()),
        "parquet_status": parquet_status,
        "parquet_error": parquet_error,
    }
    pd.DataFrame([summary]).to_csv(analysis_root / "support_summary.csv", index=False, lineterminator="\n")
    return summary
