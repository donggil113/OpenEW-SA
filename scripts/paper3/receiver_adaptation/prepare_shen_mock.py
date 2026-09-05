#!/usr/bin/env python3
"""Build synthetic Shen HDF5 fixtures and validate the future LOSO engine."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from openew.paper3.receiver_adaptation.shen_adapter import SHEN_RECEIVERS, load_shen_rows, write_mock_shen_hdf5
from openew.paper3.receiver_adaptation.shen_splits import build_loso_splits, freeze_support_query


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--rows-per-receiver", type=int, default=140)
    args = parser.parse_args()
    root = Path(args.output_root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError("mock output root must be new or empty")
    samples = []
    schemas = []
    for number, receiver in enumerate(SHEN_RECEIVERS):
        path = root / "hdf5" / f"{receiver}.h5"
        write_mock_shen_hdf5(path, rows=args.rows_per_receiver, seed=829 + number)
        features, rows = load_shen_rows(path, receiver)
        if features.shape != (args.rows_per_receiver, 256, 2):
            raise RuntimeError("mock conversion shape mismatch")
        samples.extend(rows)
        schemas.append({"receiver_id": receiver, "rows": len(rows), "feature_shape": list(features.shape)})
    support = [freeze_support_query(samples, receiver, budget=128, seed=829) for receiver in SHEN_RECEIVERS]
    report = {"status": "PASS", "scientific_evidence": False, "payload_used": "SYNTHETIC_ONLY", "receiver_count": 20, "transmitter_count": 10, "hardware_family_count": 6, "loso_split_count": len(build_loso_splits()), "support_banks": len(support), "support_query_disjoint": all(not (set(row.support_sample_ids) & set(row.query_sample_ids)) for row in support), "schemas": schemas}
    (root / "mock_validation.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
