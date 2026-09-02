#!/usr/bin/env python3
"""Recheck frozen repository trees and external WiSig source/conversion hashes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from openew.paper3.wisig.checkpoint import atomic_json
from openew.paper3.wisig.integrity import verify_integrity


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--repository",type=Path,required=True)
    parser.add_argument("--baseline-ref",default="origin/main")
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--pass-a",type=Path,required=True)
    parser.add_argument("--pass-b",type=Path,required=True)
    parser.add_argument("--expected-archive-sha256",required=True)
    parser.add_argument("--expected-manifest-sha256",required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=verify_integrity(args.repository,args.baseline_ref,args.archive,args.pass_a,args.pass_b,expected_archive_sha256=args.expected_archive_sha256,expected_manifest_sha256=args.expected_manifest_sha256)
    atomic_json(result,args.output); print(json.dumps(result,indent=2,sort_keys=True)); return 0 if result["status"]=="PASS" else 1


if __name__=="__main__": raise SystemExit(main())
