#!/usr/bin/env python3
"""Audit target proxies from official WiSig aggregate count metadata only."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
from pathlib import Path
import pickle
from typing import Any

import numpy as np
from numpy._core.multiarray import _reconstruct


class RestrictedUnpickler(pickle.Unpickler):
    _ALLOWED = {
        ("numpy.core.multiarray", "_reconstruct"): _reconstruct,
        ("numpy._core.multiarray", "_reconstruct"): _reconstruct,
        ("numpy", "ndarray"): np.ndarray,
        ("numpy", "dtype"): np.dtype,
    }

    def find_class(self, module: str, name: str) -> Any:
        try:
            return self._ALLOWED[(module, name)]
        except KeyError as error:
            raise pickle.UnpicklingError(f"forbidden pickle global: {module}.{name}") from error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-summary", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = Path(args.data_summary)
    data = RestrictedUnpickler(io.BytesIO(source.read_bytes())).load()
    counts = np.stack(data["mat_date"]).astype(np.int64, copy=False)
    if counts.ndim != 3:
        raise ValueError(f"Expected day x receiver x transmitter counts, got {counts.shape}")
    relations = {
        "receiver_id": counts.sum(axis=0),
        "capture_day": counts.sum(axis=1),
        "receiver_day": counts.reshape(-1, counts.shape[-1]),
    }
    rows = [audit_contingency(field, matrix) for field, matrix in relations.items()]
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    os.replace(temporary, destination)
    print(json.dumps({"source": str(source), "shape": list(counts.shape), "rows": rows}, indent=2))


def audit_contingency(field: str, matrix: np.ndarray) -> dict[str, object]:
    matrix = np.asarray(matrix, dtype=np.float64)
    keep = matrix.sum(axis=1) > 0
    matrix = matrix[keep]
    total = float(matrix.sum())
    group_totals = matrix.sum(axis=1)
    target_totals = matrix.sum(axis=0)
    weighted_purity = float(matrix.max(axis=1).sum() / total) if total else 0.0
    pure_mass = float(group_totals[(matrix > 0).sum(axis=1) == 1].sum() / total) if total else 0.0
    group_purity = np.divide(matrix.max(axis=1), group_totals, out=np.zeros_like(group_totals), where=group_totals > 0)
    near_mass = float(group_totals[group_purity >= 0.95].sum() / total) if total else 0.0
    joint = matrix / total if total else matrix
    p_group = group_totals / total if total else group_totals
    p_target = target_totals / total if total else target_totals
    expected = p_group[:, None] * p_target[None, :]
    positive = joint > 0
    mutual_information = float(np.sum(joint[positive] * np.log2(joint[positive] / expected[positive]))) if total else 0.0
    h_group = _entropy(p_group); h_target = _entropy(p_target)
    denominator = (h_group + h_target) / 2
    nmi = mutual_information / denominator if denominator > 0 else 0.0
    classification = (
        "FORBIDDEN_TARGET_PROXY"
        if nmi >= 0.8 or (weighted_purity >= 0.95 and pure_mass >= 0.8) or near_mass >= 0.9
        else "RELATION_ALLOWED"
        if field == "receiver_id"
        else "SPLIT_ONLY"
        if field == "capture_day"
        else "UNRESOLVED"
    )
    return {
        "field": field,
        "group_count": int(matrix.shape[0]),
        "target_count": int((target_totals > 0).sum()),
        "indexed_packet_count": int(total),
        "coverage": 1.0 if total else 0.0,
        "weighted_group_purity": weighted_purity,
        "one_to_one_target_mapping_rate": pure_mass,
        "near_deterministic_group_rate": near_mass,
        "normalized_mutual_information": nmi,
        "classification": classification,
        "audit_only_uses_target_counts": True,
    }


def _entropy(probabilities: np.ndarray) -> float:
    positive = probabilities[probabilities > 0]
    return -float(sum(value * math.log2(value) for value in positive))


if __name__ == "__main__":
    main()
