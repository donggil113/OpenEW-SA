#!/usr/bin/env python3
"""Inspect and safely extract the authorized official ManyRx archive once."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from openew.paper3.wisig.archive import (
    extract_zip_once,
    inspect_zip,
    mark_tree_read_only,
    write_json_atomic,
    write_raw_manifest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--extraction-root", type=Path, required=True)
    parser.add_argument("--analysis-root", type=Path, required=True)
    parser.add_argument("--download-utc", required=True)
    parser.add_argument("--official-page", required=True)
    parser.add_argument("--official-view-url", required=True)
    parser.add_argument("--resolved-url", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    archive_report = inspect_zip(args.archive)
    archive_report.update(
        {
            "download_utc": args.download_utc,
            "inspected_utc": datetime.now(timezone.utc).isoformat(),
            "official_page": args.official_page,
            "official_view_url": args.official_view_url,
            "resolved_url": args.resolved_url,
            "license": "CC BY-NC-SA 4.0",
            "redistribution": "PROHIBITED_BY_PROJECT_POLICY",
        }
    )
    args.analysis_root.mkdir(parents=True, exist_ok=True)
    write_json_atomic(args.analysis_root / "download_and_archive_manifest.json", archive_report)
    extracted = extract_zip_once(args.archive, args.extraction_root)
    raw_report = write_raw_manifest(
        args.extraction_root,
        args.analysis_root / "raw_manifest.csv",
        args.analysis_root / "RAW_SHA256SUMS.txt",
    )
    raw_report["extracted_files"] = [p.name for p in extracted]
    write_json_atomic(args.analysis_root / "raw_manifest_summary.json", raw_report)
    mark_tree_read_only(args.extraction_root)
    print(f"extracted {len(extracted)} file(s) to {args.extraction_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
