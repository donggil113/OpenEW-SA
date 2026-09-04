"""Frozen post-hoc addendum contract and fail-closed labels."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Iterable

from openew.paper3.wisig.archive import sha256_file

ADDENDUM_SEEDS = (829, 1829, 2829, 3829, 4829)
PRIMARY_SUPPORT_BUDGET = 128
PRIMARY_CONTEXT_K = 32
SUPPORT_BUDGETS = (16, 32, 64, 128, 256)
EXPECTED_RECEIVERS = 32
PR85_MERGE_SHA = "48cec06645736bd45c455a64841f3f50e0368b40"
FROZEN_DATA_MANIFEST_SHA256 = "ffd98dcb8182435c1aaf416c3bb137e6f56f353811e7d1d7a6fc0cc4817ae4b6"
FROZEN_SPLIT_FREEZE_SHA256 = "2be7d03278daa3239789645a8fe1ad1876a796f9acfe140aa8e267be05bf1212"
FROZEN_PREDICTION_MANIFEST_SHA256 = "9e80ed7a25ddcf3d9aa3365d0a687eb9549257cbf789040cdc71c20391c2e1f1"


class EvidenceCategory(str, Enum):
    DEPLOYABLE_METHOD = "DEPLOYABLE_METHOD"
    LABEL_FREE_CONTROL = "LABEL_FREE_CONTROL"
    ORACLE_DIAGNOSTIC = "ORACLE_DIAGNOSTIC"


_CATEGORY = {
    "DISJOINT_NATURAL": EvidenceCategory.DEPLOYABLE_METHOD,
    "NATURAL": EvidenceCategory.DEPLOYABLE_METHOD,
    "QUERY_COUPLED_CHUNK": EvidenceCategory.LABEL_FREE_CONTROL,
    "FULL_RECEIVER_PARTITION": EvidenceCategory.LABEL_FREE_CONTROL,
    "SHUFFLED": EvidenceCategory.LABEL_FREE_CONTROL,
    "NULL": EvidenceCategory.LABEL_FREE_CONTROL,
    "MISMATCHED_RX": EvidenceCategory.LABEL_FREE_CONTROL,
    "SAME_CLASS_EXCLUDED_ORACLE": EvidenceCategory.ORACLE_DIAGNOSTIC,
    "SAME_CLASS_ONLY_ORACLE": EvidenceCategory.ORACLE_DIAGNOSTIC,
    "TRANSMITTER_PURE_ORACLE": EvidenceCategory.ORACLE_DIAGNOSTIC,
}


def classify_condition(condition: str) -> EvidenceCategory:
    try:
        return _CATEGORY[str(condition).upper()]
    except KeyError as exc:
        raise ValueError(f"unregistered addendum condition: {condition}") from exc


def validate_seed(seed: int) -> int:
    if int(seed) not in ADDENDUM_SEEDS:
        raise ValueError(f"seed must be one of {ADDENDUM_SEEDS}")
    return int(seed)


def validate_support_budget(budget: int) -> int:
    if int(budget) not in SUPPORT_BUDGETS:
        raise ValueError(f"budget must be one of {SUPPORT_BUDGETS}")
    return int(budget)


def require_posthoc_output_path(path: str | Path, frozen_v2_root: str | Path) -> Path:
    destination = Path(path).resolve()
    frozen = Path(frozen_v2_root).resolve()
    if destination == frozen or frozen in destination.parents:
        raise ValueError("addendum output cannot be written inside the frozen V2 root")
    return destination


def require_unique(values: Iterable[str], *, name: str) -> tuple[str, ...]:
    result = tuple(str(value) for value in values)
    if len(result) != len(set(result)):
        raise ValueError(f"{name} contains duplicates")
    return result


def verify_frozen_v2_inputs(v2_root: str | Path, raw_converted_root: str | Path) -> dict[str, object]:
    """Verify only immutable manifests; never hashes every checkpoint repeatedly."""

    v2_root = Path(v2_root)
    pre = v2_root / "analysis" / "pre_unblinding_freeze.json"
    split = v2_root / "splits_v2_frozen" / "split_freeze_manifest.json"
    data = Path(raw_converted_root) / "dataset_manifest.json"
    required = (pre, split, data)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing frozen input manifests: {missing}")
    split_sha = sha256_file(split)
    data_sha = sha256_file(data)
    if split_sha != FROZEN_SPLIT_FREEZE_SHA256:
        raise RuntimeError("frozen V2 split manifest hash mismatch")
    if data_sha != FROZEN_DATA_MANIFEST_SHA256:
        raise RuntimeError("frozen WiSig data manifest hash mismatch")
    return {
        "status": "PASS",
        "pre_unblinding_freeze_sha256": sha256_file(pre),
        "split_freeze_sha256": split_sha,
        "data_manifest_sha256": data_sha,
        "expected_prediction_manifest_sha256": FROZEN_PREDICTION_MANIFEST_SHA256,
    }
