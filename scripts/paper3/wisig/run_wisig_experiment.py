#!/usr/bin/env python3
"""Run one checkpointed preregistered WiSig model/fold/seed configuration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openew.paper3.wisig.runner import MODEL_STAGES, RunConfig, run_experiment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--converted-root", type=Path, required=True)
    parser.add_argument("--split-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--protocol-id", required=True)
    parser.add_argument("--model-stage", choices=MODEL_STAGES, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--context-size", type=int, default=32)
    parser.add_argument("--relation-retention", type=float, default=1.0)
    parser.add_argument("--max-epochs", type=int, default=20)
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=5e-4)
    parser.add_argument("--sample-batch-size", type=int, default=1024)
    parser.add_argument("--episode-node-budget", type=int, default=1024)
    parser.add_argument("--evaluate-target", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()
    config = RunConfig(
        protocol_id=args.protocol_id,
        model_stage=args.model_stage,
        seed=args.seed,
        context_size=args.context_size,
        relation_retention=args.relation_retention,
        max_epochs=args.max_epochs,
        patience=args.patience,
        learning_rate=args.learning_rate,
        sample_batch_size=args.sample_batch_size,
        episode_node_budget=args.episode_node_budget,
        evaluate_target=args.evaluate_target,
        smoke=args.smoke,
    )
    record = run_experiment(args.repository, args.converted_root, args.split_root, args.run_root, config, resume=not args.no_resume)
    print(json.dumps({key: record.get(key) for key in ("run_id", "status", "wall_seconds", "source_validation_metrics", "held_out_metrics")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
