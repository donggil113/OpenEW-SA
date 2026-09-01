#!/usr/bin/env python3
"""Audit retrospective metadata for target proxies, temporal validity, and episodes.

This script is intentionally label-aware because it is a safety audit. Its
outputs are diagnostics only and are never accepted by relation builders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import normalized_mutual_info_score


CANDIDATE_COLUMNS = (
    "dataset",
    "artifact_source",
    "field",
    "coverage",
    "unique_count",
    "group_size_min",
    "group_size_median",
    "group_size_mean",
    "group_size_max",
    "target_entropy_bits",
    "conditional_target_entropy_bits",
    "target_nmi",
    "weighted_group_purity",
    "one_to_one_target_mapping_rate",
    "near_deterministic_target_proxy_rate",
    "missingness_target_nmi",
    "domain_correlation_nmi",
    "split_correlation_nmi_max",
    "split_protocols_audited",
    "predeclared_classification",
    "audit_classification",
    "classification_reason",
    "inference_time_available",
    "filename_semantics",
    "temporal_verdict",
    "evidence_status",
    "notes",
)


FIELD_POLICIES: dict[str, dict[str, dict[str, Any]]] = {
    "jamshield": {
        "rx_id": {
            "predeclared_classification": "ALLOWED_RELATION",
            "inference_time_available": True,
            "filename_semantics": "NOT_FILENAME_DERIVED",
            "temporal_verdict": "NO_TEMPORAL_METADATA",
            "evidence_status": "VERIFIED",
            "notes": "Station MAC from the source table; already tested in the frozen NO-GO pilot.",
        },
        "time_index": {
            "predeclared_classification": "AUDIT_ONLY",
            "inference_time_available": False,
            "filename_semantics": "NOT_FILENAME_DERIVED",
            "temporal_verdict": "TARGET_NESTED_ORDER",
            "evidence_status": "VERIFIED",
            "notes": "Consecutive row/sample counter resets in target-bearing source files; not acquisition time.",
        },
        "domain_id": {
            "predeclared_classification": "SPLIT_ONLY",
            "inference_time_available": False,
            "filename_semantics": "TARGET_BEARING_FILENAME",
            "temporal_verdict": "NO_TEMPORAL_METADATA",
            "evidence_status": "VERIFIED",
            "notes": "Converted from filenames that encode jammer/benign scenario state.",
        },
        "frequency_band": {
            "predeclared_classification": "UNRESOLVED",
            "inference_time_available": False,
            "filename_semantics": "NOT_FILENAME_DERIVED",
            "temporal_verdict": "NO_TEMPORAL_METADATA",
            "evidence_status": "UNRESOLVED",
            "notes": "Constant placeholder wifi_unknown, not recovered physical frequency metadata.",
        },
    },
    "deepsense": {
        "rx_id": {
            "predeclared_classification": "UNRESOLVED",
            "inference_time_available": True,
            "filename_semantics": "NOT_FILENAME_DERIVED",
            "temporal_verdict": "NO_TEMPORAL_METADATA",
            "evidence_status": "VERIFIED",
            "notes": "One constant receiver identity has no relational variation.",
        },
        "time_index": {
            "predeclared_classification": "AUDIT_ONLY",
            "inference_time_available": False,
            "filename_semantics": "NOT_FILENAME_DERIVED",
            "temporal_verdict": "TARGET_NESTED_ORDER",
            "evidence_status": "VERIFIED",
            "notes": "Converter window order is nested inside occupancy-pure source captures.",
        },
        "domain_id": {
            "predeclared_classification": "SPLIT_ONLY",
            "inference_time_available": False,
            "filename_semantics": "VERIFIED_SOURCE_SEMANTIC",
            "temporal_verdict": "COARSE_DATE_ONLY",
            "evidence_status": "VERIFIED",
            "notes": "day1/day2 campaign token is the frozen cross-day split variable, not dynamic time.",
        },
        "source_file_id": {
            "predeclared_classification": "FORBIDDEN_TARGET_PROXY",
            "inference_time_available": False,
            "filename_semantics": "TARGET_BEARING_FILENAME",
            "temporal_verdict": "TARGET_NESTED_ORDER",
            "evidence_status": "VERIFIED",
            "notes": "Each filename embeds a four-bit occupancy target and a day token.",
        },
        "frequency_band": {
            "predeclared_classification": "UNRESOLVED",
            "inference_time_available": False,
            "filename_semantics": "NOT_FILENAME_DERIVED",
            "temporal_verdict": "NO_TEMPORAL_METADATA",
            "evidence_status": "PARTIALLY_VERIFIED",
            "notes": "Converted wifi_20mhz_4ch descriptor lacks per-channel identity.",
        },
    },
    "electrosense": {
        "rx_id": {
            "predeclared_classification": "ALLOWED_RELATION",
            "inference_time_available": True,
            "filename_semantics": "VERIFIED_SOURCE_SEMANTIC",
            "temporal_verdict": "NO_TEMPORAL_METADATA",
            "evidence_status": "VERIFIED",
            "notes": "Sensor/site folder identity; already tested in the frozen pilot.",
        },
        "source_date_id": {
            "predeclared_classification": "ALLOWED_RELATION",
            "inference_time_available": True,
            "filename_semantics": "VERIFIED_SOURCE_SEMANTIC",
            "temporal_verdict": "COARSE_DATE_ONLY",
            "evidence_status": "PARTIALLY_VERIFIED",
            "notes": "Coarse path date token; no within-day acquisition time or reset semantics.",
        },
        "receiver_date_id": {
            "predeclared_classification": "ALLOWED_RELATION",
            "inference_time_available": True,
            "filename_semantics": "VERIFIED_SOURCE_SEMANTIC",
            "temporal_verdict": "COARSE_DATE_ONLY",
            "evidence_status": "PARTIALLY_VERIFIED",
            "notes": "Deterministic conjunction of receiver and coarse date; already tested.",
        },
        "time_index": {
            "predeclared_classification": "AUDIT_ONLY",
            "inference_time_available": False,
            "filename_semantics": "NOT_FILENAME_DERIVED",
            "temporal_verdict": "TARGET_NESTED_ORDER",
            "evidence_status": "UNRESOLVED",
            "notes": "Array row order is nested inside technology-labeled files; official timing semantics absent.",
        },
        "frequency_band": {
            "predeclared_classification": "FORBIDDEN_TARGET_PROXY",
            "inference_time_available": True,
            "filename_semantics": "TARGET_BEARING_FILENAME",
            "temporal_verdict": "NO_TEMPORAL_METADATA",
            "evidence_status": "VERIFIED",
            "notes": "Band and technology were jointly encoded by converted source filenames; frozen policy forbids it.",
        },
        "source_file_id": {
            "predeclared_classification": "FORBIDDEN_TARGET_PROXY",
            "inference_time_available": False,
            "filename_semantics": "TARGET_BEARING_FILENAME",
            "temporal_verdict": "TARGET_NESTED_ORDER",
            "evidence_status": "VERIFIED",
            "notes": "Filename explicitly embeds the technology target.",
        },
        "domain_id": {
            "predeclared_classification": "SPLIT_ONLY",
            "inference_time_available": False,
            "filename_semantics": "VERIFIED_SOURCE_SEMANTIC",
            "temporal_verdict": "NO_TEMPORAL_METADATA",
            "evidence_status": "VERIFIED",
            "notes": "Receiver identity as the frozen sensor-holdout domain; domain_id itself remains split-only.",
        },
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="/mnt/d/openew_sa_data")
    parser.add_argument(
        "--output-root", default="/mnt/d/openew_sa_data/paper3/metadata_audit"
    )
    args = parser.parse_args()
    frames = load_candidate_frames(Path(args.data_root))
    candidate_rows: list[dict[str, Any]] = []
    group_rows: list[dict[str, Any]] = []
    missing_rows: list[dict[str, Any]] = []
    temporal_rows = temporal_evidence_rows()
    episode_rows: list[dict[str, Any]] = []
    for dataset, frame in frames.items():
        target = frame["__target"].astype(str)
        domain = frame["domain_id"].astype(str)
        split_columns = [column for column in frame if column.startswith("__split_")]
        for field, policy in FIELD_POLICIES[dataset].items():
            values = frame[field]
            diagnostic = field_diagnostic(values, target)
            split_nmis = [safe_nmi(values, frame[column]) for column in split_columns]
            audit_class, reason = conservative_classification(policy, diagnostic)
            candidate_rows.append(
                {
                    "dataset": dataset,
                    "artifact_source": str(Path(args.data_root) / "processed" / dataset),
                    "field": field,
                    **diagnostic,
                    "domain_correlation_nmi": safe_nmi(values, domain),
                    "split_correlation_nmi_max": max(split_nmis, default=0.0),
                    "split_protocols_audited": ";".join(
                        column.removeprefix("__split_") for column in split_columns
                    ),
                    **policy,
                    "audit_classification": audit_class,
                    "classification_reason": reason,
                }
            )
            group_rows.extend(group_purity_rows(dataset, field, values, target))
            missing_rows.append(missingness_row(dataset, field, values, target))
        episode_rows.extend(episode_candidate_rows(dataset, frame))
    destination = Path(args.output_root)
    destination.mkdir(parents=True, exist_ok=True)
    write_csv_atomic(pd.DataFrame(candidate_rows)[list(CANDIDATE_COLUMNS)], destination / "candidate_field_audit.csv")
    proxy_columns = [
        "dataset", "field", "target_nmi", "conditional_target_entropy_bits",
        "weighted_group_purity", "one_to_one_target_mapping_rate",
        "near_deterministic_target_proxy_rate", "domain_correlation_nmi",
        "split_correlation_nmi_max", "audit_classification", "classification_reason",
    ]
    write_csv_atomic(pd.DataFrame(candidate_rows)[proxy_columns], destination / "target_proxy_summary.csv")
    write_csv_atomic(pd.DataFrame(group_rows), destination / "group_purity_summary.csv")
    write_csv_atomic(pd.DataFrame(missing_rows), destination / "missingness_summary.csv")
    write_csv_atomic(pd.DataFrame(temporal_rows), destination / "temporal_feasibility.csv")
    write_csv_atomic(pd.DataFrame(episode_rows), destination / "episode_candidates.csv")
    summary = {
        "datasets": sorted(frames),
        "candidate_field_count": len(candidate_rows),
        "rejected_target_proxy_count": sum(
            row["audit_classification"] == "FORBIDDEN_TARGET_PROXY" for row in candidate_rows
        ),
        "valid_temporal_context_count": sum(
            row["verdict"] == "VALID_TEMPORAL_CONTEXT" for row in temporal_rows
        ),
        "output_root": str(destination),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


def load_candidate_frames(data_root: Path) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for dataset in ("jamshield", "deepsense", "electrosense"):
        root = data_root / "processed" / dataset
        frame = pd.read_csv(root / "metadata.csv", dtype=str, keep_default_na=False)
        manifest = json.loads((root / "labels.json").read_text(encoding="utf-8"))
        if dataset == "jamshield":
            frame["__target"] = frame["abnormal_event_label"]
            domains = frame["domain_id"].astype(str)
            frame["__split_scenario"] = np.where(
                domains.isin(
                    {
                        "reactive_jammer_square_NLOS",
                        "random_jammer_gaussian_NLOS",
                        "constant_jammer_gaussian_25db",
                        "data_benign_4",
                    }
                ),
                "heldout",
                "source",
            )
            frame["__split_reactive"] = np.where(
                domains.str.contains("reactive", case=False) | (domains == "data_benign_4"),
                "heldout",
                "source",
            )
        elif dataset == "deepsense":
            frame["__target"] = frame["occupancy_label"]
            frame["source_file_id"] = expand_descriptor_field(
                manifest["source_files"], "path", len(frame)
            )
            frame["__split_cross_day"] = np.where(
                frame["domain_id"] == "day2", "heldout", "source"
            )
        else:
            frame["__target"] = frame["situation_label"]
            frame["source_date_id"] = expand_descriptor_field(
                manifest["source_files"], "date_id", len(frame)
            )
            frame["source_file_id"] = expand_descriptor_field(
                manifest["source_files"], "path", len(frame)
            )
            frame["receiver_date_id"] = frame["rx_id"] + "|" + frame["source_date_id"]
            frame["__split_sensor"] = np.where(
                frame["domain_id"].isin({"alcorcon1", "bcn-L", "Geneva"}),
                "heldout",
                "source",
            )
        frames[dataset] = frame
    return frames


def expand_descriptor_field(
    descriptors: Iterable[dict[str, Any]], field: str, expected: int
) -> pd.Series:
    values: list[str] = []
    for descriptor in descriptors:
        values.extend([str(descriptor.get(field, ""))] * int(descriptor.get("row_count", 0)))
    if len(values) != expected:
        raise ValueError(f"Descriptor expansion mismatch for {field}: {len(values)} != {expected}")
    return pd.Series(values, dtype="string")


def field_diagnostic(values: pd.Series, targets: pd.Series) -> dict[str, Any]:
    clean = values.astype("string")
    populated_mask = clean.notna() & (clean != "")
    pairs = pd.DataFrame({"value": clean[populated_mask], "target": targets[populated_mask]})
    sizes = pairs.groupby("value", dropna=False).size()
    target_entropy = entropy(targets.tolist())
    conditional = 0.0
    weighted_purity = 0.0
    pure_rows = 0
    near_rows = 0
    if len(pairs):
        for _, group in pairs.groupby("value", sort=False):
            counts = group["target"].value_counts()
            weight = len(group) / len(pairs)
            purity = float(counts.max() / len(group))
            conditional += weight * entropy(group["target"].tolist())
            weighted_purity += weight * purity
            if len(counts) == 1:
                pure_rows += len(group)
            if purity >= 0.95:
                near_rows += len(group)
    return {
        "coverage": float(populated_mask.mean()) if len(clean) else 0.0,
        "unique_count": int(sizes.size),
        "group_size_min": int(sizes.min()) if len(sizes) else 0,
        "group_size_median": float(sizes.median()) if len(sizes) else 0.0,
        "group_size_mean": float(sizes.mean()) if len(sizes) else 0.0,
        "group_size_max": int(sizes.max()) if len(sizes) else 0,
        "target_entropy_bits": target_entropy,
        "conditional_target_entropy_bits": conditional,
        "target_nmi": safe_nmi(pairs["value"], pairs["target"]) if len(pairs) else 0.0,
        "weighted_group_purity": weighted_purity,
        "one_to_one_target_mapping_rate": pure_rows / len(pairs) if len(pairs) else 0.0,
        "near_deterministic_target_proxy_rate": near_rows / len(pairs) if len(pairs) else 0.0,
        "missingness_target_nmi": safe_nmi(
            populated_mask.map({True: "present", False: "missing"}), targets
        ),
    }


def conservative_classification(
    policy: dict[str, Any], diagnostic: dict[str, Any]
) -> tuple[str, str]:
    base = str(policy["predeclared_classification"])
    if base == "FORBIDDEN_TARGET_PROXY":
        return base, "predeclared forbidden from source semantics"
    if diagnostic["coverage"] < 0.8:
        return "UNRESOLVED", "coverage below conservative 0.80 threshold"
    if (
        diagnostic["target_nmi"] >= 0.8
        or diagnostic["near_deterministic_target_proxy_rate"] >= 0.9
        or (
            diagnostic["weighted_group_purity"] >= 0.95
            and diagnostic["one_to_one_target_mapping_rate"] >= 0.8
        )
    ):
        return "FORBIDDEN_TARGET_PROXY", "near-deterministic target association in safety audit"
    if base == "ALLOWED_RELATION" and policy["evidence_status"] != "VERIFIED":
        return "UNRESOLVED", "relation semantics are not independently fully verified"
    return base, f"retains conservative predeclared classification {base}"


def group_purity_rows(
    dataset: str, field: str, values: pd.Series, targets: pd.Series
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pairs = pd.DataFrame({"value": values.astype("string"), "target": targets.astype(str)})
    pairs = pairs[pairs["value"].notna() & (pairs["value"] != "")]
    for value, group in pairs.groupby("value", sort=True):
        counts = group["target"].value_counts()
        rows.append(
            {
                "dataset": dataset,
                "field": field,
                "value_sha256_12": hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12],
                "group_size": len(group),
                "target_unique_count": len(counts),
                "target_purity": float(counts.max() / len(group)),
                "target_entropy_bits": entropy(group["target"].tolist()),
            }
        )
    return rows


def missingness_row(
    dataset: str, field: str, values: pd.Series, targets: pd.Series
) -> dict[str, Any]:
    populated = values.astype("string").notna() & (values.astype("string") != "")
    return {
        "dataset": dataset,
        "field": field,
        "total_count": len(values),
        "missing_count": int((~populated).sum()),
        "missing_fraction": float((~populated).mean()) if len(values) else 0.0,
        "missingness_target_nmi": safe_nmi(
            populated.map({True: "present", False: "missing"}), targets
        ),
    }


def temporal_evidence_rows() -> list[dict[str, Any]]:
    rows = [
        ("jamshield", "time_index", "TARGET_NESTED_ORDER", "Counter resets in target-bearing files; no time units, gaps, or reset semantics."),
        ("jamshield", "filesystem_mtime", "SYSTEM_TIMESTAMP_ONLY", "No evidence that local filesystem mtime is acquisition time."),
        ("jamshield", "timestamp_utc", "NO_TEMPORAL_METADATA", "No acquisition timestamp field found."),
        ("deepsense", "domain_id/day", "COARSE_DATE_ONLY", "day1/day2 supports the frozen split but not within-session dynamics."),
        ("deepsense", "time_index/window_index", "TARGET_NESTED_ORDER", "Window order exists only inside occupancy-pure captures."),
        ("deepsense", "filesystem_mtime", "SYSTEM_TIMESTAMP_ONLY", "No evidence that local filesystem mtime is acquisition time."),
        ("deepsense", "timestamp_utc", "NO_TEMPORAL_METADATA", "Binary payload and manifest expose no acquisition timestamps."),
        ("electrosense", "source_date_id", "COARSE_DATE_ONLY", "Date token has no within-day time, gap, or reset semantics."),
        ("electrosense", "time_index/array_row", "TARGET_NESTED_ORDER", "Rows occur inside technology-labeled arrays; official acquisition order is unverified."),
        ("electrosense", "filesystem_mtime", "SYSTEM_TIMESTAMP_ONLY", "No evidence that local filesystem mtime is acquisition time."),
        ("electrosense", "timestamp_utc", "NO_TEMPORAL_METADATA", "Plain NPY arrays expose no timestamp vector or header metadata."),
    ]
    return [
        {
            "dataset": dataset,
            "field": field,
            "verdict": verdict,
            "physical_or_acquisition_order_verified": False,
            "session_reset_semantics_verified": False,
            "gap_meaning_verified": False,
            "inference_time_available": verdict == "COARSE_DATE_ONLY",
            "mixed_target_episode_evidence": False,
            "reason": reason,
        }
        for dataset, field, verdict, reason in rows
    ]


def episode_candidate_rows(dataset: str, frame: pd.DataFrame) -> list[dict[str, Any]]:
    definitions = {
        "jamshield": [("station_episode", ["rx_id"], "plausible station grouping but completed pilot NO-GO")],
        "deepsense": [
            ("day_episode", ["domain_id"], "split-only coarse day; not a deployment episode"),
            ("source_capture_episode", ["source_file_id"], "target-bearing occupancy-pure capture"),
        ],
        "electrosense": [
            ("receiver_episode", ["rx_id"], "receiver grouping already tested"),
            ("date_episode", ["source_date_id"], "coarse date with no timing semantics"),
            ("receiver_date_episode", ["rx_id", "source_date_id"], "joint grouping already tested"),
            ("source_file_episode", ["source_file_id"], "technology-bearing target-pure file"),
        ],
    }
    target = frame["__target"].astype(str)
    rows: list[dict[str, Any]] = []
    for name, fields, note in definitions[dataset]:
        key = frame[fields].astype(str).agg("|".join, axis=1)
        groups = pd.DataFrame({"episode": key, "target": target}).groupby("episode", sort=False)
        sizes = groups.size()
        purity = groups["target"].apply(lambda values: values.value_counts().max() / len(values))
        mixed = groups["target"].nunique() > 1
        leakage = (
            "FORBIDDEN_TARGET_PROXY"
            if "source_file_id" in fields
            else "SPLIT_ONLY"
            if dataset == "deepsense"
            else "STRUCTURALLY_ALLOWED_BUT_NO_NEW_EXPERIMENT"
        )
        rows.append(
            {
                "dataset": dataset,
                "episode_definition": name,
                "field_sources": ";".join(fields),
                "coverage": float(key.ne("").mean()),
                "episode_count": int(len(sizes)),
                "median_episode_size": float(sizes.median()),
                "max_episode_size": int(sizes.max()),
                "mixed_label_fraction": float(mixed.mean()),
                "weighted_target_purity": float(np.average(purity, weights=sizes)),
                "domain_count": int(frame["domain_id"].nunique()),
                "deployment_plausibility": note,
                "leakage_status": leakage,
            }
        )
    return rows


def entropy(values: list[str]) -> float:
    if not values:
        return 0.0
    _, counts = np.unique(np.asarray(values, dtype=str), return_counts=True)
    probabilities = counts / counts.sum()
    return float(-sum(value * math.log2(value) for value in probabilities if value > 0))


def safe_nmi(left: Iterable[Any], right: Iterable[Any]) -> float:
    left_values = pd.Series(left, dtype="string").fillna("<MISSING>").astype(str)
    right_values = pd.Series(right, dtype="string").fillna("<MISSING>").astype(str)
    if len(left_values) != len(right_values) or not len(left_values):
        return 0.0
    if left_values.nunique() <= 1 or right_values.nunique() <= 1:
        return 0.0
    return float(normalized_mutual_info_score(left_values, right_values))


def write_csv_atomic(frame: pd.DataFrame, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


if __name__ == "__main__":
    main()
