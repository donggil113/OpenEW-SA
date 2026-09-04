#!/usr/bin/env python3
"""Generate measured and explicitly approximate V2 compute disclosures."""

from __future__ import annotations

import argparse

from openew.paper3.wisig_v2.compute_audit import generate_compute_audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--split-root", required=True)
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    frame = generate_compute_audit(args.run_root, args.split_root, args.output, converted_root=args.converted_root)
    print(f"wrote {len(frame)} compute-audit rows")


if __name__ == "__main__":
    main()
