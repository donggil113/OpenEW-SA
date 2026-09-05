#!/usr/bin/env python3
"""Write the read-only V2 integrity gate for benchmark reuse."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from openew.paper3.receiver_adaptation.frozen import verify_frozen_v2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v2-root", required=True)
    parser.add_argument("--converted-root", required=True)
    parser.add_argument("--raw-archive", required=True)
    parser.add_argument("--addendum-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = verify_frozen_v2(args.v2_root, converted_root=args.converted_root, raw_archive=args.raw_archive, addendum_root=args.addendum_root)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(report.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
    print(json.dumps(report.to_dict(), sort_keys=True))


if __name__ == "__main__":
    main()
