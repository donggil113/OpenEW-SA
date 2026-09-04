#!/usr/bin/env python3
"""Record the clean-code and complete-blind-suite freeze before unblinding."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.preunblind import create_preunblinding_freeze


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--split-manifest", required=True)
    parser.add_argument("--protocol-file", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = create_preunblinding_freeze(args.repository, args.run_root, args.split_root, args.split_manifest, args.protocol_file, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
