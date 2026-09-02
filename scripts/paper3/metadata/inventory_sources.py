#!/usr/bin/env python3
"""Inventory local OpenEW-SA data sources without hashing payloads."""

from __future__ import annotations

import argparse
import json

from openew.paper3.metadata.inventory import build_source_inventory, summarize_inventory, write_inventory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="/mnt/d/openew_sa_data")
    parser.add_argument(
        "--output-root", default="/mnt/d/openew_sa_data/paper3/source_forensics"
    )
    args = parser.parse_args()
    # Generated Paper 3 audit/run outputs are not source material and would make
    # the inventory self-referential on a second invocation.
    rows = build_source_inventory(
        args.data_root, excluded_roots=(f"{args.data_root}/paper3",)
    )
    write_inventory(
        rows,
        f"{args.output_root}/source_inventory.csv",
        f"{args.output_root}/source_inventory_summary.json",
    )
    print(json.dumps(summarize_inventory(rows), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
