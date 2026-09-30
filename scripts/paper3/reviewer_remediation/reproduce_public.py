"""One-command, RF-payload-absent validation and manuscript reproduction."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from openew.paper3.reviewer_remediation.contracts import file_sha
p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--access-template",type=Path);a=p.parse_args()
repo=Path(__file__).resolve().parents[3];a.output.mkdir(parents=True,exist_ok=False)
release=repo/"papers/paper3_receiver_adaptation_manuscript/reproducibility_release"
for name,sha in json.loads((release/"method_hashes.json").read_text()).items():
 if file_sha(repo/name)!=sha:raise RuntimeError("method code hash mismatch: "+name)
e=repo/"papers/paper3_reviewer_remediation/evidence"
for name,sha in json.loads((release/"expected_checksums.json").read_text()).items():
 if file_sha(repo/name)!=sha:raise RuntimeError("release checksum mismatch: "+name)
for name,sha in json.loads((e/"source_manifest.json").read_text())["exports"].items():
 if file_sha(e/name)!=sha:raise RuntimeError("evidence hash mismatch: "+name)
env={**os.environ,"PYTHONPATH":str(repo/"src")+os.pathsep+str(repo/"tests/paper3/metadata")}
commands=[
 [sys.executable,"-m","pytest","--import-mode=importlib","-q","tests/paper3","papers/paper2_ood_rf_signal_recognition/tests","--junitxml="+str(a.output/"tests.xml")],
 [sys.executable,"-m","compileall","-q","src/openew/paper3","scripts/paper3","tests/paper3"],
 [sys.executable,"scripts/paper3/reviewer_remediation/render_release_assets.py","--repository",str(repo),"--png-output",str(a.output/"figures")],
 [sys.executable,"scripts/paper3/reviewer_remediation/build_pdfs.py","--repository",str(repo),"--output",str(a.output/"pdf")]
]
if a.access_template:commands[-1]+=["--access-template",str(a.access_template.resolve())]
commands.append([sys.executable,"scripts/paper3/reviewer_remediation/audit_release.py","--repository",str(repo),"--pdf-root",str(a.output/"pdf"),"--output",str(a.output/"pdf_audit")])
commands.append(["git","diff","--check"])
for i,command in enumerate(commands):
 result=subprocess.run(command,cwd=repo,env=env,capture_output=True,text=True)
 (a.output/f"step_{i}.log").write_text(result.stdout+result.stderr)
 if result.returncode:raise RuntimeError("public reproduction failed at step "+str(i))
for name,sha in json.loads((release/"expected_checksums.json").read_text()).items():
 if file_sha(repo/name)!=sha:raise RuntimeError("nondeterministic release rebuild: "+name)
(a.output/"report.json").write_text(json.dumps({"status":"PASS","rf_payload_required":False,"steps":len(commands),
 "access_variant":bool(a.access_template),"environment_scope":"same installed environment unless operator builds a new one"},indent=2)+"\n")
print("PUBLIC_PAYLOAD_ABSENT_REPRODUCTION_PASS")
