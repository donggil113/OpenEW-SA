"""Receiver-level LOSO and secondary split freezes for WiSig V2."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from openew.paper3.wisig.validation import load_converted_tables

from .hashing import canonical_json_bytes, sha256_file, stable_digest


@dataclass(frozen=True)
class SupportThresholds:
    train_per_class: int = 100
    validation_per_class: int = 20
    query_per_class: int = 20


def select_validation_receivers(
    receivers: list[str] | tuple[str, ...],
    test_receiver: str,
    hardware_by_receiver: Mapping[str, str],
    *,
    count: int = 3,
) -> tuple[str, ...]:
    """Select source-validation receivers by hardware coverage then stable hash."""

    candidates = sorted(set(map(str, receivers)) - {str(test_receiver)})
    if len(candidates) < count:
        raise ValueError("not enough receivers for source validation")
    selected: list[str] = []
    families = sorted({str(hardware_by_receiver.get(receiver, "UNKNOWN")) for receiver in candidates})
    for family in families:
        family_candidates = [receiver for receiver in candidates if str(hardware_by_receiver.get(receiver, "UNKNOWN")) == family]
        if family_candidates and len(selected) < count:
            selected.append(min(family_candidates, key=lambda receiver: stable_digest(test_receiver, receiver, namespace="wisig-v2-val-hardware")))
    remaining = [receiver for receiver in candidates if receiver not in selected]
    remaining.sort(key=lambda receiver: stable_digest(test_receiver, receiver, namespace="wisig-v2-val-fill"))
    selected.extend(remaining[: max(0, count - len(selected))])
    return tuple(sorted(selected[:count]))


def _support_table(joined: pd.DataFrame, assignments: pd.Series) -> dict[str, dict[str, int]]:
    table = pd.crosstab(joined["transmitter_id"], assignments)
    return {
        str(target): {str(split): int(value) for split, value in row.items()}
        for target, row in table.sort_index().iterrows()
    }


def _eligible(support: Mapping[str, Mapping[str, int]], thresholds: SupportThresholds) -> tuple[str, ...]:
    return tuple(
        sorted(
            target
            for target, row in support.items()
            if row.get("train", 0) >= thresholds.train_per_class
            and row.get("validation", 0) >= thresholds.validation_per_class
            and row.get("test", 0) >= thresholds.query_per_class
        )
    )


def _write_protocol(
    output_root: Path,
    protocol_id: str,
    joined: pd.DataFrame,
    assignments: pd.Series,
    assignment_metadata: dict[str, Any],
    thresholds: SupportThresholds,
    fixed_eligible: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    support = _support_table(joined, assignments)
    feasible = _eligible(support, thresholds)
    eligible = fixed_eligible or feasible
    if not set(eligible).issubset(feasible):
        raise ValueError(f"fixed eligible transmitter set is infeasible in {protocol_id}")
    if not eligible:
        raise ValueError(f"no eligible transmitters in {protocol_id}")
    include = joined["transmitter_id"].astype(str).isin(eligible)
    manifest = pd.DataFrame({"sample_id": joined.loc[include, "sample_id"].astype(str), "split": assignments.loc[include].astype(str)})
    if manifest["sample_id"].duplicated().any():
        raise ValueError(f"sample overlap in {protocol_id}")
    if set(manifest["split"]) != {"train", "validation", "test"}:
        raise ValueError(f"split role missing in {protocol_id}")
    destination = output_root / protocol_id
    destination.mkdir(parents=True, exist_ok=False)
    path = destination / "split_manifest.csv"
    manifest.to_csv(path, index=False, lineterminator="\n")
    summary = {
        "schema_version": 2,
        "protocol_id": protocol_id,
        "protocol_type": assignment_metadata["protocol_type"],
        "sample_count": len(manifest),
        "split_counts": {str(key): int(value) for key, value in manifest["split"].value_counts().sort_index().items()},
        "eligible_transmitter_ids": list(eligible),
        "eligible_transmitter_count": len(eligible),
        "support_thresholds": asdict(thresholds),
        "per_class_support": {target: support[target] for target in eligible},
        "assignment_metadata": assignment_metadata,
        "split_manifest_sha256": sha256_file(path),
        "target_used_for_split_support_audit_only": True,
        "test_receiver_is_primary_unit": assignment_metadata["protocol_type"] == "receiver_loso",
        "target_receiver_context_is_not_domain_generalization_training_data": True,
        "model_visible_split_fields": [],
        "source_paths_emitted": False,
    }
    summary_path = destination / "split_summary.json"
    summary_path.write_bytes(canonical_json_bytes(summary))
    summary["split_summary_sha256"] = sha256_file(summary_path)
    return summary


def _balanced_receiver_groups(
    joined: pd.DataFrame,
    receivers: tuple[str, ...],
    hardware: Mapping[str, str],
    repeat: int,
    fold_count: int = 4,
) -> tuple[tuple[str, ...], ...]:
    contingency = pd.crosstab(joined["receiver_id"], joined["transmitter_id"]).reindex(receivers).fillna(0)
    ordered = sorted(receivers, key=lambda receiver: (-int(contingency.loc[receiver].sum()), stable_digest(repeat, receiver, namespace="wisig-v2-grouped")))
    capacities = [len(ordered) // fold_count + int(index < len(ordered) % fold_count) for index in range(fold_count)]
    target = contingency.sum(axis=0).to_numpy(dtype=float) / fold_count
    fold_vectors = [np.zeros_like(target) for _ in range(fold_count)]
    folds: list[list[str]] = [[] for _ in range(fold_count)]
    hardware_counts = [dict() for _ in range(fold_count)]
    for receiver in ordered:
        vector = contingency.loc[receiver].to_numpy(dtype=float)
        family = str(hardware.get(receiver, "UNKNOWN"))
        choices: list[tuple[float, int]] = []
        for fold in range(fold_count):
            if len(folds[fold]) >= capacities[fold]:
                continue
            support_error = float(np.square(fold_vectors[fold] + vector - target).sum())
            family_penalty = float(hardware_counts[fold].get(family, 0)) * max(1.0, float(target.sum()))
            choices.append((support_error + family_penalty, fold))
        chosen = min(choices)[1]
        folds[chosen].append(receiver)
        fold_vectors[chosen] += vector
        hardware_counts[chosen][family] = hardware_counts[chosen].get(family, 0) + 1
    return tuple(tuple(sorted(fold)) for fold in folds)


def build_v2_splits(
    converted_root: str | Path,
    output_root: str | Path,
    hardware_by_receiver: Mapping[str, str],
    *,
    thresholds: SupportThresholds | None = None,
) -> dict[str, Any]:
    output_root = Path(output_root)
    if output_root.exists():
        raise FileExistsError(f"split freeze root exists: {output_root}")
    output_root.mkdir(parents=True)
    thresholds = thresholds or SupportThresholds()
    acquisition, annotations = load_converted_tables(converted_root)
    joined = acquisition[["sample_id", "receiver_id", "day_id"]].merge(
        annotations[["sample_id", "transmitter_id"]], on="sample_id", validate="one_to_one"
    )
    for column in ("sample_id", "receiver_id", "day_id", "transmitter_id"):
        joined[column] = joined[column].astype(str)
    receivers = tuple(sorted(joined["receiver_id"].unique()))
    if len(receivers) != 32:
        raise ValueError(f"V2 preregistration expects 32 compact ManyRx receivers, found {len(receivers)}")
    if set(hardware_by_receiver) != set(receivers):
        raise ValueError("hardware map must cover exactly the 32 receivers")
    protocols: list[dict[str, Any]] = []
    loso_map: dict[str, dict[str, Any]] = {}
    loso_specs: list[tuple[str, pd.Series, dict[str, Any]]] = []
    for index, test_receiver in enumerate(receivers):
        validation = select_validation_receivers(receivers, test_receiver, hardware_by_receiver, count=3)
        assignment = pd.Series("train", index=joined.index, dtype="string")
        assignment.loc[joined["receiver_id"].isin(validation)] = "validation"
        assignment.loc[joined["receiver_id"] == test_receiver] = "test"
        protocol_id = f"receiver_loso_{index:02d}"
        train_receivers = sorted(set(receivers) - set(validation) - {test_receiver})
        metadata = {
            "protocol_type": "receiver_loso",
            "test_receiver": test_receiver,
            "test_receiver_hardware": hardware_by_receiver[test_receiver],
            "validation_receivers": list(validation),
            "validation_hardware": {receiver: hardware_by_receiver[receiver] for receiver in validation},
            "train_receivers": train_receivers,
            "selection_rule": "one stable-hash receiver per official hardware family; no model metrics",
        }
        loso_specs.append((protocol_id, assignment, metadata))
        loso_map[protocol_id] = metadata

    common_eligible = tuple(sorted(set.intersection(*[set(_eligible(_support_table(joined, assignment), thresholds)) for _, assignment, _ in loso_specs])))
    if not common_eligible:
        raise ValueError("no common transmitter set satisfies every LOSO protocol")
    for protocol_id, assignment, metadata in loso_specs:
        protocols.append(_write_protocol(output_root, protocol_id, joined, assignment, metadata, thresholds, fixed_eligible=common_eligible))

    days = tuple(sorted(joined["day_id"].unique()))
    for index, test_day in enumerate(days):
        validation_day = days[(index + 1) % len(days)]
        assignment = pd.Series("train", index=joined.index, dtype="string")
        assignment.loc[joined["day_id"] == validation_day] = "validation"
        assignment.loc[joined["day_id"] == test_day] = "test"
        protocols.append(
            _write_protocol(
                output_root,
                f"day_lodo_{index}",
                joined,
                assignment,
                {
                    "protocol_type": "leave_one_day_out_secondary",
                    "test_day": test_day,
                    "validation_day": validation_day,
                    "train_days": sorted(set(days) - {test_day, validation_day}),
                    "day_is_split_only": True,
                },
                thresholds,
            )
        )

    grouped: dict[str, Any] = {}
    for repeat in range(3):
        folds = _balanced_receiver_groups(joined, receivers, hardware_by_receiver, repeat)
        grouped[f"repeat_{repeat}"] = [list(fold) for fold in folds]

    freeze = {
        "schema_version": 2,
        "status": "FROZEN_BEFORE_TARGET_METRICS",
        "receiver_count": len(receivers),
        "primary_loso_protocol_count": len(receivers),
        "secondary_day_protocol_count": len(days),
        "secondary_grouped_receiver_design": grouped,
        "hardware_by_receiver": dict(sorted(hardware_by_receiver.items())),
        "loso_mapping": loso_map,
        "thresholds": asdict(thresholds),
        "common_primary_eligible_transmitter_ids": list(common_eligible),
        "common_primary_eligible_transmitter_count": len(common_eligible),
        "protocols": protocols,
        "selection_performance_inputs": [],
        "target_metrics_observed": False,
    }
    path = output_root / "split_freeze_manifest.json"
    path.write_bytes(canonical_json_bytes(freeze))
    freeze["split_freeze_manifest_sha256"] = sha256_file(path)
    return freeze


def load_hardware_map(path: str | Path) -> dict[str, str]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    mapping = payload.get("receiver_hardware", payload)
    return {str(key): str(value) for key, value in mapping.items()}
