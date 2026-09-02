#!/usr/bin/env python3
"""Create a checksum manifest for bounded official metadata acquisitions."""

from __future__ import annotations

import argparse

from openew.paper3.dataset_qualification.manifest import build_metadata_manifest, write_manifest_atomic


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-url", action="append", default=[])
    parser.add_argument("--source-version", action="append", default=[])
    parser.add_argument("--license-evidence", required=True)
    args = parser.parse_args()
    versions: dict[str, str] = {}
    for item in args.source_version:
        if "=" not in item:
            raise ValueError("--source-version values must use name=commit")
        name, value = item.split("=", 1)
        versions[name] = value
    manifest = build_metadata_manifest(
        args.root,
        source_urls=tuple(args.source_url),
        license_evidence=args.license_evidence,
        source_versions=versions,
    )
    write_manifest_atomic(args.output, manifest)
    print(f"manifest files={manifest['file_count']} bytes={manifest['total_size_bytes']}")


if __name__ == "__main__":
    main()
