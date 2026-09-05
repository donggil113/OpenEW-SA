#!/usr/bin/env python3
"""Estimate capture time and storage for a prospective collection."""

from __future__ import annotations
import argparse
import json
from openew.paper3.receiver_adaptation.collection import estimate_collection_storage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receivers", type=int, required=True)
    parser.add_argument("--transmitters", type=int, required=True)
    parser.add_argument("--sample-rate", type=float, required=True)
    parser.add_argument("--sample-format", choices=("ci8", "ci16_le", "cf32_le", "cf64_le"), required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--sessions-per-receiver", type=int, required=True)
    parser.add_argument("--sites", type=int, required=True)
    parser.add_argument("--days", type=int, required=True)
    parser.add_argument("--captures-per-session", type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(estimate_collection_storage(receivers=args.receivers, transmitters=args.transmitters, sample_rate_hz=args.sample_rate, sample_format=args.sample_format, capture_duration_seconds=args.duration, sessions_per_receiver=args.sessions_per_receiver, sites=args.sites, days=args.days, captures_per_session=args.captures_per_session), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
