"""Produce a create-once, non-executable future SAR target evaluation plan."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from openew.paper3.reviewer_remediation.contracts import SEEDS, file_sha

def run(data_root: Path, source_output: Path, destination: Path):
    summary_path = source_output / "source_only_summary.json"
    selected_path = source_output / "source_only_selected.csv"
    freeze_path = source_output / "source_only_freeze.json"
    summary = json.loads(summary_path.read_text())
    if summary["status"] != "SOURCE_ONLY_COMPLETE" or summary["selected_recipes"] != 160:
        raise ValueError("source-only result not complete")
    if summary["selected_sha256"] != file_sha(selected_path) or summary["freeze_sha256"] != file_sha(freeze_path):
        raise ValueError("source-only selection hash mismatch")
    with selected_path.open(newline="", encoding="utf-8") as stream:
        selected = list(csv.DictReader(stream))
    allowed = {"A_1", "A_5", "A_20", "B_1", "B_5", "B_20"}
    by_key = {(row["protocol"], int(row["seed"])): row for row in selected}
    expected = {(f"receiver_loso_{i:02d}", seed) for i in range(32) for seed in SEEDS}
    if len(selected) != 160 or set(by_key) != expected:
        raise ValueError("not exactly one recipe per receiver/seed")
    frozen = data_root / "paper3/reviewer_remediation"
    records = []
    for protocol, seed in sorted(expected):
        row = by_key[(protocol, seed)]
        if row["selected_candidate"] not in allowed or int(row["source_validation_receiver_count"]) != 3:
            raise ValueError("invalid source-selected recipe")
        original_path = frozen / "experiments" / f"{protocol}__s{seed}" / f"{protocol}__s{seed}__sar_gn__b128__primary/run.json"
        original = json.loads(original_path.read_text())
        if original["receiver"] != row["target_receiver_not_used"] or original["support_labels_used"] or original["query_used_for_adaptation"]:
            raise ValueError("original receiver/information contract incompatible")
        records.append({
            "protocol": protocol, "seed": seed,
            "source_validation_selected_recipe": row["selected_candidate"],
            "test_receiver": original["receiver"],
            "source_checkpoint_sha256": original["compatibility"]["p0_checkpoint_sha256"],
            "split_sha256": original["compatibility"]["split_sha256"],
            "data_manifest_sha256": original["compatibility"]["data_sha256"],
            "support_ids_sha256": original["support_ids_sha256"],
            "query_ids_sha256": original["query_ids_sha256"],
            "frozen_original_run_json_sha256": file_sha(original_path),
        })
    payload = {
        "status": "PLAN_ONLY_INDEPENDENT_REVIEW_REQUIRED",
        "evidence_class": "POST_HOC_OPERATIONAL_SENSITIVITY_ADDENDUM_IF_APPROVED",
        "target_evaluation_authorized": False,
        "new_target_evaluations_executed_by_this_plan": 0,
        "maximum_future_target_records": 160,
        "receiver_loso_folds": 32, "seeds": list(SEEDS),
        "support_budget": 128, "query_policy": "exact original PR90 SAR primary support/query IDs",
        "source_recipe_selection": "per fold-seed, three frozen source-validation receivers only; max equal-receiver macro-F1, declared tie order",
        "source_only_freeze_sha256": file_sha(freeze_path),
        "source_only_summary_sha256": file_sha(summary_path),
        "source_only_selected_sha256": file_sha(selected_path),
        "original_official_default_sar_status": "FROZEN_REFERENCE_UNCHANGED",
        "new_output_root_required": True,
        "one_time_blind_unblinding_required": True,
        "no_existing_method_retraining": True,
        "records": records,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    return {"plan_sha256": file_sha(destination), "records": len(records), "status": payload["status"]}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-root", type=Path, default=Path("/mnt/d/openew_sa_data"))
    p.add_argument("--source-output", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(run(args.data_root, args.source_output, args.output), indent=2))
