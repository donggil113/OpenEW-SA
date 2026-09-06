"""Observed package lock and immutable method paths, with no user/secret export."""
import argparse,importlib.metadata,json,platform,subprocess
from pathlib import Path
import torch
from openew.paper3.reviewer_remediation.contracts import file_sha
p=argparse.ArgumentParser();p.add_argument("--repository",type=Path,default=Path.cwd());a=p.parse_args()
repo=a.repository;out=repo/"papers/paper3_receiver_adaptation_manuscript/reproducibility_release";out.mkdir(exist_ok=True)
packages=sorted((d.metadata["Name"],d.version) for d in importlib.metadata.distributions() if d.metadata.get("Name"))
(out/"requirements-observed.lock").write_text("\n".join(n+"=="+v for n,v in packages)+"\n")
env={"python":platform.python_version(),"os":platform.platform(),"torch":torch.__version__,"cuda_runtime":torch.version.cuda,
 "gpu":torch.cuda.get_device_name() if torch.cuda.is_available() else None,"driver":subprocess.check_output(["nvidia-smi","--query-gpu=driver_version","--format=csv,noheader"],text=True).strip(),
 "note":"Observed compatible environment, not proof of a new clean-machine installation. No credentials or direct URL packages exported."}
(out/"environment.json").write_text(json.dumps(env,sort_keys=True,indent=2)+"\n")
paths=[]
for prefix in ["src/openew/paper3/wisig","src/openew/paper3/wisig_v2","src/openew/paper3/reviewer_remediation"]:
 paths.extend(sorted((repo/prefix).glob("*.py")))
paths.append(repo/"configs/paper3/reviewer_remediation/protocol.json")
(out/"method_hashes.json").write_text(json.dumps({str(x.relative_to(repo)):file_sha(x) for x in paths},sort_keys=True,indent=2)+"\n")
freeze=repo/"papers/paper3_reviewer_remediation/evidence/execution_freeze.json"
(out/"execution_freeze.json").write_bytes(freeze.read_bytes())
