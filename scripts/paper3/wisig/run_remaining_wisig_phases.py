#!/usr/bin/env python3
"""Wait for a running frozen phase, then execute remaining frozen phases safely."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


PHASES = ("day_secondary", "retention", "context_size", "stress_secondary")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(value: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def wait_for_pid(pid: int, expected_token: str) -> None:
    while Path(f"/proc/{pid}").exists():
        command_path = Path(f"/proc/{pid}/cmdline")
        try:
            command = command_path.read_bytes().replace(b"\0", b" ").decode("utf-8", errors="replace")
        except OSError:
            command = ""
        if command and expected_token not in command:
            raise RuntimeError(f"PID {pid} was reused by an unexpected process")
        time.sleep(15)


def require_complete(status_path: Path) -> dict:
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if status.get("status") != "COMPLETE" or int(status.get("failed_runs", 0)) != 0:
        raise RuntimeError(f"phase did not complete cleanly: {status.get('status')}")
    return status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-pid", type=int, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--converted-root", type=Path, required=True)
    parser.add_argument("--split-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--log-root", type=Path, required=True)
    args = parser.parse_args()
    state_path = args.log_root / "remaining_phase_orchestrator.json"
    state = {"status": "WAITING_FOR_RECEIVER_PRIMARY", "start_time": utc_now(), "phases": {}}
    atomic_json(state, state_path)
    wait_for_pid(args.wait_pid, "run_wisig_full_suite.py")
    receiver_status = require_complete(args.run_root / "suite_status.json")
    args.log_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.run_root / "suite_status.json", args.log_root / "suite_status_receiver_primary.json")
    state["receiver_primary"] = {"status": receiver_status["status"], "completed_runs": receiver_status["completed_runs"]}
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(args.repository / "src")
    for phase in PHASES:
        state["status"] = f"RUNNING_{phase.upper()}"
        state["phases"][phase] = {"status": "RUNNING", "start_time": utc_now()}
        atomic_json(state, state_path)
        command = [
            str(args.python),
            str(args.repository / "scripts/paper3/wisig/run_wisig_full_suite.py"),
            "--repository", str(args.repository),
            "--converted-root", str(args.converted_root),
            "--split-root", str(args.split_root),
            "--run-root", str(args.run_root),
            "--phase", phase,
        ]
        log_path = args.log_root / f"suite_{phase}.log"
        with log_path.open("wb") as log:
            completed = subprocess.run(command, cwd=args.repository, env=environment, stdout=log, stderr=subprocess.STDOUT, check=False)
        if completed.returncode != 0:
            state["status"] = "FAILED"
            state["phases"][phase].update({"status": "FAILED", "end_time": utc_now(), "return_code": completed.returncode})
            atomic_json(state, state_path)
            raise RuntimeError(f"{phase} exited with {completed.returncode}")
        phase_status = require_complete(args.run_root / "suite_status.json")
        shutil.copy2(args.run_root / "suite_status.json", args.log_root / f"suite_status_{phase}.json")
        state["phases"][phase].update({"status": "COMPLETE", "end_time": utc_now(), "completed_runs": phase_status["completed_runs"]})
        atomic_json(state, state_path)
    state["status"] = "COMPLETE"
    state["end_time"] = utc_now()
    atomic_json(state, state_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
