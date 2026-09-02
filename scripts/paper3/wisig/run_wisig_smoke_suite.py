#!/usr/bin/env python3
"""Run all frozen WiSig models in source-only smoke mode on fold 0/seed 829."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openew.paper3.wisig.checkpoint import atomic_json
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig.runner import MODEL_STAGES, RunConfig, run_experiment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--converted-root", type=Path, required=True)
    parser.add_argument("--split-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--max-epochs", type=int, default=3)
    args = parser.parse_args()
    bundle = ManyRxBundle.load(args.converted_root)
    results: list[dict[str, object]] = []
    for stage in MODEL_STAGES:
        config = RunConfig(
            protocol_id="receiver_fold_0",
            model_stage=stage,
            seed=829,
            relation_retention=0.0 if stage == "P2_NULL" else 1.0,
            max_epochs=args.max_epochs,
            patience=2,
            evaluate_target=False,
            smoke=True,
        )
        try:
            record = run_experiment(
                args.repository,
                args.converted_root,
                args.split_root,
                args.run_root,
                config,
                bundle=bundle,
                resume=True,
            )
            history = json.loads((args.run_root / "runs" / record["run_id"] / "history.json").read_text(encoding="utf-8"))["history"]
            result = {
                "model_stage": stage,
                "status": record["status"],
                "held_out_metrics_disabled": record.get("held_out_metrics") is None,
                "initial_loss": history[0]["train"]["loss"],
                "final_loss": history[-1]["train"]["loss"],
                "loss_decreased": history[-1]["train"]["loss"] < history[0]["train"]["loss"],
                "source_validation_macro_f1": record["source_validation_metrics"]["macro_f1"],
                "wall_seconds": record["wall_seconds"],
                "peak_gpu_memory_bytes": record["peak_gpu_memory_bytes"],
            }
        except Exception as exc:
            result = {"model_stage": stage, "status": "FAILED", "failure_reason": f"{type(exc).__name__}: {exc}"}
        results.append(result)
    summary = {
        "status": "PASS" if all(row.get("status") == "COMPLETE" and row.get("held_out_metrics_disabled") and row.get("loss_decreased") for row in results) else "FAIL",
        "protocol_id": "receiver_fold_0",
        "seed": 829,
        "target_metrics_computed": False,
        "results": results,
    }
    atomic_json(summary, args.run_root / "smoke_summary.json")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
