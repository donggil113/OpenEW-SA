#!/usr/bin/env python3
"""Run preregistered P2 oracle-composition and sensitivity diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openew.paper3.wisig_v2.diagnostics import run_oracle_composition_diagnostics, run_p2_sensitivities


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--analysis-root", required=True)
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--sensitivity", action="store_true")
    args = parser.parse_args(); root = Path(args.analysis_root)
    result = {}
    if args.oracle:
        frame = run_oracle_composition_diagnostics(args.converted_root, args.split_root, args.run_root, root / "composition_oracle_results.csv")
        result["oracle_rows"] = len(frame)
    if args.sensitivity:
        frames = run_p2_sensitivities(args.converted_root, args.split_root, args.run_root, root)
        result.update({f"{key}_rows": len(value) for key, value in frames.items()})
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
