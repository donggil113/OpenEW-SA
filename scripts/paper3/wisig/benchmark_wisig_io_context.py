#!/usr/bin/env python3
"""Benchmark logical data loading and target-neutral context assembly without inference."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from openew.paper3.wisig.checkpoint import atomic_json
from openew.paper3.wisig.context import build_context_episodes, episode_statistics
from openew.paper3.wisig.data import ManyRxBundle


def logical_dataset_bytes(root: Path) -> int:
    manifest = json.loads((root / "dataset_manifest.json").read_text(encoding="utf-8"))
    total = (root / "dataset_manifest.json").stat().st_size
    for shard in manifest["shards"]:
        directory = root / "shards" / shard["name"]
        for filename in shard["files"]:
            total += (directory / filename).stat().st_size
    return total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--converted-root", type=Path, required=True)
    parser.add_argument("--split-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--context-size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=829)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    bundle = ManyRxBundle.load(args.converted_root)
    load_seconds = time.perf_counter() - started
    rows = []
    for protocol in [f"receiver_fold_{index}" for index in range(5)]:
        split_path = args.split_root / protocol / "split_manifest.csv"
        split_started = time.perf_counter()
        partitions = bundle.split_indices(split_path)
        split_seconds = time.perf_counter() - split_started
        for partition, indices in sorted(partitions.items()):
            context_started = time.perf_counter()
            episodes = build_context_episodes(indices, bundle.receiver_ids, bundle.sample_ids, context_size=args.context_size, seed=args.seed, partition=partition, shuffled=False)
            context_seconds = time.perf_counter() - context_started
            rows.append({"protocol_id":protocol,"partition":partition,"sample_count":len(indices),"split_lookup_seconds":split_seconds,"context_assembly_seconds":context_seconds,"context_samples_per_second":len(indices)/context_seconds if context_seconds else None,**episode_statistics(episodes)})
    frame = pd.DataFrame(rows)
    frame.to_csv(args.output_root / "context_assembly_benchmark.csv", index=False, lineterminator="\n")
    summary = {
        "status":"PASS",
        "model_training_or_inference_performed":False,
        "context_fields":["receiver_id"],
        "context_size":args.context_size,
        "seed":args.seed,
        "logical_dataset_bytes":logical_dataset_bytes(args.converted_root),
        "bundle_load_seconds":load_seconds,
        "bundle_feature_array_bytes":int(bundle.features.nbytes),
        "context_assembly_seconds_mean":float(frame.context_assembly_seconds.mean()),
        "context_assembly_seconds_max":float(frame.context_assembly_seconds.max()),
        "context_samples_per_second_mean":float(frame.context_samples_per_second.mean()),
        "row_count":len(frame),
    }
    atomic_json(summary,args.output_root/"io_context_benchmark_summary.json")
    print(json.dumps(summary,indent=2,sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())
