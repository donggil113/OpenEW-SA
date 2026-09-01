"""Executable relation whitelist and split-isolation contract."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

import numpy as np

from openew.paper3.relational_audit import DEFAULT_RELATION_WHITELISTS, validate_relation_fields


class LeakageContractViolation(RuntimeError):
    """Raised when a requested graph construction violates the frozen policy."""


class SplitContaminationError(LeakageContractViolation):
    """Raised when a relation group crosses dataset partitions."""


RELATION_FIELDS: dict[str, dict[str, tuple[str, ...]]] = {
    "jamshield": {"station": ("rx_id",)},
    "deepsense": {},
    "electrosense": {
        "receiver": ("rx_id",),
        "date": ("source_date_id",),
        "receiver_date": ("rx_id", "source_date_id"),
    },
}

STAGE_RELATIONS: dict[str, dict[str, tuple[str, ...]]] = {
    "jamshield": {"m0": (), "m1": ("station",), "m2": ("station",)},
    "deepsense": {"m0": ()},
    "electrosense": {
        "m0": (),
        "m1": ("receiver", "date"),
        "m2": ("receiver", "date", "receiver_date"),
    },
}

EXPLICITLY_FORBIDDEN_FIELDS = frozenset(
    {
        "domain_id",
        "frequency_band",
        "band_lower_mhz",
        "band_upper_mhz",
        "band_center_mhz",
        "source_capture_id",
        "source_relative_path",
        "source_file",
        "source_path",
        "scenario",
        "split",
        "target",
        "true_label",
        "label",
        "ood_label",
        "is_ood",
        "correctness",
        "prediction",
        "predicted_label",
        "heldout_performance",
    }
)


def validate_relation_types(dataset: str, relation_types: Iterable[str]) -> tuple[str, ...]:
    """Validate relation types and their underlying fields against the merged audit."""

    dataset_key = str(dataset).lower()
    if dataset_key not in RELATION_FIELDS:
        raise LeakageContractViolation(f"Unsupported Paper 3 dataset: {dataset}")
    requested = tuple(str(item) for item in relation_types)
    if len(set(requested)) != len(requested):
        raise LeakageContractViolation(f"Duplicate relation type requested: {requested}")
    unknown = sorted(set(requested) - set(RELATION_FIELDS[dataset_key]))
    if unknown:
        raise LeakageContractViolation(
            f"Relation types are not allowed for {dataset_key}: {unknown}"
        )
    fields = {field for name in requested for field in RELATION_FIELDS[dataset_key][name]}
    forbidden = sorted(fields & EXPLICITLY_FORBIDDEN_FIELDS)
    if forbidden:
        raise LeakageContractViolation(f"Forbidden relation fields requested: {forbidden}")
    try:
        validate_relation_fields(dataset_key, fields, DEFAULT_RELATION_WHITELISTS[dataset_key])
    except ValueError as error:
        raise LeakageContractViolation(str(error)) from error
    if dataset_key == "deepsense" and requested:
        raise LeakageContractViolation("DeepSense has no leakage-safe Paper 3 relation")
    return requested


def relation_fields(dataset: str, relation_type: str) -> tuple[str, ...]:
    validate_relation_types(dataset, (relation_type,))
    return RELATION_FIELDS[dataset][relation_type]


def validate_partition_membership(
    group_ids_by_type: Mapping[str, np.ndarray], partition_ids: np.ndarray
) -> None:
    """Prove that no non-isolated group identifier spans partitions."""

    partition_ids = np.asarray(partition_ids).astype(str)
    for relation_type, group_ids in group_ids_by_type.items():
        groups = np.asarray(group_ids, dtype=np.int64)
        if len(groups) != len(partition_ids):
            raise SplitContaminationError(
                f"Partition/group length mismatch for {relation_type}: {len(groups)} != {len(partition_ids)}"
            )
        for group_id in np.unique(groups[groups >= 0]):
            touched = np.unique(partition_ids[groups == group_id])
            if len(touched) > 1:
                raise SplitContaminationError(
                    f"Relation {relation_type} group {group_id} crosses partitions: {touched.tolist()}"
                )
