#!/usr/bin/env python3
"""Create the immutable benchmark pre-target freeze."""

from __future__ import annotations
import argparse
import json
from openew.paper3.receiver_adaptation.pretarget import create_pretarget_freeze


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--preregistration", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--frozen-integrity", required=True)
    args = parser.parse_args()
    payload = create_pretarget_freeze(args.repository, args.output, preregistration=args.preregistration, config=args.config, frozen_integrity=args.frozen_integrity)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
