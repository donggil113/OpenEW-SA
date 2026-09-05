#!/usr/bin/env python3
"""Metadata export, tier QA and planning; does not acquire RF or train."""
import argparse,json
from pathlib import Path
from openew.paper3.collection_runtime.release import export_metadata,assess_collection,estimate_storage
p=argparse.ArgumentParser();p.add_argument("command",choices=["export","readiness","estimate"]);p.add_argument("--spec",type=Path,required=True)
a=p.parse_args();s=json.loads(a.spec.read_text())
result={"export":export_metadata,"readiness":assess_collection,"estimate":estimate_storage}[a.command](**s)
print(json.dumps(result,indent=2))
