"""Label-free deployable controls and explicitly label-dependent oracle diagnostics."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .hashing import stable_digest


def choose_mismatched_receiver(
    target_receiver: str,
    candidate_receivers: Sequence[str],
    *,
    seed: int,
) -> str:
    candidates = sorted({str(value) for value in candidate_receivers} - {str(target_receiver)})
    if not candidates:
        raise ValueError("mismatched-receiver control needs another receiver")
    return min(candidates, key=lambda value: stable_digest(seed, target_receiver, value, namespace="wisig-v2-mismatch"))


def day_matched_support(
    source_indices: Sequence[int],
    query_day_ids: Sequence[str],
    sample_ids: Sequence[str],
    day_ids: Sequence[str],
    *,
    budget: int,
    seed: int,
    namespace: str,
) -> tuple[int, ...]:
    """Select without labels while approximately matching query day counts."""

    if budget <= 0:
        raise ValueError("budget must be positive")
    source = [int(index) for index in source_indices]
    if not source:
        raise ValueError("support source is empty")
    query_days, counts = np.unique(np.asarray(query_day_ids, dtype=str), return_counts=True)
    proportions = counts / counts.sum()
    selected: list[int] = []
    used: set[int] = set()
    for day, proportion in zip(query_days.tolist(), proportions.tolist()):
        day_candidates = [index for index in source if str(day_ids[index]) == str(day)]
        day_candidates.sort(key=lambda index: stable_digest(seed, sample_ids[index], namespace=namespace + ":day"))
        take = min(len(day_candidates), int(round(budget * float(proportion))))
        selected.extend(day_candidates[:take]); used.update(day_candidates[:take])
    remaining = [index for index in source if index not in used]
    remaining.sort(key=lambda index: stable_digest(seed, sample_ids[index], namespace=namespace + ":fill"))
    selected.extend(remaining[: max(0, budget - len(selected))])
    return tuple(selected[:budget])


def shuffled_receiver_support(
    indices: Sequence[int],
    receiver_ids: Sequence[str],
    sample_ids: Sequence[str],
    day_ids: Sequence[str],
    query_day_ids: Sequence[str],
    *,
    excluded_receiver: str,
    budget: int,
    seed: int,
) -> tuple[int, ...]:
    candidates = [int(index) for index in indices if str(receiver_ids[int(index)]) != str(excluded_receiver)]
    return day_matched_support(candidates, query_day_ids, sample_ids, day_ids, budget=budget, seed=seed, namespace="wisig-v2-shuffled")


def oracle_support_for_query(
    support_indices: Sequence[int],
    labels: Sequence[int] | np.ndarray,
    *,
    query_label: int,
    mode: str,
    sample_ids: Sequence[str],
    seed: int,
    k: int,
) -> tuple[int, ...]:
    """Audit-only construction. Labels are deliberately explicit in the signature."""

    if mode not in {"same_class_excluded", "same_class_only"}:
        raise ValueError("unknown oracle query-control mode")
    if mode == "same_class_excluded":
        candidates = [int(index) for index in support_indices if int(labels[int(index)]) != int(query_label)]
    else:
        candidates = [int(index) for index in support_indices if int(labels[int(index)]) == int(query_label)]
    candidates.sort(key=lambda index: stable_digest(seed, sample_ids[index], namespace=f"wisig-v2-oracle:{mode}"))
    return tuple(candidates[:k])


def transmitter_pure_oracle_pool(
    receiver_indices: Sequence[int],
    labels: Sequence[int] | np.ndarray,
    sample_ids: Sequence[str],
    *,
    budget: int,
    seed: int,
) -> tuple[int, ...]:
    """Choose one target-pure pool deterministically, never by performance."""

    by_label: dict[int, list[int]] = {}
    for index in receiver_indices:
        by_label.setdefault(int(labels[int(index)]), []).append(int(index))
    eligible = {label: values for label, values in by_label.items() if values}
    if not eligible:
        raise ValueError("no label group for oracle pool")
    chosen = min(eligible, key=lambda label: stable_digest(seed, label, namespace="wisig-v2-oracle-pure-label"))
    ordered = sorted(eligible[chosen], key=lambda index: stable_digest(seed, sample_ids[index], namespace="wisig-v2-oracle-pure-sample"))
    return tuple(ordered[:budget])
