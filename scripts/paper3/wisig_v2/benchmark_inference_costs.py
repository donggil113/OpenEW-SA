#!/usr/bin/env python3
"""Benchmark label-free V2 inference on frozen seed-829 runs."""

from __future__ import annotations

import argparse

from openew.paper3.wisig_v2.inference_benchmark import benchmark_frozen_inference


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    frame = benchmark_frozen_inference(args.converted_root, args.split_root, args.run_root, args.output, repeats=args.repeats)
    print(f"wrote {len(frame)} label-free inference benchmark rows")


if __name__ == "__main__":
    main()
