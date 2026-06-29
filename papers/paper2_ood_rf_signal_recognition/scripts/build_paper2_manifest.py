#!/usr/bin/env python
"""Build a unified Paper 2 manifest from OpenEW-SA processed artifacts.

The manifest is a lightweight index over existing converted artifacts. It records one row per
sample and points back to the shared feature tensor plus row index, leaving model-specific feature
loading to the future Paper 2 experiment runner.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML is a project dependency.
    yaml = None

MANIFEST_COLUMNS = [
    "sample_id",
    "dataset_source",
    "task",
    "label",
    "domain_id",
    "input_type",
    "feature_path",
    "feature_index",
    "split_hint",
    "source_artifact_dir",
]

DEFAULT_ARTIFACT_DIRS = [
    Path(r"D:\openew_sa_data\processed\jamshield"),
    Path(r"D:\openew_sa_data\processed\deepsense"),
    Path(r"D:\openew_sa_data\processed\electrosense"),
]

DEFAULT_DATASET_SPECS = {
    "jamshield": {
        "task": "jamming_interference_detection",
        "label_column": "abnormal_event_label",
    },
    "deepsense": {
        "task": "wifi_occupancy_classification",
        "label_column": "occupancy_label",
    },
    "electrosense": {
        "task": "psd_technology_recognition",
        "label_column": "situation_label",
    },
}

LABEL_COLUMN_PRIORITY = [
    "modulation_label",
    "occupancy_label",
    "abnormal_event_label",
    "situation_label",
    "threat_level",
]
SPLIT_HINT_COLUMNS = ["split_hint", "split", "paper2_split", "split_name", "fold"]


@dataclass(frozen=True)
class ArtifactSpec:
    """Configuration for one OpenEW-SA processed artifact directory."""

    path: Path
    dataset_source: str | None = None
    task: str | None = None
    label_column: str | None = None


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Build a unified Paper 2 manifest from OpenEW-SA processed artifact directories.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", type=Path, help="YAML config with artifact directories and output path.")
    parser.add_argument(
        "--artifact-dir",
        action="append",
        help="Processed artifact directory. Comma-separated values may be repeated.",
    )
    parser.add_argument("--output", type=Path, help="Output manifest CSV path.")
    parser.add_argument("--limit", type=int, help="Maximum rows to read per artifact for smoke tests.")
    parser.add_argument("--dry-run", action="store_true", help="Read inputs and print a summary without writing CSV.")
    parser.add_argument(
        "--skip-missing",
        action="store_true",
        help="Skip missing artifact directories instead of failing.",
    )
    return parser.parse_args()


def main() -> None:
    """Build and optionally write the Paper 2 manifest."""

    args = parse_args()
    config = _load_config(args.config)
    specs = _resolve_artifact_specs(args, config)
    output = _resolve_output_path(args, config)
    limit = args.limit if args.limit is not None else _config_value(config, ("limit",))
    skip_missing = bool(args.skip_missing or _config_value(config, ("skip_missing",), default=False))

    manifest, summary = build_manifest(specs, limit=_optional_int(limit), skip_missing=skip_missing)
    summary["output"] = str(output)
    summary["dry_run"] = bool(args.dry_run)

    if args.dry_run:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(output, index=False)
    summary_path = output.with_name(f"{output.stem}.summary.json")
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


def build_manifest(
    specs: list[ArtifactSpec],
    limit: int | None = None,
    skip_missing: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return the unified manifest and a summary for the provided artifact specs."""

    if limit is not None and limit <= 0:
        raise ValueError("--limit must be a positive integer when provided.")
    frames: list[pd.DataFrame] = []
    artifacts: list[dict[str, Any]] = []
    warnings: list[str] = []

    for spec in specs:
        artifact_summary, frame = _manifest_from_artifact(spec, limit=limit, skip_missing=skip_missing)
        artifacts.append(artifact_summary)
        warnings.extend(artifact_summary.get("warnings", []))
        if frame is not None and not frame.empty:
            frames.append(frame)

    if not frames:
        raise ValueError("No manifest rows were built from the provided artifact directories.")

    manifest = pd.concat(frames, ignore_index=True).loc[:, MANIFEST_COLUMNS]
    summary = {
        "num_rows": int(len(manifest)),
        "num_artifacts": int(len([artifact for artifact in artifacts if not artifact.get("skipped")])),
        "columns": MANIFEST_COLUMNS,
        "artifacts": artifacts,
        "warnings": warnings,
    }
    return manifest, summary


def _manifest_from_artifact(
    spec: ArtifactSpec,
    limit: int | None,
    skip_missing: bool,
) -> tuple[dict[str, Any], pd.DataFrame | None]:
    artifact_dir = spec.path
    summary: dict[str, Any] = {
        "artifact_dir": str(artifact_dir),
        "skipped": False,
        "warnings": [],
    }
    if not artifact_dir.exists():
        if skip_missing:
            summary["skipped"] = True
            summary["warnings"].append(f"Missing artifact directory skipped: {artifact_dir}")
            return summary, None
        raise FileNotFoundError(f"Artifact directory not found: {artifact_dir}")

    metadata_path = artifact_dir / "metadata.csv"
    labels_path = artifact_dir / "labels.json"
    features_path = artifact_dir / "features.npy"
    if not metadata_path.exists():
        if skip_missing:
            summary["skipped"] = True
            summary["warnings"].append(f"Missing metadata.csv skipped: {metadata_path}")
            return summary, None
        raise FileNotFoundError(f"metadata.csv not found: {metadata_path}")

    labels = _read_json(labels_path)
    metadata = pd.read_csv(metadata_path, dtype=str, keep_default_na=False)
    if metadata.empty:
        raise ValueError(f"metadata.csv is empty: {metadata_path}")
    metadata_row_count = len(metadata)

    dataset_source = _resolve_dataset_source(spec, labels, metadata, artifact_dir)
    dataset_defaults = DEFAULT_DATASET_SPECS.get(dataset_source.lower(), {})
    label_column = spec.label_column or labels.get("label_column") or dataset_defaults.get("label_column")
    if label_column is None:
        label_column = _infer_label_column(labels, metadata)
    if label_column not in metadata.columns:
        raise ValueError(
            f"Label column '{label_column}' not found in {metadata_path}. "
            f"Available columns: {metadata.columns.tolist()}"
        )

    task = spec.task or dataset_defaults.get("task") or _task_from_label_column(label_column)
    feature_row_count = _feature_row_count(features_path)
    if feature_row_count is not None and feature_row_count != len(metadata):
        summary["warnings"].append(
            f"{features_path} has {feature_row_count} rows but metadata has {len(metadata)} rows."
        )

    metadata = metadata.reset_index(drop=True)
    metadata["_paper2_feature_index"] = metadata.index
    if limit is not None:
        metadata = metadata.head(limit).copy()

    split_hint_column = _first_existing_column(metadata, SPLIT_HINT_COLUMNS)
    manifest = pd.DataFrame(
        {
            "sample_id": _column_or_generated(metadata, "sample_id", dataset_source),
            "dataset_source": _text_column(metadata, "dataset_source", dataset_source),
            "task": task,
            "label": _text_column(metadata, label_column),
            "domain_id": _text_column(metadata, "domain_id"),
            "input_type": _text_column(metadata, "input_type"),
            "feature_path": str(features_path) if features_path.exists() else "",
            "feature_index": metadata["_paper2_feature_index"].astype(int),
            "split_hint": _text_column(metadata, split_hint_column) if split_hint_column else "",
            "source_artifact_dir": str(artifact_dir),
        }
    )
    summary.update(
        {
            "dataset_source": dataset_source,
            "task": task,
            "label_column": label_column,
            "metadata_path": str(metadata_path),
            "labels_path": str(labels_path) if labels_path.exists() else "",
            "feature_path": str(features_path) if features_path.exists() else "",
            "feature_rows": feature_row_count,
            "metadata_rows": int(metadata_row_count),
            "manifest_rows": int(len(manifest)),
            "split_hint_column": split_hint_column or "",
        }
    )
    return summary, manifest


def _resolve_artifact_specs(args: argparse.Namespace, config: dict[str, Any]) -> list[ArtifactSpec]:
    cli_dirs = _list_option(args.artifact_dir)
    if cli_dirs:
        return [ArtifactSpec(path=Path(path)) for path in cli_dirs]

    config_specs = _config_value(config, ("artifacts",), ("artifact_dirs",))
    if config_specs:
        specs = []
        for item in config_specs:
            if isinstance(item, str):
                specs.append(ArtifactSpec(path=Path(item)))
            elif isinstance(item, dict):
                specs.append(
                    ArtifactSpec(
                        path=Path(str(item["path"])),
                        dataset_source=item.get("dataset_source"),
                        task=item.get("task"),
                        label_column=item.get("label_column"),
                    )
                )
            else:
                raise ValueError(f"Unsupported artifact spec: {item!r}")
        return specs

    return [ArtifactSpec(path=path) for path in DEFAULT_ARTIFACT_DIRS]


def _resolve_output_path(args: argparse.Namespace, config: dict[str, Any]) -> Path:
    output = args.output or _config_value(
        config,
        ("output",),
        ("output_manifest",),
        ("outputs", "manifest_csv"),
    )
    if output:
        return Path(output)
    return Path(r"D:\openew_sa_data\paper2\manifests\paper2_manifest.csv")


def _load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    if yaml is None:
        raise RuntimeError("PyYAML is required to read --config files.")
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Config must be a YAML mapping: {path}")
    return loaded


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    return loaded if isinstance(loaded, dict) else {}


def _resolve_dataset_source(
    spec: ArtifactSpec,
    labels: dict[str, Any],
    metadata: pd.DataFrame,
    artifact_dir: Path,
) -> str:
    if spec.dataset_source:
        return spec.dataset_source
    labels_source = labels.get("dataset_source")
    if labels_source:
        return str(labels_source)
    if "dataset_source" in metadata.columns and not metadata["dataset_source"].dropna().empty:
        return str(metadata["dataset_source"].dropna().astype(str).mode().iloc[0])
    return artifact_dir.name


def _infer_label_column(labels: dict[str, Any], metadata: pd.DataFrame) -> str:
    class_names = labels.get("class_names")
    if isinstance(class_names, dict):
        for column in LABEL_COLUMN_PRIORITY:
            if column in class_names and column in metadata.columns:
                return column
    for column in LABEL_COLUMN_PRIORITY:
        if column in metadata.columns and metadata[column].fillna("").astype(str).ne("").any():
            return column
    raise ValueError("Could not infer a label column from labels.json or metadata.csv.")


def _task_from_label_column(label_column: str) -> str:
    return {
        "modulation_label": "modulation_recognition",
        "occupancy_label": "occupancy_classification",
        "abnormal_event_label": "interference_detection",
        "situation_label": "situation_recognition",
        "threat_level": "threat_level_classification",
    }.get(label_column, f"{label_column}_classification")


def _feature_row_count(path: Path) -> int | None:
    if not path.exists():
        return None
    import numpy as np

    features = np.load(path, mmap_mode="r")
    return int(features.shape[0])


def _first_existing_column(frame: pd.DataFrame, columns: list[str]) -> str | None:
    for column in columns:
        if column in frame.columns:
            return column
    return None


def _column_or_generated(frame: pd.DataFrame, column: str, prefix: str) -> pd.Series:
    if column in frame.columns:
        return frame[column].fillna("").astype(str)
    return pd.Series([f"{prefix}_{index:08d}" for index in range(len(frame))])


def _text_column(frame: pd.DataFrame, column: str | None, default: str = "") -> pd.Series | str:
    if column and column in frame.columns:
        return frame[column].fillna("").astype(str)
    return default


def _list_option(values: list[str] | None) -> list[str]:
    if values is None:
        return []
    parsed: list[str] = []
    for value in values:
        parsed.extend(part.strip() for part in str(value).split(",") if part.strip())
    return parsed


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _config_value(
    config: dict[str, Any],
    *paths: tuple[str, ...],
    default: Any | None = None,
) -> Any:
    for path in paths:
        current: Any = config
        for key in path:
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]
        if current not in (None, ""):
            return current
    return default


if __name__ == "__main__":
    main()
