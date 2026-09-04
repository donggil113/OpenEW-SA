#!/usr/bin/env python3
"""Run the fixed single-seed official-equalized WiSig diagnostic."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from openew.paper3.wisig.checkpoint import atomic_json
from openew.paper3.wisig.data import ManyRxBundle
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
    args = parser.parse_args(); root = Path(args.run_root)
    configs = [RunConfig(f"receiver_loso_{receiver:02d}", model, 829, data_variant="official_equalized") for receiver in range(32) for model in MODELS]
    atomic_json({"status": "FROZEN_BEFORE_TARGET_METRICS", "planned": len(configs), "configs": [asdict(config) for config in configs]}, root / "frozen_equalized_run_plan.json")
    bundle = ManyRxBundle.load(args.converted_root); rows = []
    for config in configs:
        try:
            record = run_experiment(args.repository, args.converted_root, args.split_root, root, config, bundle=bundle, resume=True)
            row = {"run_id": record["run_id"], "status": record["status"]}
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            row = {"protocol": config.protocol_id, "model": config.model_stage, "seed": config.seed, "status": "FAILED", "failure_reason": message}
            rows.append(row); atomic_json({"status": "RUNNING_WITH_FAILURES", "planned": 96, "entries": rows}, root / "suite_status.json")
            if is_fatal_failure(message):
                raise
            continue
        rows.append(row)
        atomic_json({"status": "RUNNING", "planned": 96, "entries": rows}, root / "suite_status.json")
    summary = {"status": "COMPLETE" if all(row["status"] == "COMPLETE" for row in rows) else "COMPLETE_WITH_FAILURES", "planned": 96, "completed": sum(row["status"] == "COMPLETE" for row in rows), "failed": sum(row["status"] != "COMPLETE" for row in rows), "entries": rows}
    atomic_json(summary, root / "suite_status.json"); print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
