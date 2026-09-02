#!/usr/bin/env python3
"""Run full converted-row, reproducibility, proxy, support, and index audits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openew.paper3.wisig.archive import write_json_atomic
from openew.paper3.wisig.reconciliation import reconcile_manyrx
from openew.paper3.wisig.validation import (
    compare_deterministic_passes,
    run_sample_level_qa,
    run_target_proxy_audit,
    write_support_outputs,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pass-a", type=Path, required=True)
    parser.add_argument("--pass-b", type=Path, required=True)
    parser.add_argument("--compact-pickle", type=Path, required=True)
    parser.add_argument("--full-summary-pickle", type=Path, required=True)
    parser.add_argument("--analysis-root", type=Path, required=True)
    args = parser.parse_args()
    args.analysis_root.mkdir(parents=True, exist_ok=True)
    deterministic = compare_deterministic_passes(args.pass_a, args.pass_b)
    qa = run_sample_level_qa(args.pass_a)
    proxy = run_target_proxy_audit(args.pass_a)
    support = write_support_outputs(args.pass_a, args.analysis_root)
    reconciliation = reconcile_manyrx(args.compact_pickle, args.full_summary_pickle, args.analysis_root)
    write_json_atomic(args.analysis_root / "conversion_reproducibility.json", deterministic)
    write_json_atomic(args.analysis_root / "sample_level_qa.json", qa)
    write_json_atomic(args.analysis_root / "target_proxy_audit.json", proxy)
    summary = {
        "status": "PASS" if deterministic["byte_identical"] and qa["status"] == proxy["status"] == reconciliation["status"] == "PASS" else "FAIL",
        "pass_a_b_deterministic": deterministic["byte_identical"],
        "sample_level_qa": qa["status"],
        "target_proxy_audit": proxy["status"],
        "raw_index_reconciliation": reconciliation["status"],
        "support": support,
    }
    write_json_atomic(args.analysis_root / "audit_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
