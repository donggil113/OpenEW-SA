"""Frozen WiSig V2 run plans and failure-aware sequential execution."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from openew.paper3.wisig.checkpoint import atomic_json
from openew.paper3.wisig.data import ManyRxBundle

from .contracts import CONTEXT_K_VALUES, PRIMARY_CONTEXT_K, PRIMARY_SEEDS, PRIMARY_SUPPORT_BUDGET, SUPPORT_BUDGETS
from .runner import RunConfig, run_experiment


PRIMARY_MODELS = (
    "P0",
    "P0_WIDE",
    "DG_CORAL",
    "DG_GROUPDRO",
    "DG_DANN",
    "SOURCE_NORM",
    "P1",
    "P2",
    "P2_SHUFFLED",
    "P2_NULL",
    "P2_MISMATCHED_RX",
    "RX_NORM",
    "T3A",
)


def _config(protocol: str, model: str, seed: int, *, budget: int = PRIMARY_SUPPORT_BUDGET, k: int = PRIMARY_CONTEXT_K, smoke: bool = False, variant: str = "raw") -> RunConfig:
    return RunConfig(
        protocol_id=protocol,
        model_stage=model,
        seed=seed,
        support_budget=budget,
        context_k=k,
        context_retention=1.0,
        max_epochs=2 if smoke else 30,
        patience=2 if smoke else 8,
        learning_rate=5e-4,
        weight_decay=1e-4,
        sample_batch_size=1024,
        episode_node_budget=1056,
        coral_weight=0.1,
        groupdro_eta=0.01,
        dann_reversal=0.1,
        blind_target_metrics=True,
        evaluate_target_predictions=not smoke,
        smoke=smoke,
        data_variant=variant,
    )


def primary_loso_plan() -> list[tuple[str, RunConfig]]:
    return [
        ("primary_loso", _config(f"receiver_loso_{receiver:02d}", model, seed))
        for receiver in range(32)
        for seed in PRIMARY_SEEDS
        for model in PRIMARY_MODELS
    ]


def day_secondary_plan() -> list[tuple[str, RunConfig]]:
    return [
        ("day_secondary", _config(f"day_lodo_{fold}", model, seed))
        for fold in range(4)
        for seed in PRIMARY_SEEDS
        for model in PRIMARY_MODELS
    ]


def support_budget_plan() -> list[tuple[str, RunConfig]]:
    return [
        ("support_budget", _config(f"receiver_loso_{receiver:02d}", "P2", seed, budget=budget, k=min(PRIMARY_CONTEXT_K, budget)))
        for receiver in range(32)
        for seed in PRIMARY_SEEDS
        for budget in SUPPORT_BUDGETS
    ]


def context_k_plan() -> list[tuple[str, RunConfig]]:
    return [
        ("context_k", _config(f"receiver_loso_{receiver:02d}", "P2", seed, k=k))
        for receiver in range(32)
        for seed in PRIMARY_SEEDS
        for k in CONTEXT_K_VALUES
    ]


def smoke_plan() -> list[tuple[str, RunConfig]]:
    return [
        ("source_only_smoke", _config("receiver_loso_00", model, PRIMARY_SEEDS[0], smoke=True))
        for model in PRIMARY_MODELS
        if model not in {"P2_SHUFFLED", "P2_NULL", "P2_MISMATCHED_RX", "RX_NORM", "T3A"}
    ]


def full_plan(phases: set[str] | None = None) -> list[tuple[str, RunConfig]]:
    rows = primary_loso_plan() + day_secondary_plan() + support_budget_plan() + context_k_plan()
    return [row for row in rows if phases is None or row[0] in phases]


def deduplicate_plan(rows: Iterable[tuple[str, RunConfig]]) -> list[tuple[list[str], RunConfig]]:
    unique: dict[str, tuple[list[str], RunConfig]] = {}
    for phase, config in rows:
        if config.config_hash in unique:
            unique[config.config_hash][0].append(phase)
        else:
            unique[config.config_hash] = ([phase], config)
    return list(unique.values())


def plan_summary() -> dict[str, Any]:
    rows = full_plan()
    unique = deduplicate_plan(rows)
    phase_counts: dict[str, int] = {}
    for phase, _ in rows:
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
    return {
        "declared_condition_runs": len(rows),
        "unique_condition_runs": len(unique),
        "primary_loso_runs": len(primary_loso_plan()),
        "day_secondary_runs": len(day_secondary_plan()),
        "support_budget_runs": len(support_budget_plan()),
        "context_k_runs": len(context_k_plan()),
        "phase_counts": phase_counts,
        "models": list(PRIMARY_MODELS),
        "seeds": list(PRIMARY_SEEDS),
        "receiver_is_primary_evaluation_unit": True,
        "target_metrics_blinded_during_execution": True,
    }


def execute_suite(
    repository: str | Path,
    converted_root: str | Path,
    split_root: str | Path,
    run_root: str | Path,
    *,
    phases: set[str] | None = None,
    smoke: bool = False,
) -> dict[str, Any]:
    run_root = Path(run_root)
    rows = smoke_plan() if smoke else full_plan(phases)
    unique = deduplicate_plan(rows)
    plan_payload = {
        "summary": plan_summary(),
        "selected_phases": ["source_only_smoke"] if smoke else (sorted(phases) if phases else "all"),
        "runs": [{"phases": labels, "config": asdict(config), "config_hash": config.config_hash} for labels, config in unique],
    }
    atomic_json(plan_payload, run_root / ("smoke_plan.json" if smoke else "frozen_run_plan.json"))
    bundle = ManyRxBundle.load(converted_root)
    results: list[dict[str, Any]] = []
    fatal_tokens = ("split", "manifest", "leak", "overlap", "annotation", "unknown sample", "target metrics", "non-finite")
    for number, (phase_labels, config) in enumerate(unique, start=1):
        try:
            record = run_experiment(repository, converted_root, split_root, run_root, config, bundle=bundle, resume=True)
            result = {"run_number": number, "phases": phase_labels, "run_id": record["run_id"], "status": record["status"]}
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            result = {"run_number": number, "phases": phase_labels, "config_hash": config.config_hash, "status": "FAILED", "failure_reason": message}
            results.append(result)
            atomic_json({"status": "RUNNING_WITH_FAILURES", "entries": results}, run_root / "suite_status.json")
            if any(token in message.lower() for token in fatal_tokens):
                raise
            continue
        results.append(result)
        atomic_json({"status": "RUNNING", "planned_unique_runs": len(unique), "entries": results}, run_root / "suite_status.json")
    summary = {
        "status": "COMPLETE" if all(row["status"] == "COMPLETE" for row in results) else "COMPLETE_WITH_FAILURES",
        "planned_unique_runs": len(unique),
        "completed_runs": sum(row["status"] == "COMPLETE" for row in results),
        "failed_runs": sum(row["status"] != "COMPLETE" for row in results),
        "entries": results,
    }
    atomic_json(summary, run_root / "suite_status.json")
    return summary
