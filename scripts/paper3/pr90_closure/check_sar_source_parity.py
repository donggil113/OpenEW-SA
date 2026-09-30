"""Read-only parity of source-only A1 diagnostic with frozen PR90 source-validation archives."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from openew.paper3.reviewer_remediation.calibration import probability_metrics
from openew.paper3.reviewer_remediation.contracts import SEEDS, file_sha
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig_v2.blinding import read_blind_predictions
from openew.paper3.wisig_v2.runner import remap_bundle_to_split_targets
from openew.paper3.wisig_v2.support import freeze_support_query


def run(data_root: Path, source_output: Path, destination: Path):
    base = ManyRxBundle.load(data_root / "paper3/wisig/converted/pass_a")
    counts = 0
    max_error = {name: 0.0 for name in ("macro_f1", "ece", "nll", "brier")}
    for index in range(32):
        protocol = f"receiver_loso_{index:02d}"
        split_dir = data_root / "paper3/wisig_v2/splits_v2_frozen" / protocol
        bundle = remap_bundle_to_split_targets(base, split_dir / "split_summary.json")
        roles = bundle.split_indices(split_dir / "split_manifest.csv")
        receivers = sorted(set(map(str, bundle.receiver_ids[roles["validation"]])))
        for seed in SEEDS:
            parent = data_root / "paper3/reviewer_remediation/experiments" / f"{protocol}__s{seed}"
            original = read_blind_predictions(parent / "source_sar_gn.npz")
            original_ids = list(map(str, original["sample_ids"]))
            by_id = {name: row for row, name in enumerate(original_ids)}
            if len(by_id) != len(original_ids):
                raise ValueError("duplicate frozen source-validation ID")
            checkpoint = source_output / "candidate_checkpoints" / f"{protocol}__s{seed}__A_1.json"
            frozen = json.loads(checkpoint.read_text())
            rows = {row["source_validation_receiver"]: row for row in frozen["rows"]}
            if set(rows) != set(receivers):
                raise ValueError("source receiver set mismatch")
            for receiver in receivers:
                partition = freeze_support_query(roles["validation"], bundle.sample_ids, bundle.receiver_ids,
                                                receiver_id=receiver, seed=seed, support_budget=128)
                query = np.array(partition.query_indices)
                ids = list(map(str, bundle.sample_ids[query]))
                if any(name not in by_id for name in ids):
                    raise ValueError("source-validation query ID absent from frozen source archive")
                probabilities = original["probabilities"][[by_id[name] for name in ids]]
                metrics = probability_metrics(bundle.labels[query], probabilities)
                for name in max_error:
                    error = abs(metrics[name]-rows[receiver][name])
                    max_error[name] = max(max_error[name], error)
                counts += 1
    if counts != 480 or max(max_error.values()) > 1e-9:
        raise AssertionError(f"source A1 parity failed: {counts} {max_error}")
    payload = {"status": "PASS", "scope": "A_1 source-validation only, 32 LOSO x five seeds x three validation receivers",
               "receiver_seed_validation_rows": counts, "maximum_absolute_metric_difference": max_error,
               "source_only_freeze_sha256": file_sha(source_output / "source_only_freeze.json"),
               "heldout_target_predictions_recomputed": 0, "heldout_target_metrics_computed": 0}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return payload


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-root", type=Path, default=Path("/mnt/d/openew_sa_data"))
    p.add_argument("--source-output", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(run(args.data_root, args.source_output, args.output), indent=2))
