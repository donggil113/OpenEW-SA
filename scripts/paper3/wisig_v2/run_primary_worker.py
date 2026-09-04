#!/usr/bin/env python3
"""Run a disjoint LOSO receiver subset without touching the global suite status."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from openew.paper3.wisig.checkpoint import atomic_json
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig_v2.parallel import receiver_worker_plan
from openew.paper3.wisig_v2.runner import run_experiment, run_id
from openew.paper3.wisig_v2.suite import is_fatal_failure


def current_git_sha(repository: str | Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=Path(repository), text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--receivers", required=True, help="Comma-separated disjoint receiver indices in execution order")
    parser.add_argument("--expected-git-sha", required=True)
    parser.add_argument("--worker-name", required=True)
    parser.add_argument("--blind-target-metrics", action="store_true", required=True)
    args = parser.parse_args()
    receivers = [int(value) for value in args.receivers.split(",") if value.strip()]
    configs = receiver_worker_plan(receivers)
    root = Path(args.run_root)
    status_path = root / f"{args.worker_name}_status.json"
    if current_git_sha(args.repository) != args.expected_git_sha:
        raise RuntimeError("worker Git SHA differs from the frozen execution SHA")
    for config in configs:
        record_path = root / "runs" / run_id(config) / "run.json"
        if record_path.exists() and json.loads(record_path.read_text(encoding="utf-8")).get("status") == "RUNNING":
            raise RuntimeError(f"worker receiver range collides with an active run: {record_path.parent.name}")
    plan = {
        "status": "FROZEN_DISJOINT_WORKER",
        "worker_name": args.worker_name,
        "receivers_in_order": receivers,
        "planned_runs": len(configs),
        "expected_git_sha": args.expected_git_sha,
        "target_metrics_blinded": True,
        "global_suite_status_modified": False,
    }
    atomic_json(plan, root / f"{args.worker_name}_plan.json")
    bundle = ManyRxBundle.load(args.converted_root)
    rows: list[dict[str, object]] = []
    for number, config in enumerate(configs, start=1):
        if current_git_sha(args.repository) != args.expected_git_sha:
            raise RuntimeError("Git HEAD changed during disjoint worker execution")
        try:
            record = run_experiment(args.repository, args.converted_root, args.split_root, root, config, bundle=bundle, resume=True)
            row: dict[str, object] = {"run_number": number, "run_id": record["run_id"], "status": record["status"]}
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            row = {"run_number": number, "protocol_id": config.protocol_id, "model": config.model_stage, "seed": config.seed, "status": "FAILED", "failure_reason": message}
            rows.append(row)
            atomic_json({**plan, "status": "RUNNING_WITH_FAILURES", "entries": rows}, status_path)
            if is_fatal_failure(message):
                raise
            continue
        rows.append(row)
        atomic_json({**plan, "status": "RUNNING", "entries": rows}, status_path)
    summary = {
        **plan,
        "status": "COMPLETE" if all(row["status"] == "COMPLETE" for row in rows) else "COMPLETE_WITH_FAILURES",
        "completed_runs": sum(row["status"] == "COMPLETE" for row in rows),
        "failed_runs": sum(row["status"] != "COMPLETE" for row in rows),
        "entries": rows,
    }
    atomic_json(summary, status_path)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
