#!/usr/bin/env python3
"""Run the fixed grouped-receiver secondary suite with blind target metrics."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from openew.paper3.wisig.checkpoint import atomic_json
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig_v2.contracts import PRIMARY_SEEDS
from openew.paper3.wisig_v2.runner import RunConfig, run_experiment
from openew.paper3.wisig_v2.suite import is_fatal_failure


MODELS = ("P0", "P2", "P2_SHUFFLED")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--blind-target-metrics", action="store_true", required=True)
    args = parser.parse_args(); root = Path(args.run_root); bundle = ManyRxBundle.load(args.converted_root)
    configs = [RunConfig(f"grouped_receiver_r{repeat}_f{fold}", model, seed) for repeat in range(3) for fold in range(4) for seed in PRIMARY_SEEDS for model in MODELS]
    atomic_json({"status": "FROZEN_BEFORE_TARGET_METRICS", "planned": len(configs), "configs": [asdict(config) for config in configs]}, root / "frozen_grouped_run_plan.json")
    rows = []; planned = len(configs)
    for config in configs:
        protocol, model, seed = config.protocol_id, config.model_stage, config.seed
        try:
            record = run_experiment(args.repository, args.converted_root, args.split_root, root, config, bundle=bundle, resume=True)
            row = {"run_id": record["run_id"], "status": record["status"]}
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            row = {"protocol": protocol, "model": model, "seed": seed, "status": "FAILED", "failure_reason": message}
            rows.append(row); atomic_json({"status": "RUNNING_WITH_FAILURES", "planned": planned, "entries": rows}, root / "suite_status.json")
            if is_fatal_failure(message):
                raise
            continue
        rows.append(row); atomic_json({"status": "RUNNING", "planned": planned, "entries": rows}, root / "suite_status.json")
    summary = {"status": "COMPLETE" if all(row["status"] == "COMPLETE" for row in rows) else "COMPLETE_WITH_FAILURES", "planned": planned, "completed": sum(row["status"] == "COMPLETE" for row in rows), "failed": sum(row["status"] != "COMPLETE" for row in rows), "entries": rows}
    atomic_json(summary, root / "suite_status.json"); print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
