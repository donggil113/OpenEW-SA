"""Frozen source-validation-only SAR operational sensitivity.

A --freeze-only invocation creates a write-once plan with file hashes.
--execute verifies it and writes source-validation results in a new folder.
No held-out test prediction or metric is computed.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
import torch

from openew.paper3.pr90_closure.sar_diagnostic import TraceConfig, adapt_with_trace
from openew.paper3.reviewer_remediation.calibration import probability_metrics
from openew.paper3.reviewer_remediation.contracts import SEEDS, file_sha
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig.models import IndependentClassifier
from openew.paper3.wisig_v2.runner import _independent_probabilities, _to_tensor, remap_bundle_to_split_targets, set_determinism
from openew.paper3.wisig_v2.support import freeze_support_query


def candidates(class_count: int):
    normalized = 0.2 * math.log(class_count) / math.log(1000)
    return [(f"{policy}_{count}", TraceConfig(passes=count, reset_threshold=value))
            for policy, value in (("A", 0.2), ("B", normalized)) for count in (1, 5, 20)]


def plan(repo: Path, data_root: Path) -> dict:
    config = repo / "configs/paper3/pr90_closure/sar_source_only_v1.json"
    script = repo / "scripts/paper3/pr90_closure/run_sar_source_only.py"
    module = repo / "src/openew/paper3/pr90_closure/sar_diagnostic.py"
    old_method = repo / "src/openew/paper3/reviewer_remediation/methods.py"
    sources = data_root / "paper3/wisig_v2"
    splits = {}
    checkpoints = {}
    for index in range(32):
        protocol = f"receiver_loso_{index:02d}"
        split_dir = sources / "splits_v2_frozen" / protocol
        splits[protocol] = {"manifest": file_sha(split_dir / "split_manifest.csv"),
                            "summary": file_sha(split_dir / "split_summary.json")}
        for seed in SEEDS:
            checkpoint = sources / "experiments/confirmatory_v2/runs" / f"{protocol}__p0__s{seed}__b128__k32__r100__raw/checkpoint.pt"
            checkpoints[f"{protocol}__s{seed}"] = file_sha(checkpoint)
    cfg = json.loads(config.read_text())
    if cfg["seeds"] != list(SEEDS) or cfg["class_count"] != 6 or cfg["passes"] != [1, 5, 20] or not cfg["target_receiver_excluded"]:
        raise ValueError("source-only protocol differs from declared design")
    return {"status": "FROZEN_BEFORE_SOURCE_ONLY_DIAGNOSTIC",
            "evidence_class": cfg["evidence_class"],
            "git_head_at_freeze": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
            "config_sha256": file_sha(config), "script_sha256": file_sha(script),
            "diagnostic_module_sha256": file_sha(module), "frozen_method_sha256": file_sha(old_method),
            "split_hashes": splits, "source_checkpoint_hashes": checkpoints,
            "expected_candidate_rows": 32 * 5 * 3 * 6,
            "future_target_evaluation_authorized": False}


def create_freeze(repo: Path, data_root: Path, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    destination = output / "source_only_freeze.json"
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(plan(repo, data_root), stream, indent=2, sort_keys=True)
        stream.write("\n")
    return {"freeze_path": str(destination), "sha256": file_sha(destination)}


def verify_freeze(repo: Path, data_root: Path, output: Path):
    frozen = json.loads((output / "source_only_freeze.json").read_text())
    current = plan(repo, data_root)
    current["git_head_at_freeze"] = frozen["git_head_at_freeze"]
    if frozen != current:
        raise ValueError("source-only code, config, split or checkpoint changed after freeze")
    if any((output / name).exists() for name in ("source_only_rows.csv", "source_only_selected.csv", "source_only_summary.json")):
        raise FileExistsError("source-only result already exists")


def save_candidate_checkpoint(destination: Path, payload: dict) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("candidate checkpoint already exists")
    descriptor, temporary = tempfile.mkstemp(prefix=destination.name + ".", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_candidate_checkpoint(destination: Path, protocol: str, seed: int, candidate_id: str,
                              expected_receivers: list[str], freeze_sha: str) -> list[dict]:
    payload = json.loads(destination.read_text())
    items = payload.get("rows", [])
    if payload.get("freeze_sha256") != freeze_sha or len(items) != 3 or {
        (r["protocol"], r["seed"], r["candidate"], r["source_validation_receiver"]) for r in items
    } != {(protocol, seed, candidate_id, receiver) for receiver in expected_receivers}:
        raise ValueError("candidate checkpoint incompatible or incomplete")
    return items


def execute(repo: Path, data_root: Path, output: Path) -> dict:
    verify_freeze(repo, data_root, output)
    freeze_sha = file_sha(output / "source_only_freeze.json")
    torch.set_num_threads(4)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base = ManyRxBundle.load(data_root / "paper3/wisig/converted/pass_a")
    v2 = data_root / "paper3/wisig_v2"
    rows = []
    selected = []
    for index in range(32):
        protocol = f"receiver_loso_{index:02d}"
        split_dir = v2 / "splits_v2_frozen" / protocol
        bundle = remap_bundle_to_split_targets(base, split_dir / "split_summary.json")
        if len(bundle.transmitter_ids) != 6:
            raise ValueError("unexpected split-local class count")
        roles = bundle.split_indices(split_dir / "split_manifest.csv")
        val_receivers = sorted({str(bundle.receiver_ids[i]) for i in roles["validation"]})
        test_receivers = sorted({str(bundle.receiver_ids[i]) for i in roles["test"]})
        if len(val_receivers) != 3 or len(test_receivers) != 1 or set(val_receivers) & set(test_receivers):
            raise ValueError("source-validation receiver contract failed")
        for seed in SEEDS:
            set_determinism(seed)
            checkpoint = v2 / "experiments/confirmatory_v2/runs" / f"{protocol}__p0__s{seed}__b128__k32__r100__raw/checkpoint.pt"
            source = IndependentClassifier(6).to(device)
            source.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True)["model_state"])
            source.eval()
            source_queries = []
            for receiver in val_receivers:
                frozen = freeze_support_query(roles["validation"], bundle.sample_ids, bundle.receiver_ids,
                                              receiver_id=receiver, seed=seed, support_budget=128)
                support, query = np.array(frozen.support_indices), np.array(frozen.query_indices)
                if set(support) & set(query) or set(support) & set(roles["test"]) or set(query) & set(roles["test"]):
                    raise ValueError("source query/support entered held-out test role")
                source_queries.append((receiver, support, query))
            candidate_means = []
            for candidate_id, config in candidates(6):
                destination = output / "candidate_checkpoints" / f"{protocol}__s{seed}__{candidate_id}.json"
                if destination.exists():
                    candidate_rows = read_candidate_checkpoint(destination, protocol, seed, candidate_id,
                                                               val_receivers, freeze_sha)
                    rows.extend(candidate_rows)
                    candidate_means.append(float(np.mean([r["macro_f1"] for r in candidate_rows])))
                    continue
                receiver_scores = []
                candidate_rows = []
                for receiver, support, query in source_queries:
                    tick = time.perf_counter()
                    adapted, trace, _ = adapt_with_trace(source, _to_tensor(bundle.features[support], device), 6, config)
                    if device.type == "cuda":
                        torch.cuda.synchronize()
                    adaptation_seconds = time.perf_counter() - tick
                    tick = time.perf_counter()
                    probabilities = _independent_probabilities(adapted, bundle, query, device, 1024)
                    if device.type == "cuda":
                        torch.cuda.synchronize()
                    prediction_seconds = time.perf_counter() - tick
                    metrics = probability_metrics(bundle.labels[query], probabilities)
                    receiver_scores.append(metrics["macro_f1"])
                    candidate_rows.append({
                        "protocol": protocol, "seed": seed, "test_receiver_not_used": test_receivers[0],
                        "source_validation_receiver": receiver, "candidate": candidate_id,
                        "passes": config.passes, "threshold": config.reset_threshold,
                        "support_count": len(support), "validation_query_count": len(query),
                        "macro_f1": metrics["macro_f1"], "accuracy": metrics["accuracy"],
                        "ece": metrics["ece"], "nll": metrics["nll"], "brier": metrics["brier"],
                        "attempted_updates": trace["attempted_updates"],
                        "optimizer_updates": trace["completed_optimizer_updates"],
                        "resets": trace["resets"], "empty_first": trace["empty_first"],
                        "empty_second": trace["empty_second"],
                        "final_parameter_changed_tensors": trace["source_state_comparison"]["changed_tensors"],
                        "final_parameter_max_abs": trace["source_state_comparison"]["max_abs"],
                        "final_state_sha256": trace["final_state_sha256"],
                        "adaptation_seconds": adaptation_seconds,
                        "prediction_seconds": prediction_seconds,
                    })
                save_candidate_checkpoint(destination, {"freeze_sha256": freeze_sha, "rows": candidate_rows})
                rows.extend(candidate_rows)
                candidate_means.append(float(np.mean(receiver_scores)))
                print(f"SOURCE_ONLY_CHECKPOINT {protocol} seed={seed} candidate={candidate_id}", flush=True)
            winner = int(np.argmax(candidate_means))
            selected.append({
                "protocol": protocol, "seed": seed, "selected_candidate": candidates(6)[winner][0],
                "source_validation_receiver_count": 3,
                "selected_mean_macro_f1": candidate_means[winner],
                "all_candidate_mean_macro_f1": "|".join(f"{v:.12g}" for v in candidate_means),
                "target_receiver_not_used": test_receivers[0],
            })
    if len(rows) != 2880 or len(selected) != 160:
        raise ValueError("source-only diagnostic coverage incomplete")
    rows_path = output / "source_only_rows.csv"
    with rows_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    selected_path = output / "source_only_selected.csv"
    with selected_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(selected[0]))
        writer.writeheader()
        writer.writerows(selected)
    grouped = {}
    for name, _ in candidates(6):
        items = [row for row in rows if row["candidate"] == name]
        grouped[name] = {
            "source_validation_receiver_runs": len(items),
            "mean_macro_f1": float(np.mean([row["macro_f1"] for row in items])),
            "mean_ece": float(np.mean([row["ece"] for row in items])),
            "mean_nll": float(np.mean([row["nll"] for row in items])),
            "mean_brier": float(np.mean([row["brier"] for row in items])),
            "reset_count": sum(row["resets"] for row in items),
            "optimizer_updates": sum(row["optimizer_updates"] for row in items),
            "changed_final_state_count": sum(row["final_parameter_changed_tensors"] > 0 for row in items),
            "adaptation_seconds_total": sum(row["adaptation_seconds"] for row in items),
            "prediction_seconds_total": sum(row["prediction_seconds"] for row in items),
        }
    summary = {
        "status": "SOURCE_ONLY_COMPLETE", "receiver_loso_folds": 32, "seeds": list(SEEDS),
        "source_validation_receivers_per_fold": 3, "candidate_evaluations": len(rows),
        "selected_recipes": len(selected), "candidate_summary": grouped,
        "selected_distribution": {name: sum(row["selected_candidate"] == name for row in selected)
                                  for name, _ in candidates(6)},
        "rows_sha256": file_sha(rows_path), "selected_sha256": file_sha(selected_path),
        "freeze_sha256": file_sha(output / "source_only_freeze.json"),
        "target_predictions_computed": 0, "target_metrics_computed": 0,
        "future_target_evaluation_authorized": False,
    }
    with (output / "source_only_summary.json").open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["freeze-only", "execute"])
    p.add_argument("--repo", type=Path, default=Path.cwd())
    p.add_argument("--data-root", type=Path, default=Path("/mnt/d/openew_sa_data"))
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = create_freeze(args.repo, args.data_root, args.output) if args.mode == "freeze-only" else execute(args.repo, args.data_root, args.output)
    print(json.dumps(result, indent=2))
