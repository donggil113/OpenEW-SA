#!/usr/bin/env python3
"""Audit all V2 PNG/PDF figure pairs, font embedding, and page counts."""

from __future__ import annotations

import argparse
import json

from openew.paper3.wisig_v2.figure_audit import audit_figure_exports


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--figure-root", required=True); parser.add_argument("--output", required=True); args = parser.parse_args()
    print(json.dumps(audit_figure_exports(args.figure_root, args.output), indent=2))


if __name__ == "__main__":
    main()
