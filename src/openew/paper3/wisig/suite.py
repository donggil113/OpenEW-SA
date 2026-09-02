"""Frozen WiSig study plan and sequential checkpointed execution."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from .checkpoint import atomic_json
from .data import ManyRxBundle
from .runner import MODEL_STAGES, SEEDS, RunConfig, run_experiment


def full_suite_plan() -> list[tuple[str, RunConfig]]:
    rows: list[tuple[str, RunConfig]] = []
    for fold in range(5):
        for stage in MODEL_STAGES:
            for seed in SEEDS:
                rows.append(("receiver_primary", _config(f"receiver_fold_{fold}", stage, seed)))
    for fold in range(4):
        for stage in MODEL_STAGES:
            for seed in SEEDS:
                rows.append(("day_secondary", _config(f"day_fold_{fold}", stage, seed)))
    for fold in range(5):
        for retention in (1.0, 0.75, 0.5, 0.25, 0.0):
            for seed in SEEDS:
                rows.append(("retention", _config(f"receiver_fold_{fold}", "P2", seed, retention=retention)))
    for fold in range(5):
        for size in (8, 32, 128):
            for seed in SEEDS:
                rows.append(("context_size", _config(f"receiver_fold_{fold}", "P2", seed, context_size=size)))
    for stage in ("P0", "P1", "P2", "P2_SHUFFLED"):
        for seed in SEEDS:
            rows.append(("stress_secondary", _config("receiver_day_stress_0", stage, seed)))
    return rows


def _config(protocol: str, stage: str, seed: int, *, context_size: int = 32, retention: float | None = None) -> RunConfig:
    if retention is None:
        retention = 0.0 if stage == "P2_NULL" else 1.0
    return RunConfig(
        protocol_id=protocol,
        model_stage=stage,
        seed=seed,
        context_size=context_size,
        relation_retention=retention,
        max_epochs=30,
        patience=8,
        learning_rate=5e-4,
        weight_decay=1e-4,
        sample_batch_size=1024,
        episode_node_budget=1024,
        coral_weight=0.1,
        groupdro_eta=0.01,
        evaluate_target=True,
        smoke=False,
    )


def deduplicate_plan(rows: Iterable[tuple[str, RunConfig]]) -> list[tuple[list[str], RunConfig]]:
    unique: dict[str, tuple[list[str], RunConfig]] = {}
    for phase, config in rows:
        if config.config_hash in unique:
            unique[config.config_hash][0].append(phase)
        else:
            unique[config.config_hash] = ([phase], config)
    return list(unique.values())


def plan_summary() -> dict[str, Any]:
    rows = full_suite_plan()
    unique = deduplicate_plan(rows)
    by_phase: dict[str, int] = {}
    for phase, _ in rows:
        by_phase[phase] = by_phase.get(phase, 0) + 1
    return {
        "declared_condition_runs": len(rows),
        "unique_executable_runs": len(unique),
        "duplicate_conditions_reused_by_hash": len(rows) - len(unique),
        "phase_counts": by_phase,
        "models": list(MODEL_STAGES),
        "seeds": list(SEEDS),
        "receiver_folds": 5,
        "day_folds": 4,
        "target_evaluation_policy": "once after split/model freeze; never used for redesign",
    }


def execute_suite(
    repository: str | Path,
    converted_root: str | Path,
    split_root: str | Path,
    run_root: str | Path,
    *,
    phases: set[str] | None = None,
) -> dict[str, Any]:
    run_root = Path(run_root)
    plan = full_suite_plan()
    if phases:
        plan = [row for row in plan if row[0] in phases]
    unique = deduplicate_plan(plan)
    atomic_json({"summary": plan_summary(), "selected_phases": sorted(phases) if phases else "all", "runs": [{"phases": phase, "config": asdict(config), "config_hash": config.config_hash} for phase, config in unique]}, run_root / "frozen_run_plan.json")
    bundle = ManyRxBundle.load(converted_root)
    results: list[dict[str, Any]] = []
    integrity_tokens = ("incompatib", "split", "unknown sample", "capacity match", "manifest", "leakage", "target")
    for run_number, (run_phases, config) in enumerate(unique, start=1):
        try:
            record = run_experiment(repository, converted_root, split_root, run_root, config, bundle=bundle, resume=True)
            results.append({"run_number": run_number, "phases": run_phases, "run_id": record["run_id"], "status": record["status"]})
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            results.append({"run_number": run_number, "phases": run_phases, "config_hash": config.config_hash, "status": "FAILED", "failure_reason": message})
            atomic_json({"status": "RUNNING_WITH_FAILURES", "completed_plan_entries": results}, run_root / "suite_status.json")
            if any(token in message.lower() for token in integrity_tokens):
                raise
            continue
        atomic_json({"status": "RUNNING", "planned_unique_runs": len(unique), "completed_plan_entries": results}, run_root / "suite_status.json")
    summary = {
        "status": "COMPLETE" if all(row["status"] == "COMPLETE" for row in results) else "COMPLETE_WITH_FAILURES",
        "planned_unique_runs": len(unique),
        "completed_runs": sum(row["status"] == "COMPLETE" for row in results),
        "failed_runs": sum(row["status"] != "COMPLETE" for row in results),
        "entries": results,
    }
    atomic_json(summary, run_root / "suite_status.json")
    return summary
