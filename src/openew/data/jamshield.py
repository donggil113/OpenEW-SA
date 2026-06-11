"""JamShield Dataset conversion utilities for jamming/interference metrics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from openew.data.schema import MetadataRecord, records_to_frame, validate_metadata_frame

DATASET_SOURCE = "jamshield"
REQUIRED_COLUMNS = {"sample", "station", "attack"}
EXCLUDED_FEATURE_COLUMNS = REQUIRED_COLUMNS
NON_DATA_TOKENS = {
    "baseline_performance",
    "dataset_summary",
    "inspection",
    "jamshield_raw_inspection",
    "metadata",
    "task_summary",
}


def convert(config: dict[str, Any]) -> None:
    """Convert raw JamShield CSV files into OpenEW-SA artifacts."""

    raw_dir = Path(config.get("raw_dir") or config.get("input_dir", "data/raw/jamshield")).expanduser()
    output_dir = Path(config["output_dir"]).expanduser()
    files = _discover_jamshield_csvs(raw_dir)
    if not files:
        raise FileNotFoundError(f"No JamShield data CSV files found in {raw_dir}; download manually first.")

    frames: list[pd.DataFrame] = []
    source_files: list[dict[str, Any]] = []
    for path in files:
        frame = pd.read_csv(path)
        frame = _normalize_columns(frame)
        if not _is_data_frame(frame):
            continue
        relative_path = str(path.relative_to(raw_dir))
        frame["_source_relative_path"] = relative_path
        frame["_source_stem"] = path.stem
        frame["_source_row_index"] = np.arange(len(frame))
        frames.append(frame)
        source_files.append({"relative_path": relative_path, "row_count": len(frame)})

    if not frames:
        raise FileNotFoundError(f"No JamShield data CSV files with columns {sorted(REQUIRED_COLUMNS)} found in {raw_dir}.")

    combined = pd.concat(frames, ignore_index=True, sort=False)
    feature_columns = _infer_feature_columns(combined)
    features = _build_features(combined, feature_columns)
    metadata = _build_metadata(combined)
    labels = {
        "dataset_source": DATASET_SOURCE,
        "label_column": "abnormal_event_label",
        "class_names": {
            "abnormal_event_label": ["normal", "abnormal_interference"],
            "situation_label": ["normal", "abnormal"],
            "threat_level": ["low", "high"],
        },
        "feature_columns": feature_columns,
        "num_samples": len(metadata),
        "source_files": source_files,
    }
    _save_artifacts(output_dir, metadata, features, labels)


def _discover_jamshield_csvs(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw JamShield directory does not exist: {raw_dir}")
    return [
        path
        for path in sorted(raw_dir.rglob("*.csv"))
        if path.is_file() and not _looks_like_non_data_csv(path)
    ]


def _looks_like_non_data_csv(path: Path) -> bool:
    lowered = path.stem.lower()
    return any(token in lowered for token in NON_DATA_TOKENS)


def _is_data_frame(frame: pd.DataFrame) -> bool:
    return REQUIRED_COLUMNS.issubset({column.lower() for column in frame.columns})


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized.columns = [str(column).strip() for column in normalized.columns]
    normalized = normalized.rename(
        columns={column: column.lower() for column in normalized.columns if column.lower() in REQUIRED_COLUMNS}
    )
    return normalized


def _infer_feature_columns(frame: pd.DataFrame) -> list[str]:
    columns = [
        column
        for column in frame.columns
        if column.lower() not in EXCLUDED_FEATURE_COLUMNS and not column.startswith("_source_")
    ]
    numeric = frame[columns].apply(pd.to_numeric, errors="coerce")
    feature_columns = [column for column in columns if not numeric[column].isna().all()]
    if not feature_columns:
        raise ValueError("JamShield conversion found no numeric metric columns after excluding sample, station, and attack.")
    return feature_columns


def _build_features(frame: pd.DataFrame, feature_columns: list[str]) -> np.ndarray:
    numeric = frame[feature_columns].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    return numeric.to_numpy(dtype=np.float32)


def _build_metadata(frame: pd.DataFrame) -> pd.DataFrame:
    records: list[MetadataRecord] = []
    for index, row in frame.iterrows():
        attack = _attack_value(row["attack"])
        records.append(
            MetadataRecord(
                sample_id=f"jamshield_{index:08d}",
                dataset_source=DATASET_SOURCE,
                input_type="tabular_metrics",
                time_index=row.get("sample", index),
                frequency_band="wifi_unknown",
                tx_id="",
                rx_id=_string_or_empty(row.get("station")),
                modulation_label="",
                occupancy_label="",
                abnormal_event_label="abnormal_interference" if attack else "normal",
                domain_id=_string_or_empty(row.get("_source_stem")),
                synthetic_mission_context="routine_monitoring",
                situation_label="abnormal" if attack else "normal",
                threat_level="high" if attack else "low",
                human_review_required=bool(attack),
            )
        )
    return records_to_frame(records)


def _attack_value(value: Any) -> bool:
    if pd.isna(value):
        return False
    return int(float(value)) != 0


def _string_or_empty(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def _save_artifacts(output_dir: Path, metadata: pd.DataFrame, features: np.ndarray, labels: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    validate_metadata_frame(metadata).to_csv(output_dir / "metadata.csv", index=False)
    np.save(output_dir / "features.npy", features.astype(np.float32, copy=False))
    with (output_dir / "labels.json").open("w", encoding="utf-8") as handle:
        json.dump(labels, handle, indent=2, sort_keys=True)
