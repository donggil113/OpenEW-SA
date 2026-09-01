#!/usr/bin/env python
"""Run one explicitly specified Paper 3 pilot configuration."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from openew.paper3.static_relational.runner import RunSpec, run_suite


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/paper3/static_relational/pilot.yaml"))
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--dataset", required=True, choices=("jamshield", "electrosense", "deepsense"))
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--model-stage", required=True, choices=("m0", "m1", "m2"))
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--relation-types", nargs="*", default=[])
    parser.add_argument("--relation-retention", type=float, default=1.0)
    parser.add_argument("--shuffled-relations", action="store_true")
    parser.add_argument("--variant", default="manual")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--allow-heldout-evaluation", action="store_true")
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    spec = RunSpec(
        dataset=args.dataset,
        protocol=args.protocol,
        model_stage=args.model_stage,
        seed=args.seed,
        relation_types=tuple(args.relation_types),
        relation_retention=args.relation_retention,
        shuffled_relations=args.shuffled_relations,
        variant=args.variant,
    )
    print(
        run_suite(
            config,
            args.run_root,
            [spec],
            resume=args.resume,
            smoke=args.smoke,
            evaluate_heldout=args.allow_heldout_evaluation,
        )
    )


if __name__ == "__main__":
    main()
