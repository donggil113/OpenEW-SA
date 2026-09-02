#!/usr/bin/env python3
"""Estimate prospective RF collection storage from explicit scenario inputs."""

from __future__ import annotations

import argparse
import json

from openew.paper3.dataset_qualification.planning import estimate_collection_storage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-rate", type=float, required=True)
    parser.add_argument("--sample-format", required=True)
    parser.add_argument("--channels", type=int, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--receivers", type=int, required=True)
    parser.add_argument("--sessions", type=int, required=True)
    parser.add_argument("--captures", type=int, required=True)
    parser.add_argument("--compression-low", type=float, default=0.65)
    parser.add_argument("--compression-high", type=float, default=0.95)
    parser.add_argument("--derived-ratio", type=float, default=0.10)
    parser.add_argument("--headroom", type=float, default=1.25)
    args = parser.parse_args()
    estimate = estimate_collection_storage(
        sample_rate_hz=args.sample_rate,
        sample_format=args.sample_format,
        channels=args.channels,
        duration_seconds=args.duration,
        receivers=args.receivers,
        sessions=args.sessions,
        captures_per_session=args.captures,
        compression_low_ratio=args.compression_low,
        compression_high_ratio=args.compression_high,
        derived_feature_ratio=args.derived_ratio,
        headroom_ratio=args.headroom,
    )
    print(json.dumps(estimate.to_mapping(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
