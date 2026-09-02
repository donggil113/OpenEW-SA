#!/usr/bin/env python3
"""Plan relation/episode coverage without making predictive power claims."""

from __future__ import annotations

import argparse
import json

from openew.paper3.dataset_qualification.planning import plan_structural_coverage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receivers", type=int, required=True)
    parser.add_argument("--sessions", type=int, required=True)
    parser.add_argument("--campaigns", type=int, required=True)
    parser.add_argument("--samples-per-session", type=int, required=True)
    parser.add_argument("--intra-session-correlation", type=float, required=True)
    parser.add_argument("--seeds", type=int, required=True)
    parser.add_argument("--mixed-label-sessions", type=int, required=True)
    parser.add_argument("--minimum-mixed-label-sessions", type=int, default=8)
    args = parser.parse_args()
    plan = plan_structural_coverage(
        receivers=args.receivers,
        sessions=args.sessions,
        campaigns=args.campaigns,
        samples_per_session=args.samples_per_session,
        expected_intra_session_correlation=args.intra_session_correlation,
        seed_count=args.seeds,
        mixed_label_sessions=args.mixed_label_sessions,
        minimum_mixed_label_sessions=args.minimum_mixed_label_sessions,
    )
    print(json.dumps(plan.to_mapping(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
