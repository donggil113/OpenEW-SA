"""Final read-only execution reconciliation, distinct from one-time unblinding."""
import argparse,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
from openew.paper3.reviewer_remediation.analysis import preflight
from openew.paper3.reviewer_remediation.contracts import create_once,file_sha,FROZEN_SHA
p=argparse.ArgumentParser();p.add_argument("--repository",type=Path,default=Path.cwd());p.add_argument("--data-root",type=Path,required=True);p.add_argument("--output-root",type=Path,required=True);a=p.parse_args()
changes=subprocess.check_output(["git","diff","--name-status",FROZEN_SHA],cwd=a.repository,text=True).splitlines()
if any(not x.startswith("A\t") for x in changes):raise RuntimeError("pre-existing tracked files changed")
result=preflight(a.data_root,a.output_root,a.repository)
unblind=json.loads((a.output_root/"unblinding_manifest.json").read_text())
assert result["prediction_manifest_sha256"]==unblind["prediction_manifest_sha256"]
result.pop("prediction_hashes")
prior={}
for name in ["frozen_after.json","conversion_after.json"]:
 report=json.loads((a.output_root/name).read_text());assert report["status"]=="PASS"
 prior[name]={"sha256":file_sha(a.output_root/name),"status":"PASS","scope":report["scope"]}
result.update({"utc":datetime.now(timezone.utc).isoformat(),"prior_git_base":FROZEN_SHA,
 "existing_tracked_files_modified":0,"prior_artifact_audits":prior,
 "unblinding_event_unchanged":True,"new_metric_computation":False})
print(create_once(a.output_root/"final_execution_integrity.json",result))
