"""Support-only, deterministic WiSig receiver/day domain split construction."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .archive import sha256_file, write_json_atomic
from .provenance import canonical_json_bytes
from .validation import load_converted_tables


@dataclass(frozen=True)
class SupportThresholds:
    train_per_class: int = 100
    validation_per_class: int = 20
    test_per_class: int = 20


def _stable_digest(value: str, namespace: str) -> str:
    return hashlib.sha256(f"{namespace}\x1f{value}".encode("utf-8")).hexdigest()


def balanced_receiver_groups(joined: pd.DataFrame, fold_count: int = 5) -> tuple[tuple[str, ...], ...]:
    """Greedy support balancing using only receiver IDs and packet counts."""

    contingency = pd.crosstab(joined["receiver_id"], joined["transmitter_id"]).sort_index()
    receivers = sorted(
        contingency.index.astype(str),
        key=lambda receiver: (-int(contingency.loc[receiver].sum()), _stable_digest(receiver, "wisig-receiver-fold-v1")),
    )
    capacities = [len(receivers) // fold_count + int(index < len(receivers) % fold_count) for index in range(fold_count)]
    fold_vectors = [np.zeros(contingency.shape[1], dtype=np.int64) for _ in range(fold_count)]
    folds: list[list[str]] = [[] for _ in range(fold_count)]
    ideal = contingency.sum(axis=0).to_numpy(dtype=np.float64) / fold_count
    for receiver in receivers:
        vector = contingency.loc[receiver].to_numpy(dtype=np.int64)
        candidates: list[tuple[float, int, int, int]] = []
        for fold_index in range(fold_count):
            if len(folds[fold_index]) >= capacities[fold_index]:
                continue
            projected = fold_vectors[fold_index] + vector
            support_error = float(np.square(projected - ideal).sum())
            candidates.append((support_error, int(projected.sum()), len(folds[fold_index]), fold_index))
        chosen = min(candidates)[-1]
        folds[chosen].append(receiver)
        fold_vectors[chosen] += vector
    return tuple(tuple(sorted(group)) for group in folds)


def _class_support(joined: pd.DataFrame, split_series: pd.Series) -> dict[str, dict[str, int]]:
    table = pd.crosstab(joined["transmitter_id"], split_series)
    return {
        str(target): {str(split): int(count) for split, count in row.items()}
        for target, row in table.iterrows()
    }


def _eligible_targets(support: dict[str, dict[str, int]], thresholds: SupportThresholds) -> set[str]:
    return {
        target
        for target, values in support.items()
        if values.get("train", 0) >= thresholds.train_per_class
        and values.get("validation", 0) >= thresholds.validation_per_class
        and values.get("test", 0) >= thresholds.test_per_class
    }


def _write_split(root: Path, protocol_id: str, joined: pd.DataFrame, assignments: pd.Series, metadata: dict[str, Any], thresholds: SupportThresholds) -> dict[str, Any]:
    support = _class_support(joined, assignments)
    eligible = _eligible_targets(support, thresholds)
    if not eligible:
        raise ValueError(f"no transmitter class passes support thresholds for {protocol_id}")
    included = joined["transmitter_id"].isin(eligible)
    manifest = pd.DataFrame({"sample_id": joined.loc[included, "sample_id"], "split": assignments.loc[included]})
    if manifest["sample_id"].duplicated().any():
        raise ValueError(f"sample overlap in {protocol_id}")
    if set(manifest["split"]) != {"train", "validation", "test"}:
        raise ValueError(f"missing split role in {protocol_id}")
    destination = root / protocol_id
    destination.mkdir(parents=True, exist_ok=False)
    manifest_path = destination / "split_manifest.csv"
    manifest.to_csv(manifest_path, index=False, lineterminator="\n")
    included_support = {target: support[target] for target in sorted(eligible)}
    summary = {
        "protocol_id": protocol_id,
        "protocol_type": metadata["protocol_type"],
        "sample_count": len(manifest),
        "split_counts": {str(key): int(value) for key, value in manifest["split"].value_counts().sort_index().items()},
        "eligible_transmitter_ids": sorted(eligible),
        "eligible_transmitter_count": len(eligible),
        "support_thresholds": asdict(thresholds),
        "per_class_support": included_support,
        "assignment_metadata": metadata,
        "split_manifest_sha256": sha256_file(manifest_path),
        "target_used_for_support_feasibility_only": True,
        "model_relation_fields": ["receiver_id"],
        "split_only_fields": ["day_id"],
        "source_paths_emitted": False,
    }
    (destination / "split_summary.json").write_bytes(canonical_json_bytes(summary))
    summary["split_summary_sha256"] = sha256_file(destination / "split_summary.json")
    return summary


def build_all_splits(converted_root: str | Path, output_root: str | Path, thresholds: SupportThresholds | None = None) -> dict[str, Any]:
    thresholds = thresholds or SupportThresholds()
    output_root = Path(output_root)
    if output_root.exists():
        raise FileExistsError(f"split freeze root already exists: {output_root}")
    output_root.mkdir(parents=True)
    acquisition, annotations = load_converted_tables(converted_root)
    joined = acquisition[["sample_id", "receiver_id", "day_id"]].merge(
        annotations[["sample_id", "transmitter_id"]], on="sample_id", validate="one_to_one"
    )
    receiver_groups = balanced_receiver_groups(joined, 5)
    protocols: list[dict[str, Any]] = []
    for test_index, test_receivers in enumerate(receiver_groups):
        validation_index = (test_index + 1) % len(receiver_groups)
        validation_receivers = receiver_groups[validation_index]
        assignment = pd.Series("train", index=joined.index, dtype="string")
        assignment.loc[joined["receiver_id"].isin(validation_receivers)] = "validation"
        assignment.loc[joined["receiver_id"].isin(test_receivers)] = "test"
        protocols.append(
            _write_split(
                output_root,
                f"receiver_fold_{test_index}",
                joined,
                assignment,
                {
                    "protocol_type": "unseen_receiver",
                    "test_receivers": list(test_receivers),
                    "validation_receivers": list(validation_receivers),
                    "train_receivers": sorted(set(joined["receiver_id"]) - set(test_receivers) - set(validation_receivers)),
                    "receiver_values_are_split_metadata_not_model_embeddings": True,
                },
                thresholds,
            )
        )
    days = tuple(sorted(str(value) for value in joined["day_id"].unique()))
    for test_index, test_day in enumerate(days):
        validation_day = days[(test_index + 1) % len(days)]
        assignment = pd.Series("train", index=joined.index, dtype="string")
        assignment.loc[joined["day_id"] == validation_day] = "validation"
        assignment.loc[joined["day_id"] == test_day] = "test"
        protocols.append(
            _write_split(
                output_root,
                f"day_fold_{test_index}",
                joined,
                assignment,
                {
                    "protocol_type": "leave_one_day_out",
                    "test_day": test_day,
                    "validation_day": validation_day,
                    "train_days": sorted(set(days) - {test_day, validation_day}),
                    "day_is_split_only": True,
                },
                thresholds,
            )
        )

    # One support-predeclared secondary intersection stress protocol.
    test_receivers = receiver_groups[0]
    validation_receivers = receiver_groups[1]
    test_day = days[0]
    validation_day = days[1]
    is_test = joined["receiver_id"].isin(test_receivers) & (joined["day_id"] == test_day)
    is_validation = joined["receiver_id"].isin(validation_receivers) & (joined["day_id"] == validation_day)
    is_train = (~joined["receiver_id"].isin(test_receivers + validation_receivers)) & (~joined["day_id"].isin([test_day, validation_day]))
    stress_joined = joined.loc[is_test | is_validation | is_train].reset_index(drop=True)
    stress_assignment = pd.Series("train", index=stress_joined.index, dtype="string")
    stress_assignment.loc[stress_joined["receiver_id"].isin(validation_receivers) & (stress_joined["day_id"] == validation_day)] = "validation"
    stress_assignment.loc[stress_joined["receiver_id"].isin(test_receivers) & (stress_joined["day_id"] == test_day)] = "test"
    stress_summary = _write_split(
        output_root,
        "receiver_day_stress_0",
        stress_joined,
        stress_assignment,
        {
            "protocol_type": "secondary_receiver_day_intersection_stress",
            "test_receivers": list(test_receivers),
            "test_day": test_day,
            "validation_receivers": list(validation_receivers),
            "validation_day": validation_day,
            "train_receivers": sorted(set(joined["receiver_id"]) - set(test_receivers) - set(validation_receivers)),
            "train_days": sorted(set(days) - {test_day, validation_day}),
            "secondary_only": True,
        },
        thresholds,
    )
    protocols.append(stress_summary)
    freeze = {
        "schema_version": 1,
        "status": "FROZEN_SUPPORT_ONLY",
        "protocol_count": len(protocols),
        "receiver_fold_count": 5,
        "day_fold_count": 4,
        "secondary_stress_count": 1,
        "receiver_groups": [list(group) for group in receiver_groups],
        "days": list(days),
        "thresholds": asdict(thresholds),
        "protocols": protocols,
        "model_performance_observed": False,
        "selection_inputs": ["receiver_id", "day_id", "packet_count", "class_support"],
        "selection_forbidden_inputs": ["accuracy", "macro_f1", "loss", "target_test_performance"],
    }
    (output_root / "split_freeze_manifest.json").write_bytes(canonical_json_bytes(freeze))
    freeze["split_freeze_manifest_sha256"] = sha256_file(output_root / "split_freeze_manifest.json")
    return freeze
