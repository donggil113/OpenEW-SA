#!/usr/bin/env python3
"""Run resumable post-hoc P2 shuffled-context source training."""

from __future__ import annotations

import argparse
import json

from openew.paper3.v2_addendum.shuffled_training import run_shuffled_suite


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--v2-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--worker-index", type=int, default=0)
    parser.add_argument("--worker-count", type=int, default=1)
    args = parser.parse_args()
    records = run_shuffled_suite(
        args.repository,
        args.converted_root,
        args.split_root,
        args.output_root,
        v2_root=args.v2_root,
        worker_index=args.worker_index,
        worker_count=args.worker_count,
    )
    print(json.dumps({"worker_index": args.worker_index, "worker_count": args.worker_count, "completed": sum(r["status"] == "COMPLETE" for r in records), "failed": sum(r["status"] == "FAILED" for r in records)}, indent=2))


if __name__ == "__main__":
    main()
