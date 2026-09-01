"""Deterministic, read-only relational metadata audit for Paper 3.

The module profiles frozen OpenEW-SA artifacts without loading feature arrays into
memory or writing sample-level records.  Explicit policy is combined with observed
coverage and target association; no field becomes allowed merely because its name
does not contain ``label``.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


AUDIT_COLUMNS = [
    "dataset",
    "artifact_source",
    "field",
    "dtype",
    "non_null_count",
    "total_count",
    "availability_fraction",
    "unique_count",
    "example_values_redacted_or_short",
    "available_at_inference",
    "relation_candidate",
    "temporal_candidate",
    "target_or_label_related",
    "leakage_risk",
    "leakage_reason",
    "proposed_relation_type",
    "verified_status",
    "notes",
    "target_purity",
    "target_baseline",
    "target_purity_lift",
    "single_target_group_fraction",
    "value_contains_target_token",
]

RELATION_COVERAGE_COLUMNS = [
    "dataset",
    "field",
    "policy_class",
    "allowed_by_whitelist",
    "availability_fraction",
    "unique_count",
    "average_group_size",
    "target_purity",
    "target_baseline",
    "relation_candidate",
    "temporal_candidate",
    "leakage_risk",
    "proposed_relation_type",
    "notes",
]

DATASET_SUMMARY_COLUMNS = [
    "dataset",
    "artifact_source",
    "metadata_rows",
    "metadata_column_count",
    "feature_shape",
    "feature_dtype",
    "source_file_count",
    "allowed_relation_fields",
    "allowed_relation_count",
    "minimum_allowed_relation_coverage",
    "target_proxy_field_count",
    "temporal_relation_defensible",
    "dataset_verdict",
    "static_verdict",
    "dynamic_verdict",
    "notes",
]

TARGET_FIELDS = {
    "jamshield": "abnormal_event_label",
    "deepsense": "occupancy_label",
    "electrosense": "situation_label",
}

DEFAULT_ARTIFACT_DIRS = {
    dataset: Path("/mnt/d/openew_sa_data/processed") / dataset
    for dataset in TARGET_FIELDS
}

POLICY_ALLOWED = "A. ALLOWED MODEL RELATION"
POLICY_SPLIT_ONLY = "B. SPLIT-ONLY"
POLICY_DIAGNOSTIC = "C. DIAGNOSTIC-ONLY"
POLICY_FORBIDDEN = "D. FORBIDDEN / TARGET LEAKAGE"
POLICY_UNRESOLVED = "E. UNRESOLVED"

DEFAULT_RELATION_WHITELISTS = {
    "jamshield": frozenset({"rx_id"}),
    "deepsense": frozenset(),
    "electrosense": frozenset({"rx_id", "source_date_id"}),
}

LABEL_OR_OUTCOME_FIELDS = frozenset(
    {
        "modulation_label",
        "occupancy_label",
        "abnormal_event_label",
        "situation_label",
        "threat_level",
        "human_review_required",
        "ood_label",
        "is_ood",
        "split",
        "paper2_split",
        "test_correct",
        "prediction_correct",
        "source_occupancy_label",
        "source_technology_label",
    }
)

TARGET_TOKENS = {
    "jamshield": {"normal", "abnormal", "attack", "benign", "jammer"},
    "deepsense": {f"{value:04b}" for value in range(16)} | {"occupied", "idle"},
    "electrosense": {"dab", "dvbt", "fm", "gsm", "lte", "tetra", "unknown", "unkn"},
}


@dataclass(frozen=True)
class FieldPolicy:
    """Human-reviewed use policy for one candidate metadata field."""

    policy_class: str
    available_at_inference: str
    relation_candidate: str
    temporal_candidate: str
    target_or_label_related: str
    leakage_risk: str
    leakage_reason: str
    proposed_relation_type: str
    verified_status: str
    notes: str


def _policy(
    policy_class: str,
    available: str,
    relation: str,
    temporal: str,
    target_related: str,
    risk: str,
    reason: str,
    relation_type: str = "",
    verified: str = "VERIFIED FACT",
    notes: str = "",
) -> FieldPolicy:
    return FieldPolicy(
        policy_class,
        available,
        relation,
        temporal,
        target_related,
        risk,
        reason,
        relation_type,
        verified,
        notes,
    )


COMMON_POLICIES = {
    "sample_id": _policy(
        POLICY_DIAGNOSTIC,
        "yes",
        "no",
        "no",
        "no",
        "medium",
        "Converter-generated global order is an identifier, not a physical relation or clock.",
    ),
    "dataset_source": _policy(
        POLICY_DIAGNOSTIC, "yes", "no", "no", "no", "low", "Constant within each dataset."
    ),
    "input_type": _policy(
        POLICY_DIAGNOSTIC, "yes", "no", "no", "no", "low", "Constant within each dataset."
    ),
    "tx_id": _policy(
        POLICY_UNRESOLVED,
        "no",
        "no",
        "no",
        "no",
        "unknown",
        "The frozen converted artifacts do not populate transmitter identity.",
    ),
    "modulation_label": _policy(
        POLICY_FORBIDDEN, "no", "no", "no", "yes", "critical", "Ground-truth label field."
    ),
    "occupancy_label": _policy(
        POLICY_FORBIDDEN, "no", "no", "no", "yes", "critical", "Ground-truth label field."
    ),
    "abnormal_event_label": _policy(
        POLICY_FORBIDDEN, "no", "no", "no", "yes", "critical", "Ground-truth label field."
    ),
    "situation_label": _policy(
        POLICY_FORBIDDEN, "no", "no", "no", "yes", "critical", "Ground-truth or target-derived label field."
    ),
    "threat_level": _policy(
        POLICY_FORBIDDEN,
        "no",
        "no",
        "no",
        "yes",
        "critical",
        "Converter-synthesized target-derived field for JamShield and a constant elsewhere.",
    ),
    "human_review_required": _policy(
        POLICY_FORBIDDEN,
        "no",
        "no",
        "no",
        "yes",
        "critical",
        "Converter-synthesized from the JamShield target and constant elsewhere.",
    ),
    "synthetic_mission_context": _policy(
        POLICY_DIAGNOSTIC,
        "no",
        "no",
        "no",
        "no",
        "medium",
        "Converter constant rather than measured acquisition context.",
    ),
    "source_capture_id": _policy(
        POLICY_FORBIDDEN,
        "conditional",
        "no",
        "no",
        "yes",
        "critical",
        "Every frozen source capture/file is target-pure in all three tasks.",
    ),
    "source_relative_path": _policy(
        POLICY_FORBIDDEN,
        "no",
        "no",
        "no",
        "yes",
        "critical",
        "Source paths and stems visibly encode class, jammer, benign, day, or technology tokens.",
    ),
    "source_occupancy_label": _policy(
        POLICY_FORBIDDEN, "no", "no", "no", "yes", "critical", "Ground-truth occupancy label."
    ),
    "source_technology_label": _policy(
        POLICY_FORBIDDEN, "no", "no", "no", "yes", "critical", "Ground-truth technology label."
    ),
    "source_original_shape": _policy(
        POLICY_DIAGNOSTIC,
        "no",
        "no",
        "no",
        "conditional",
        "high",
        "File shape is conversion provenance and may encode source/class collection structure.",
    ),
}

DATASET_POLICIES = {
    "jamshield": {
        "rx_id": _policy(
            POLICY_ALLOWED,
            "yes",
            "yes",
            "no",
            "no",
            "medium",
            "Raw station identity is acquisition-time metadata, but two of seven stations are single-target in the frozen rows.",
            "station_edge",
            notes="Treat the source field as station/endpoint identity; the source README calls it a transmitting station.",
        ),
        "domain_id": _policy(
            POLICY_SPLIT_ONLY,
            "no",
            "no",
            "no",
            "yes",
            "critical",
            "CSV stems define the frozen scenario holdout and explicitly encode benign/jammer type; all 20 groups are target-pure.",
        ),
        "frequency_band": _policy(
            POLICY_DIAGNOSTIC,
            "yes",
            "no",
            "no",
            "no",
            "low",
            "The converted value is the constant placeholder wifi_unknown.",
        ),
        "time_index": _policy(
            POLICY_UNRESOLVED,
            "conditional",
            "no",
            "conditional",
            "conditional",
            "high",
            "The raw sample counter is monotonic only inside a source CSV; the required CSV/session identity is target-pure and forbidden.",
            verified="VERIFIED FACT + UNRESOLVED MODEL USE",
        ),
        "source_row_index": _policy(
            POLICY_UNRESOLVED,
            "conditional",
            "no",
            "conditional",
            "conditional",
            "high",
            "Row order is verified inside each target-pure source file but not safely usable without that file identity.",
        ),
        "source_date_id": _policy(
            POLICY_UNRESOLVED, "no", "no", "no", "no", "unknown", "No acquisition date is present."
        ),
    },
    "deepsense": {
        "rx_id": _policy(
            POLICY_DIAGNOSTIC, "yes", "no", "no", "no", "low", "Constant single receiver identifier."
        ),
        "domain_id": _policy(
            POLICY_SPLIT_ONLY,
            "yes",
            "no",
            "no",
            "yes",
            "high",
            "The field is exactly the Paper 1/Paper 2 day1/day2 holdout definition.",
        ),
        "source_domain_id": _policy(
            POLICY_SPLIT_ONLY,
            "yes",
            "no",
            "no",
            "yes",
            "high",
            "The source day token is exactly the frozen holdout definition.",
        ),
        "frequency_band": _policy(
            POLICY_DIAGNOSTIC,
            "yes",
            "no",
            "no",
            "no",
            "low",
            "Constant 20 MHz four-channel descriptor with no per-channel relation metadata.",
        ),
        "time_index": _policy(
            POLICY_DIAGNOSTIC,
            "yes",
            "no",
            "conditional",
            "conditional",
            "critical",
            "Window order is verified only within one class-pure capture; time_index repeats across 32 files and metadata omits a safe capture key.",
        ),
        "source_row_index": _policy(
            POLICY_DIAGNOSTIC,
            "yes",
            "no",
            "conditional",
            "conditional",
            "critical",
            "Contiguous window order is real, but the enclosing capture is target-pure.",
        ),
        "source_date_id": _policy(
            POLICY_UNRESOLVED, "no", "no", "no", "no", "unknown", "Only day1/day2 domain tokens are available."
        ),
    },
    "electrosense": {
        "rx_id": _policy(
            POLICY_ALLOWED,
            "yes",
            "yes",
            "no",
            "no",
            "low",
            "Receiver/sensor identity is physical acquisition metadata and all 40 receivers contain multiple target classes.",
            "receiver_edge",
        ),
        "source_sensor_id": _policy(
            POLICY_DIAGNOSTIC,
            "yes",
            "no",
            "no",
            "no",
            "low",
            "Duplicate source descriptor for rx_id; not separately whitelisted to avoid duplicate relations.",
        ),
        "domain_id": _policy(
            POLICY_SPLIT_ONLY,
            "yes",
            "no",
            "no",
            "yes",
            "high",
            "Exact duplicate of receiver identity used to define the frozen sensor holdout; use rx_id equality only under the whitelist.",
        ),
        "frequency_band": _policy(
            POLICY_FORBIDDEN,
            "yes",
            "no",
            "no",
            "yes",
            "critical",
            "All 125 observed bands are target-pure in the frozen technology-classification task.",
        ),
        "source_frequency_band": _policy(
            POLICY_FORBIDDEN,
            "yes",
            "no",
            "no",
            "yes",
            "critical",
            "Duplicate source descriptor of an exact target proxy.",
        ),
        "band_lower_mhz": _policy(
            POLICY_FORBIDDEN,
            "yes",
            "no",
            "no",
            "yes",
            "critical",
            "Derived from a frequency band that is an exact target proxy in the frozen task.",
        ),
        "band_upper_mhz": _policy(
            POLICY_FORBIDDEN,
            "yes",
            "no",
            "no",
            "yes",
            "critical",
            "Derived from a frequency band that is an exact target proxy in the frozen task.",
        ),
        "band_center_mhz": _policy(
            POLICY_FORBIDDEN,
            "yes",
            "no",
            "no",
            "yes",
            "critical",
            "Derived from a frequency band that is an exact target proxy in the frozen task.",
        ),
        "source_date_id": _policy(
            POLICY_ALLOWED,
            "yes",
            "yes",
            "no",
            "no",
            "medium",
            "Coarse acquisition-date folder is reconstructable for every row and is not target-pure, but it lacks year and time-of-day.",
            "acquisition_date_edge",
        ),
        "time_index": _policy(
            POLICY_UNRESOLVED,
            "conditional",
            "no",
            "conditional",
            "conditional",
            "critical",
            "Row order is local to a target-pure frequency/technology file; no timestamp or cross-file order is available.",
        ),
        "source_row_index": _policy(
            POLICY_UNRESOLVED,
            "conditional",
            "no",
            "conditional",
            "conditional",
            "critical",
            "Local array order is verified, but the capture boundary is an exact target proxy and no clock is available.",
        ),
    },
}

DATASET_VERDICTS = {
    "jamshield": (
        "CONDITIONAL GO",
        "CONDITIONAL GO",
        "NO-GO",
        "Station equality is fully covered; target-pure scenario/session files prevent leakage-safe temporal construction.",
    ),
    "deepsense": (
        "NO-GO",
        "NO-GO",
        "NO-GO",
        "No nonconstant whitelisted relation remains; every reconstructable capture is one occupancy class.",
    ),
    "electrosense": (
        "CONDITIONAL GO",
        "CONDITIONAL GO",
        "NO-GO",
        "Receiver and coarse date groups are covered; frequency/capture are target proxies and timestamps are absent.",
    ),
}


def read_metadata_preserve_strings(path: Path) -> pd.DataFrame:
    """Read metadata without coercing symbolic identifiers such as ``0001``."""

    if not path.exists():
        raise FileNotFoundError(f"metadata.csv not found: {path}")
    try:
        frame = pd.read_csv(path, dtype="string", keep_default_na=False)
    except pd.errors.EmptyDataError as error:
        raise ValueError(f"metadata.csv is empty: {path}") from error
    if frame.empty:
        raise ValueError(f"metadata.csv contains no rows: {path}")
    return frame


def validate_relation_fields(
    dataset: str,
    requested_fields: Iterable[str],
    allowed_field_whitelist: Iterable[str],
) -> tuple[str, ...]:
    """Reject target fields and enforce the dataset's hard reviewed whitelist."""

    dataset_key = dataset.lower()
    if dataset_key not in DEFAULT_RELATION_WHITELISTS:
        raise ValueError(f"Unsupported Paper 3 dataset: {dataset}")
    requested = tuple(dict.fromkeys(str(field) for field in requested_fields))
    configured = frozenset(str(field) for field in allowed_field_whitelist)
    reviewed = DEFAULT_RELATION_WHITELISTS[dataset_key]
    forbidden = [field for field in requested if _looks_forbidden(field)]
    if forbidden:
        raise ValueError(f"Forbidden target/outcome fields requested for relations: {forbidden}")
    unsafe_whitelist = configured - reviewed
    if unsafe_whitelist:
        raise ValueError(
            f"Configured whitelist for {dataset_key} exceeds reviewed fields: {sorted(unsafe_whitelist)}"
        )
    outside_config = [field for field in requested if field not in configured]
    if outside_config:
        raise ValueError(f"Relation fields are not explicitly whitelisted for {dataset_key}: {outside_config}")
    return requested


def audit_artifact(
    dataset: str,
    artifact_dir: Path,
    allowed_field_whitelist: Iterable[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Audit one frozen artifact directory without modifying its inputs."""

    dataset_key = dataset.lower()
    if dataset_key not in TARGET_FIELDS:
        raise ValueError(f"Unsupported Paper 3 dataset: {dataset}")
    artifact_dir = Path(artifact_dir)
    metadata_path = artifact_dir / "metadata.csv"
    labels_path = artifact_dir / "labels.json"
    feature_path = artifact_dir / "features.npy"
    before = _source_signature([metadata_path, labels_path, feature_path])

    metadata = read_metadata_preserve_strings(metadata_path)
    if not labels_path.exists():
        raise FileNotFoundError(f"labels.json not found: {labels_path}")
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    if not feature_path.exists():
        raise FileNotFoundError(f"features.npy not found: {feature_path}")
    features = np.load(feature_path, mmap_mode="r", allow_pickle=False)
    if int(features.shape[0]) != len(metadata):
        raise ValueError(
            f"Feature/metadata row mismatch for {dataset_key}: {features.shape[0]} != {len(metadata)}"
        )

    augmented, field_sources = _augment_source_fields(dataset_key, metadata, labels)
    target_field = TARGET_FIELDS[dataset_key]
    if target_field not in augmented:
        raise ValueError(f"Target field '{target_field}' missing from {metadata_path}")
    target = augmented[target_field].astype("string").fillna("")
    target_baseline = _target_baseline(target)

    rows: list[dict[str, Any]] = []
    for field in augmented.columns:
        series = augmented[field].astype("string").fillna("")
        policy = _field_policy(dataset_key, field)
        association = _association_profile(series, target)
        contains_token = _contains_target_token(dataset_key, series)
        leakage_reason = policy.leakage_reason
        target_related = policy.target_or_label_related
        risk = policy.leakage_risk
        if contains_token and policy.policy_class != POLICY_FORBIDDEN:
            leakage_reason += " Observed values contain target/domain tokens."
            target_related = "yes"
            risk = _max_risk(risk, "high")
        if _near_exact_proxy(association, len(augmented)) and policy.policy_class != POLICY_FORBIDDEN:
            leakage_reason += " Observed grouping is a near-exact target proxy."
            target_related = "yes"
            risk = _max_risk(risk, "critical")
        populated = series.str.strip().ne("")
        rows.append(
            {
                "dataset": dataset_key,
                "artifact_source": field_sources.get(field, str(metadata_path)),
                "field": field,
                "dtype": _infer_dtype(series),
                "non_null_count": int(populated.sum()),
                "total_count": int(len(series)),
                "availability_fraction": round(float(populated.mean()), 6),
                "unique_count": int(series.loc[populated].nunique(dropna=False)),
                "example_values_redacted_or_short": _short_examples(dataset_key, field, series),
                "available_at_inference": policy.available_at_inference,
                "relation_candidate": policy.relation_candidate,
                "temporal_candidate": policy.temporal_candidate,
                "target_or_label_related": target_related,
                "leakage_risk": risk,
                "leakage_reason": leakage_reason,
                "proposed_relation_type": policy.proposed_relation_type,
                "verified_status": policy.verified_status,
                "notes": policy.notes,
                "target_purity": association["target_purity"],
                "target_baseline": target_baseline,
                "target_purity_lift": _round_or_blank(
                    _subtract(association["target_purity"], target_baseline)
                ),
                "single_target_group_fraction": association["single_target_group_fraction"],
                "value_contains_target_token": contains_token,
            }
        )

    whitelist = frozenset(
        DEFAULT_RELATION_WHITELISTS[dataset_key]
        if allowed_field_whitelist is None
        else allowed_field_whitelist
    )
    validate_relation_fields(dataset_key, whitelist, whitelist)
    after = _source_signature([metadata_path, labels_path, feature_path])
    if before != after:
        raise RuntimeError(f"Source artifact changed during audit: {artifact_dir}")

    audit = pd.DataFrame(rows, columns=AUDIT_COLUMNS)
    summary = {
        "dataset": dataset_key,
        "artifact_source": str(artifact_dir),
        "metadata_rows": int(len(metadata)),
        "metadata_column_count": int(len(metadata.columns)),
        "feature_shape": "x".join(str(value) for value in features.shape),
        "feature_dtype": str(features.dtype),
        "source_file_count": int(len(labels.get("source_files", []))),
        "allowed_field_whitelist": sorted(whitelist),
        "source_signature": before,
    }
    return audit, summary


def run_audit(
    artifact_dirs: Mapping[str, Path],
    output_dir: Path,
    relation_whitelists: Mapping[str, Iterable[str]] | None = None,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Run all dataset audits and optionally write the three required external CSVs."""

    output_dir = Path(output_dir)
    relation_whitelists = relation_whitelists or DEFAULT_RELATION_WHITELISTS
    resolved_artifacts = {name: Path(path) for name, path in artifact_dirs.items()}
    _validate_output_location(output_dir, resolved_artifacts.values())

    audits: list[pd.DataFrame] = []
    artifact_summaries: list[dict[str, Any]] = []
    for dataset in sorted(resolved_artifacts):
        whitelist = relation_whitelists.get(dataset, ())
        validate_relation_fields(dataset, whitelist, whitelist)
        audit, summary = audit_artifact(dataset, resolved_artifacts[dataset], whitelist)
        audits.append(audit)
        artifact_summaries.append(summary)
    audit_frame = pd.concat(audits, ignore_index=True).loc[:, AUDIT_COLUMNS]
    coverage = _relation_coverage_summary(audit_frame, relation_whitelists)
    dataset_summary = _dataset_relation_summary(audit_frame, artifact_summaries, relation_whitelists)

    outputs = {
        "relational_metadata_audit": str(output_dir / "relational_metadata_audit.csv"),
        "relation_coverage_summary": str(output_dir / "relation_coverage_summary.csv"),
        "dataset_relation_summary": str(output_dir / "dataset_relation_summary.csv"),
    }
    if write_outputs:
        output_dir.mkdir(parents=True, exist_ok=True)
        audit_frame.to_csv(outputs["relational_metadata_audit"], index=False)
        coverage.to_csv(outputs["relation_coverage_summary"], index=False)
        dataset_summary.to_csv(outputs["dataset_relation_summary"], index=False)
    return {
        "audit": audit_frame,
        "coverage": coverage,
        "dataset_summary": dataset_summary,
        "artifact_summaries": artifact_summaries,
        "outputs": outputs,
    }


def _augment_source_fields(
    dataset: str, metadata: pd.DataFrame, labels: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, str]]:
    frame = metadata.copy()
    sources = {column: "metadata.csv" for column in frame.columns}
    descriptors = labels.get("source_files", [])
    if not descriptors:
        return frame, sources
    expected = sum(int(item.get("row_count", 0)) for item in descriptors)
    if expected != len(frame):
        raise ValueError(
            f"labels.json source row counts do not match metadata for {dataset}: {expected} != {len(frame)}"
        )

    derived: dict[str, list[str]] = {
        "source_capture_id": [],
        "source_relative_path": [],
        "source_row_index": [],
    }
    dataset_fields = {
        "deepsense": ["domain_id", "occupancy_label"],
        "electrosense": [
            "sensor_id",
            "date_id",
            "frequency_band",
            "technology_label",
            "original_shape",
        ],
        "jamshield": [],
    }[dataset]
    for field in dataset_fields:
        derived[f"source_{field}"] = []

    for capture_index, descriptor in enumerate(descriptors):
        count = int(descriptor["row_count"])
        path = str(descriptor.get("path") or descriptor.get("relative_path") or "")
        derived["source_capture_id"].extend([f"source_capture_{capture_index:04d}"] * count)
        derived["source_relative_path"].extend([path] * count)
        derived["source_row_index"].extend([str(index) for index in range(count)])
        for field in dataset_fields:
            value = descriptor.get(field, "")
            if isinstance(value, (list, tuple)):
                value = "x".join(str(part) for part in value)
            derived[f"source_{field}"].extend([str(value)] * count)

    for field, values in derived.items():
        frame[field] = pd.Series(values, dtype="string")
        sources[field] = "labels.json:source_files (deterministically expanded by row_count)"

    if dataset == "electrosense":
        parsed = frame["frequency_band"].map(_parse_frequency_band)
        frame["band_lower_mhz"] = parsed.map(lambda item: item[0] if item else "").astype("string")
        frame["band_upper_mhz"] = parsed.map(lambda item: item[1] if item else "").astype("string")
        frame["band_center_mhz"] = parsed.map(
            lambda item: (item[0] + item[1]) / 2.0 if item else ""
        ).astype("string")
        for field in ("band_lower_mhz", "band_upper_mhz", "band_center_mhz"):
            sources[field] = "derived from metadata.csv:frequency_band"
    return frame, sources


def _field_policy(dataset: str, field: str) -> FieldPolicy:
    if field in DATASET_POLICIES[dataset]:
        return DATASET_POLICIES[dataset][field]
    if field in COMMON_POLICIES:
        return COMMON_POLICIES[field]
    if _looks_forbidden(field):
        return _policy(
            POLICY_FORBIDDEN,
            "no",
            "no",
            "no",
            "yes",
            "critical",
            "Field name matches a target, outcome, OOD, split, or correctness pattern.",
        )
    return _policy(
        POLICY_UNRESOLVED,
        "unresolved",
        "no",
        "unresolved",
        "unresolved",
        "unknown",
        "No reviewed Paper 3 policy exists for this field.",
        verified="UNRESOLVED",
    )


def _looks_forbidden(field: str) -> bool:
    lowered = field.lower()
    if lowered in LABEL_OR_OUTCOME_FIELDS:
        return True
    tokens = ("label", "target", "is_ood", "ood_label", "correct", "ground_truth")
    return any(token in lowered for token in tokens)


def _association_profile(series: pd.Series, target: pd.Series) -> dict[str, float | int | str]:
    work = pd.DataFrame({"field": series, "target": target})
    work = work.loc[work["field"].str.strip().ne("") & work["target"].str.strip().ne("")]
    if work.empty:
        return {"target_purity": "", "single_target_group_fraction": "", "average_group_size": ""}
    counts = work.groupby(["field", "target"], sort=False).size()
    purity = float(counts.groupby(level=0).max().sum() / len(work))
    target_counts = work.groupby("field", sort=False)["target"].nunique()
    group_count = int(len(target_counts))
    return {
        "target_purity": round(purity, 6),
        "single_target_group_fraction": round(float((target_counts == 1).mean()), 6),
        "average_group_size": round(float(len(work) / group_count), 6),
    }


def _target_baseline(target: pd.Series) -> float | str:
    valid = target.loc[target.str.strip().ne("")]
    if valid.empty:
        return ""
    return round(float(valid.value_counts().max() / len(valid)), 6)


def _near_exact_proxy(association: Mapping[str, Any], total_count: int) -> bool:
    purity = association.get("target_purity")
    group_size = association.get("average_group_size")
    if purity == "" or group_size == "":
        return False
    return float(purity) >= 0.98 and float(group_size) >= 2 and total_count > 0


def _contains_target_token(dataset: str, series: pd.Series) -> bool:
    values = series.loc[series.str.strip().ne("")].drop_duplicates().head(5000)
    tokens = TARGET_TOKENS[dataset]
    for value in values:
        normalized = str(value).lower()
        parts = set(re.findall(r"[a-z0-9]+", normalized))
        if tokens & parts:
            return True
        if dataset == "deepsense" and any(token in normalized for token in tokens):
            return True
    return False


def _infer_dtype(series: pd.Series) -> str:
    valid = series.loc[series.str.strip().ne("")]
    if valid.empty:
        return "empty"
    lowered = {str(value).lower() for value in valid.drop_duplicates().head(1000)}
    if lowered <= {"true", "false"}:
        return "bool"
    if valid.str.fullmatch(r"[-+]?\d+").all():
        if valid.str.fullmatch(r"0\d+").any():
            return "string (leading-zero symbolic values present)"
        return "int64-like"
    numeric = pd.to_numeric(valid, errors="coerce")
    if numeric.notna().all():
        return "float64-like"
    return "string"


def _short_examples(dataset: str, field: str, series: pd.Series, limit: int = 6) -> str:
    values = series.loc[series.str.strip().ne("")].drop_duplicates().head(limit)
    examples: list[str] = []
    for value in values:
        text = str(value)
        if field == "rx_id" or field.endswith("sensor_id"):
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
            examples.append(f"<id:{digest}>")
        elif "path" in field:
            examples.append(Path(text.replace("\\", "/")).name[:80])
        else:
            examples.append(text[:80])
    return " | ".join(examples)


def _parse_frequency_band(value: Any) -> tuple[float, float] | None:
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*", str(value))
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def _source_signature(paths: Iterable[Path]) -> str:
    rows: list[str] = []
    for path in paths:
        if not path.exists():
            rows.append(f"{path.name}\0MISSING")
            continue
        stat = path.stat()
        rows.append(f"{path.name}\0{stat.st_size}\0{stat.st_mtime_ns}")
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


def _validate_output_location(output_dir: Path, artifact_dirs: Iterable[Path]) -> None:
    output = output_dir.resolve()
    for artifact in artifact_dirs:
        source = Path(artifact).resolve()
        try:
            output.relative_to(source)
        except ValueError:
            continue
        raise ValueError(f"Audit output directory must not be inside a source artifact: {output}")


def _relation_coverage_summary(
    audit: pd.DataFrame,
    whitelists: Mapping[str, Iterable[str]],
) -> pd.DataFrame:
    potential = audit.loc[
        audit["field"].isin(
            {
                "rx_id",
                "domain_id",
                "frequency_band",
                "time_index",
                "source_capture_id",
                "source_date_id",
                "source_row_index",
                "source_sensor_id",
                "source_frequency_band",
                "band_lower_mhz",
                "band_upper_mhz",
                "band_center_mhz",
            }
        )
    ].copy()
    rows = []
    for item in potential.to_dict(orient="records"):
        dataset = item["dataset"]
        policy = _field_policy(dataset, item["field"])
        unique_count = int(item["unique_count"])
        rows.append(
            {
                "dataset": dataset,
                "field": item["field"],
                "policy_class": policy.policy_class,
                "allowed_by_whitelist": item["field"] in set(whitelists.get(dataset, ())),
                "availability_fraction": item["availability_fraction"],
                "unique_count": unique_count,
                "average_group_size": round(item["total_count"] / unique_count, 6)
                if unique_count
                else "",
                "target_purity": item["target_purity"],
                "target_baseline": item["target_baseline"],
                "relation_candidate": item["relation_candidate"],
                "temporal_candidate": item["temporal_candidate"],
                "leakage_risk": item["leakage_risk"],
                "proposed_relation_type": item["proposed_relation_type"],
                "notes": item["notes"],
            }
        )
    return pd.DataFrame(rows, columns=RELATION_COVERAGE_COLUMNS).sort_values(
        ["dataset", "field"], ignore_index=True
    )


def _dataset_relation_summary(
    audit: pd.DataFrame,
    artifact_summaries: list[dict[str, Any]],
    whitelists: Mapping[str, Iterable[str]],
) -> pd.DataFrame:
    summaries = {item["dataset"]: item for item in artifact_summaries}
    rows = []
    for dataset in sorted(summaries):
        summary = summaries[dataset]
        dataset_audit = audit.loc[audit["dataset"] == dataset]
        allowed = sorted(set(whitelists.get(dataset, ())))
        allowed_rows = dataset_audit.loc[dataset_audit["field"].isin(allowed)]
        coverages = pd.to_numeric(allowed_rows["availability_fraction"], errors="coerce")
        verdict, static_verdict, dynamic_verdict, notes = DATASET_VERDICTS[dataset]
        rows.append(
            {
                "dataset": dataset,
                "artifact_source": summary["artifact_source"],
                "metadata_rows": summary["metadata_rows"],
                "metadata_column_count": summary["metadata_column_count"],
                "feature_shape": summary["feature_shape"],
                "feature_dtype": summary["feature_dtype"],
                "source_file_count": summary["source_file_count"],
                "allowed_relation_fields": " | ".join(allowed),
                "allowed_relation_count": len(allowed),
                "minimum_allowed_relation_coverage": round(float(coverages.min()), 6)
                if not coverages.empty
                else 0.0,
                "target_proxy_field_count": int(
                    (
                        dataset_audit["target_or_label_related"].eq("yes")
                        & pd.to_numeric(dataset_audit["non_null_count"], errors="coerce").gt(0)
                    ).sum()
                ),
                "temporal_relation_defensible": False,
                "dataset_verdict": verdict,
                "static_verdict": static_verdict,
                "dynamic_verdict": dynamic_verdict,
                "notes": notes,
            }
        )
    return pd.DataFrame(rows, columns=DATASET_SUMMARY_COLUMNS)


def _max_risk(left: str, right: str) -> str:
    order = {"unknown": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    return left if order.get(left, 0) >= order.get(right, 0) else right


def _subtract(left: Any, right: Any) -> float | None:
    try:
        return float(left) - float(right)
    except (TypeError, ValueError):
        return None


def _round_or_blank(value: float | None) -> float | str:
    if value is None or not math.isfinite(value):
        return ""
    return round(value, 6)
