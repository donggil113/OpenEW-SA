"""Read-only reconciliation of the 160 frozen SAR-GN primary records.

The replay uses only frozen, label-free support packets. Existing query
predictions and metrics are compared; no held-out prediction is recomputed.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch

from openew.paper3.pr90_closure.sar_diagnostic import TraceConfig, adapt_with_trace, state_comparison, tensor_state_sha256
from openew.paper3.reviewer_remediation.contracts import SEEDS, digest, file_sha
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig.models import IndependentClassifier
from openew.paper3.wisig_v2.blinding import read_blind_predictions
from openew.paper3.wisig_v2.runner import _to_tensor, remap_bundle_to_split_targets, set_determinism
from openew.paper3.wisig_v2.support import freeze_support_query


def metrics_index(path: Path) -> dict:
    output = {}
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["scope"] == "primary" and row["budget"] == "128" and row["probability_variant"] == "raw" and row["method"] in ("P0", "SAR_GN"):
                key = (row["protocol"], int(row["seed"]), row["method"])
                if key in output:
                    raise ValueError("duplicate receiver-seed-method metric")
                output[key] = row
    if len(output) != 320:
        raise ValueError(f"expected 320 metric rows, got {len(output)}")
    return output


def run(root: Path, data_root: Path, output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("forensic destination must be new or empty")
    output.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.set_num_threads(4)
    v2 = data_root / "paper3/wisig_v2"
    old = data_root / "paper3/reviewer_remediation"
    original = v2 / "experiments/confirmatory_v2/runs"
    split_root = v2 / "splits_v2_frozen"
    recorded = metrics_index(old / "analysis/receiver_seed_metrics.csv")
    bundle = ManyRxBundle.load(data_root / "paper3/wisig/converted/pass_a")
    rows = []
    for index in range(32):
        protocol = f"receiver_loso_{index:02d}"
        split_dir = split_root / protocol
        local = remap_bundle_to_split_targets(bundle, split_dir / "split_summary.json")
        roles = local.split_indices(split_dir / "split_manifest.csv")
        test_receiver = sorted(set(map(str, local.receiver_ids[roles["test"]])))
        if len(test_receiver) != 1:
            raise ValueError("not one test receiver")
        for seed in SEEDS:
            set_determinism(seed)
            folder = old / "experiments" / f"{protocol}__s{seed}" / f"{protocol}__s{seed}__sar_gn__b128__primary"
            info = json.loads((folder / "run.json").read_text())
            if info["status"] != "COMPLETE" or info["protocol"] != protocol or info["seed"] != seed or info["receiver"] != test_receiver[0] or info["budget"] != 128 or info["scope"] != "primary":
                raise ValueError(f"incompatible frozen record {folder}")
            support = freeze_support_query(roles["test"], local.sample_ids, local.receiver_ids,
                                           receiver_id=test_receiver[0], seed=seed, support_budget=128)
            if digest(local.sample_ids[list(support.support_indices)].tolist()) != info["support_ids_sha256"]:
                raise ValueError(f"support IDs changed for {folder}")
            if digest(local.sample_ids[list(support.query_indices)].tolist()) != info["query_ids_sha256"]:
                raise ValueError(f"query IDs changed for {folder}")
            if file_sha(folder / "predictions_blind.npz") != info["prediction_sha256"]:
                raise ValueError("SAR prediction hash changed")
            if file_sha(folder / "adapted.pt") != info["checkpoint_sha256"]:
                raise ValueError("SAR checkpoint hash changed")
            p0folder = original / f"{protocol}__p0__s{seed}__b128__k32__r100__raw"
            if file_sha(p0folder / "checkpoint.pt") != info["compatibility"]["p0_checkpoint_sha256"]:
                raise ValueError("P0 checkpoint changed")
            source_state = torch.load(p0folder / "checkpoint.pt", map_location="cpu", weights_only=True)["model_state"]
            frozen_state = torch.load(folder / "adapted.pt", map_location="cpu", weights_only=True)["model_state"]
            source = IndependentClassifier(len(local.transmitter_ids)).to(device)
            source.load_state_dict(source_state)
            source.eval()
            inputs = _to_tensor(local.features[list(support.support_indices)], device)
            replay, trace, steps = adapt_with_trace(source, inputs, len(local.transmitter_ids), TraceConfig())
            state_match = state_comparison(replay.state_dict(), frozen_state)
            if state_match["max_abs"] > 1e-6:
                raise ValueError(f"support replay disagrees with frozen checkpoint: {folder} {state_match}")
            prior_cost = info["costs"]
            if trace["resets"] != prior_cost["recoveries"] or trace["completed_optimizer_updates"] != prior_cost["gradient_steps"]:
                raise ValueError("support replay disagrees with frozen reset/update counts")
            sar = read_blind_predictions(folder / "predictions_blind.npz")
            p0 = read_blind_predictions(p0folder / "predictions_blind.npz")
            if not np.array_equal(sar["sample_ids"], p0["sample_ids"]):
                raise ValueError("P0/SAR query IDs differ")
            prob_same = np.array_equal(sar["probabilities"], p0["probabilities"])
            class_same = np.array_equal(sar["probabilities"].argmax(-1), p0["probabilities"].argmax(-1))
            metric_sar = recorded[(protocol, seed, "SAR_GN")]
            metric_p0 = recorded[(protocol, seed, "P0")]
            metric_same = float(metric_sar["macro_f1"]) == float(metric_p0["macro_f1"])
            rows.append({
                "protocol": protocol, "receiver": test_receiver[0], "seed": seed,
                "run_json_sha256": file_sha(folder / "run.json"),
                "adapted_checkpoint_sha256": info["checkpoint_sha256"],
                "adapted_tensor_sha256": tensor_state_sha256(frozen_state),
                "source_checkpoint_sha256": info["compatibility"]["p0_checkpoint_sha256"],
                "source_tensor_sha256": tensor_state_sha256(source_state),
                "attempted_updates": trace["attempted_updates"],
                "completed_updates": trace["completed_optimizer_updates"],
                "reset_count": trace["resets"],
                "both_updates_reset": int(len(steps) == 2 and all(step["reset"] for step in steps)),
                "first_retained_total": trace["first_retained_total"],
                "second_retained_total": trace["second_retained_total"],
                "first_retained_per_batch": "|".join(str(step["first_retained"]) for step in steps),
                "second_retained_per_batch": "|".join(str(step["second_retained"]) for step in steps),
                "empty_first": trace["empty_first"],
                "empty_second": trace["empty_second"],
                "final_ema": trace["final_ema"],
                "final_momentum_buffers": trace["final_momentum_buffers"],
                "source_to_final_exact": trace["source_state_comparison"]["exact"],
                "source_to_final_changed_tensors": trace["source_state_comparison"]["changed_tensors"],
                "source_to_final_max_abs": trace["source_state_comparison"]["max_abs"],
                "replay_to_frozen_exact": state_match["exact"],
                "replay_to_frozen_max_abs": state_match["max_abs"],
                "p0_prediction_probabilities_exact": prob_same,
                "p0_prediction_argmax_exact": class_same,
                "p0_prediction_max_abs": float(np.max(np.abs(sar["probabilities"]-p0["probabilities"]))),
                "p0_macro_f1_equal": metric_same,
                "p0_macro_f1": metric_p0["macro_f1"],
                "sar_macro_f1": metric_sar["macro_f1"],
            })
    if len(rows) != 160 or len({(r["protocol"], r["seed"]) for r in rows}) != 160:
        raise ValueError("forensic grid not complete/unique")
    path = output / "sar_original_primary160.csv"
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["receiver"]].append(float(row["sar_macro_f1"])-float(row["p0_macro_f1"]))
    receiver_differences = [sum(values)/len(values) for values in grouped.values()]
    summary = {
        "scope": "frozen SAR_GN primary support128; 32 receiver LOSO x five seeds",
        "records": len(rows), "receivers": len(grouped), "seeds": list(SEEDS),
        "attempted_updates": sum(r["attempted_updates"] for r in rows),
        "completed_updates": sum(r["completed_updates"] for r in rows),
        "resets": sum(r["reset_count"] for r in rows),
        "both_updates_reset_records": sum(r["both_updates_reset"] for r in rows),
        "empty_first": sum(r["empty_first"] for r in rows),
        "empty_second": sum(r["empty_second"] for r in rows),
        "first_retained_total": sum(r["first_retained_total"] for r in rows),
        "second_retained_total": sum(r["second_retained_total"] for r in rows),
        "final_state_exact_source_records": sum(r["source_to_final_exact"] for r in rows),
        "final_state_changed_source_records": sum(not r["source_to_final_exact"] for r in rows),
        "replay_checkpoint_exact_records": sum(r["replay_to_frozen_exact"] for r in rows),
        "prediction_probability_exact_p0_records": sum(r["p0_prediction_probabilities_exact"] for r in rows),
        "prediction_argmax_exact_p0_records": sum(r["p0_prediction_argmax_exact"] for r in rows),
        "metric_macro_f1_equal_p0_records": sum(r["p0_macro_f1_equal"] for r in rows),
        "receiver_delta_positive": sum(x > 0 for x in receiver_differences),
        "receiver_delta_negative": sum(x < 0 for x in receiver_differences),
        "receiver_delta_tied": sum(x == 0 for x in receiver_differences),
        "max_source_to_final_parameter_abs": max(r["source_to_final_max_abs"] for r in rows),
        "max_replay_to_frozen_parameter_abs": max(r["replay_to_frozen_max_abs"] for r in rows),
        "max_prediction_abs_from_p0": max(r["p0_prediction_max_abs"] for r in rows),
        "official_source_policy": "source weights and original blind prediction archives read-only; label-free support adaptation replay only; no held-out query reevaluation",
        "csv_sha256": file_sha(path),
    }
    with (output / "sar_original_summary.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("/mnt/d/openew_sa_data"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(Path.cwd(), args.data_root, args.output), indent=2))
