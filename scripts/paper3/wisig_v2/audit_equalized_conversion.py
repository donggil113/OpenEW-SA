#!/usr/bin/env python3
"""Audit deterministic official-equalized WiSig conversion without training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openew.paper3.wisig.archive import write_json_atomic
from openew.paper3.wisig.validation import (
    compare_deterministic_passes,
    run_sample_level_qa,
    run_target_proxy_audit,
    write_support_outputs,
)
from openew.paper3.wisig_v2.equalized import compare_raw_structure, validate_equalized_manifests


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pass-a", type=Path, required=True)
    parser.add_argument("--pass-b", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--analysis-root", type=Path, required=True)
    args = parser.parse_args(); args.analysis_root.mkdir(parents=True, exist_ok=True)
    manifest = validate_equalized_manifests(args.pass_a, args.pass_b)
    reproducibility = compare_deterministic_passes(args.pass_a, args.pass_b)
    qa = run_sample_level_qa(args.pass_a)
    proxy = run_target_proxy_audit(args.pass_a)
    structure = compare_raw_structure(args.raw_root, args.pass_a)
    support = write_support_outputs(args.pass_a, args.analysis_root)
    write_json_atomic(args.analysis_root / "equalized_manifest_validation.json", manifest)
    write_json_atomic(args.analysis_root / "equalized_conversion_reproducibility.json", reproducibility)
    write_json_atomic(args.analysis_root / "equalized_sample_level_qa.json", qa)
    write_json_atomic(args.analysis_root / "equalized_target_proxy_audit.json", proxy)
    write_json_atomic(args.analysis_root / "equalized_raw_structure_comparison.json", structure)
    summary = {
        "status": "PASS" if manifest["status"] == qa["status"] == proxy["status"] == structure["status"] == "PASS" and reproducibility["byte_identical"] else "FAIL",
        "pass_a_b_deterministic": reproducibility["byte_identical"],
        "manifest_validation": manifest["status"],
        "sample_level_qa": qa["status"],
        "target_proxy_audit": proxy["status"],
        "raw_structure_comparison": structure["status"],
        "support": support,
    }
    write_json_atomic(args.analysis_root / "equalized_audit_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
