"""Create-once final addendum package manifest; never edits scientific artifacts."""
import argparse,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
from openew.paper3.reviewer_remediation.contracts import create_once,file_sha,digest
p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--repository",type=Path,default=Path.cwd());a=p.parse_args()
root=a.output_root
integrity=json.loads((root/"final_execution_integrity.json").read_text());assert integrity["status"]=="PASS"
assert json.loads((root/"fresh_clone_validation/report.json").read_text())["status"]=="PASS"
core=json.loads((root/"analysis/core_analysis_manifest.json").read_text())
for name,sha in core["files"].items():assert file_sha(root/"analysis"/name)==sha
paths=set()
for folder in ["analysis","figures_release_final","timing_replay"]:
 paths.update(x for x in (root/folder).rglob("*") if x.is_file())
for name in ["frozen_before.json","frozen_after.json","conversion_after.json","execution_freeze.json",
 "prediction_manifest.json","unblinding_manifest.json","sar_fidelity.json","final_execution_integrity.json",
 "collection_stress_v1/stress_report.json","logs/final_tests.xml","pdf_release_audit/audit.json",
 "fresh_clone_validation/report.json","fresh_clone_validation/tests.xml","fresh_clone_validation/pdf_audit/audit.json"]:
 paths.add(root/name)
paths.update((root/"pdf_release").glob("*.pdf"))
paths.update((root/"pdf_release").glob("*_build.log"))
paths.update((root/"fresh_clone_validation").glob("step_*.log"))
registry={str(x.relative_to(root)):file_sha(x) for x in sorted((root/"experiments").glob("*/*/run.json"))}
assert len(registry)==2400
files={str(x.relative_to(root)):file_sha(x) for x in sorted(paths)}
report={"utc":datetime.now(timezone.utc).isoformat(),"git_sha":subprocess.check_output(["git","rev-parse","HEAD"],cwd=a.repository,text=True).strip(),
 "evidence":"POST_HOC_BASELINE_COMPLETENESS","core_analysis_sha256":core["analysis_sha256"],
 "files":files,"file_count":len(files),"run_registry":registry,"run_registry_sha256":digest(registry),
 "scientific_prediction_manifest_sha256":integrity["prediction_manifest_sha256"],
 "scope":"Final analysis, final figures/PDFs, timing, durability and reproducibility reports. Superseded PDF drafts, literature payloads and raw predictions are excluded; predictions are bound by their immutable manifest."}
print(create_once(root/"final_package_manifest.json",report))
