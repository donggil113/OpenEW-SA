#!/usr/bin/env python3
"""Run source-only smoke or blinded receiver-adaptation benchmark records."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from openew.paper3.wisig.checkpoint import atomic_json
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.receiver_adaptation.budget import budget_plan, run_budget_record
from openew.paper3.receiver_adaptation.oracle import run_oracle_record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--frozen-run-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--phase", required=True, choices=("source-smoke", "oracle", "budget", "all"))
    args = parser.parse_args()
    output = Path(args.output_root)
    bundle = ManyRxBundle.load(args.converted_root)
    entries = []
    if args.phase == "source-smoke":
        row = run_oracle_record(args.converted_root, args.split_root, args.frozen_run_root, output / "smoke", protocol="receiver_loso_00", seed=829, bundle=bundle, source_only=True)
        print(json.dumps(row, sort_keys=True))
        return
    if args.phase in {"oracle", "all"}:
        for receiver in range(32):
            protocol = f"receiver_loso_{receiver:02d}"
            for seed in (829, 1829, 2829, 3829, 4829):
                try:
                    row = run_oracle_record(args.converted_root, args.split_root, args.frozen_run_root, output, protocol=protocol, seed=seed, bundle=bundle)
                    entries.append({"phase": "oracle", "run_id": row["run_id"], "status": row["status"]})
                except Exception as exc:
                    entries.append({"phase": "oracle", "protocol": protocol, "seed": seed, "status": "FAILED", "reason": f"{type(exc).__name__}: {exc}"})
                atomic_json({"status": "RUNNING", "entries": entries}, output / "suite_status.json")
    if args.phase in {"budget", "all"}:
        for protocol, seed in budget_plan():
            try:
                row = run_budget_record(args.converted_root, args.split_root, args.frozen_run_root, output, protocol=protocol, seed=seed, bundle=bundle)
                entries.append({"phase": "budget", "run_id": row["run_id"], "status": row["status"], "evaluations": row["evaluation_count"]})
            except Exception as exc:
                entries.append({"phase": "budget", "protocol": protocol, "seed": seed, "status": "FAILED", "reason": f"{type(exc).__name__}: {exc}"})
            atomic_json({"status": "RUNNING", "entries": entries}, output / "suite_status.json")
    summary = {"status": "COMPLETE" if entries and all(row["status"] == "COMPLETE" for row in entries) else "COMPLETE_WITH_FAILURES", "records": len(entries), "failed": sum(row["status"] != "COMPLETE" for row in entries), "adaptation_evaluations": sum(1 if row["phase"] == "oracle" else int(row.get("evaluations", 0)) for row in entries), "entries": entries}
    atomic_json(summary, output / "suite_status.json")
    print(json.dumps({key: value for key, value in summary.items() if key != "entries"}, sort_keys=True))


if __name__ == "__main__":
    main()
