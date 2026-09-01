#!/usr/bin/env python
"""Run the frozen Paper 3 M0--M2 suite with checkpoint/resume."""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml

from openew.paper3.static_relational.runner import plan_full_suite, plan_smoke_suite, run_suite


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/paper3/static_relational/pilot.yaml"))
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--allow-heldout-evaluation", action="store_true")
    parser.add_argument("--seeds", nargs="+", type=int)
    parser.add_argument("--suite", choices=("all", "primary", "controls", "corruption", "ablations"), default="all")
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.smoke and args.allow_heldout_evaluation:
        raise ValueError("Smoke mode intentionally disables held-out evaluation")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_root = args.run_root or Path(config["output_roots"]["experiments"]) / f"static_relational_m0_m2_{timestamp}"
    specs = plan_smoke_suite(config) if args.smoke else plan_full_suite(config, args.seeds)
    if not args.smoke:
        specs = _filter_suite(specs, args.suite)
    (run_root / "configs").mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.config, run_root / "configs" / "pilot.yaml")
    summary = run_suite(
        config=config,
        run_root=run_root,
        specs=specs,
        resume=args.resume,
        smoke=args.smoke,
        evaluate_heldout=args.allow_heldout_evaluation,
    )
    print(f"RUN_ROOT={run_root}")
    print(yaml.safe_dump(summary, sort_keys=True))


def _filter_suite(specs, suite: str):
    if suite == "all":
        return specs
    if suite == "primary":
        return [item for item in specs if item.variant == "primary"]
    if suite == "controls":
        return [item for item in specs if item.variant == "shuffled_control"]
    if suite == "corruption":
        return [
            item
            for item in specs
            if item.model_stage == "m2"
            and not item.shuffled_relations
            and (item.variant == "primary" or item.variant.startswith("retention_"))
        ]
    return [
        item
        for item in specs
        if item.model_stage == "m2"
        and not item.shuffled_relations
        and item.variant in {"primary", "receiver_only", "date_only", "receiver_date_only", "retention_0"}
    ]


if __name__ == "__main__":
    main()
