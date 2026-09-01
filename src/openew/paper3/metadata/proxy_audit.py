"""Label-aware safety diagnostics that never feed relation construction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import log
from typing import Iterable, Mapping, Sequence

import numpy as np
from sklearn.metrics import normalized_mutual_info_score

from .enums import Eligibility
from .leakage import EligibilityEngine
from .schema import AcquisitionRecord, AnnotationRecord


@dataclass(frozen=True)
class ProxyDiagnostic:
    field: str
    total_count: int
    non_null_count: int
    coverage: float
    unique_count: int
    group_size_min: int
    group_size_median: float
    group_size_mean: float
    group_size_max: int
    target_entropy: float
    conditional_target_entropy: float
    normalized_mutual_information: float
    weighted_group_purity: float
    one_to_one_target_mapping_rate: float
    near_deterministic_group_rate: float
    missingness_target_nmi: float
    classification: str
    reason: str

    def to_mapping(self) -> dict[str, object]:
        return asdict(self)


def audit_field(
    acquisition: Sequence[AcquisitionRecord],
    annotations: Sequence[AnnotationRecord],
    field: str,
    *,
    eligibility: EligibilityEngine,
    near_deterministic_threshold: float = 0.95,
) -> ProxyDiagnostic:
    if len({row.sample_id for row in acquisition}) != len(acquisition):
        raise ValueError("Duplicate acquisition sample IDs")
    labels = _annotation_index(annotations)
    paired = [row for row in acquisition if row.sample_id in labels]
    targets = [labels[row.sample_id] for row in paired]
    values = [getattr(row, field, None) for row in paired]
    populated = [(str(value), target) for value, target in zip(values, targets) if value not in (None, "")]
    groups: dict[str, list[str]] = {}
    for value, target in populated:
        groups.setdefault(value, []).append(target)
    sizes = np.asarray([len(group) for group in groups.values()], dtype=float)
    target_entropy = _entropy(targets)
    conditional = _conditional_entropy(groups)
    nmi = (
        float(normalized_mutual_info_score([value for value, _ in populated], [target for _, target in populated]))
        if populated and len(set(target for _, target in populated)) > 1
        else 0.0
    )
    purity_by_group = [_purity(group) for group in groups.values()]
    weighted_purity = (
        sum(len(group) * _purity(group) for group in groups.values()) / len(populated)
        if populated
        else 0.0
    )
    one_to_one = (
        sum(len(group) for group in groups.values() if len(set(group)) == 1) / len(populated)
        if populated
        else 0.0
    )
    near_rate = (
        sum(len(group) for group in groups.values() if _purity(group) >= near_deterministic_threshold)
        / len(populated)
        if populated
        else 0.0
    )
    missing_flags = ["missing" if value in (None, "") else "present" for value in values]
    missing_nmi = (
        float(normalized_mutual_info_score(missing_flags, targets))
        if targets and len(set(targets)) > 1
        else 0.0
    )
    classification, reason = _classify(
        field, eligibility, len(paired), len(populated), nmi, weighted_purity, one_to_one, near_rate
    )
    return ProxyDiagnostic(
        field=field,
        total_count=len(paired),
        non_null_count=len(populated),
        coverage=len(populated) / len(paired) if paired else 0.0,
        unique_count=len(groups),
        group_size_min=int(sizes.min()) if len(sizes) else 0,
        group_size_median=float(np.median(sizes)) if len(sizes) else 0.0,
        group_size_mean=float(sizes.mean()) if len(sizes) else 0.0,
        group_size_max=int(sizes.max()) if len(sizes) else 0,
        target_entropy=target_entropy,
        conditional_target_entropy=conditional,
        normalized_mutual_information=nmi,
        weighted_group_purity=weighted_purity,
        one_to_one_target_mapping_rate=one_to_one,
        near_deterministic_group_rate=near_rate,
        missingness_target_nmi=missing_nmi,
        classification=classification,
        reason=reason,
    )


def audit_fields(
    acquisition: Sequence[AcquisitionRecord],
    annotations: Sequence[AnnotationRecord],
    fields: Iterable[str],
    *,
    eligibility: EligibilityEngine,
) -> tuple[ProxyDiagnostic, ...]:
    return tuple(
        audit_field(acquisition, annotations, field, eligibility=eligibility) for field in fields
    )


def _annotation_index(annotations: Sequence[AnnotationRecord]) -> dict[str, str]:
    index: dict[str, str] = {}
    for row in annotations:
        if row.sample_id in index:
            raise ValueError(f"Duplicate annotation for sample {row.sample_id}")
        index[row.sample_id] = row.target_label
    return index


def _entropy(values: Sequence[str]) -> float:
    if not values:
        return 0.0
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return -sum((count / len(values)) * log(count / len(values), 2) for count in counts.values())


def _conditional_entropy(groups: Mapping[str, Sequence[str]]) -> float:
    total = sum(len(group) for group in groups.values())
    if total == 0:
        return 0.0
    return sum(len(group) / total * _entropy(list(group)) for group in groups.values())


def _purity(values: Sequence[str]) -> float:
    if not values:
        return 0.0
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return max(counts.values()) / len(values)


def _classify(
    field: str,
    eligibility: EligibilityEngine,
    total: int,
    populated: int,
    nmi: float,
    purity: float,
    one_to_one: float,
    near_rate: float,
) -> tuple[str, str]:
    base = eligibility.eligibility(field)
    if base in {Eligibility.FORBIDDEN_LABEL, Eligibility.FORBIDDEN_TARGET_PROXY}:
        return "FORBIDDEN_TARGET_PROXY", f"base policy is {base.value}"
    coverage = populated / total if total else 0.0
    if total == 0 or coverage < 0.8:
        return "UNRESOLVED", "coverage is below the conservative 0.80 threshold"
    if nmi >= 0.8 or (purity >= 0.95 and one_to_one >= 0.8) or near_rate >= 0.9:
        return "FORBIDDEN_TARGET_PROXY", (
            "field is near-deterministically associated with the audit target"
        )
    if base is Eligibility.RELATION_ALLOWED:
        return "ALLOWED_RELATION", "base policy allows relations and proxy thresholds were not met"
    if base is Eligibility.SPLIT_ONLY:
        return "SPLIT_ONLY", "base policy restricts this field to split construction"
    if base is Eligibility.AUDIT_ONLY:
        return "AUDIT_ONLY", "base policy restricts this field to audit/provenance"
    return "UNRESOLVED", f"base eligibility is {base.value}"
