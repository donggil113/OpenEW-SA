"""Capture reproducibility metadata without usernames, tokens, URLs or host serials."""
import argparse,importlib.metadata,json,platform,subprocess,sys
from pathlib import Path
import torch
from openew.paper3.collection_runtime.storage import sha256,atomic_json
p=argparse.ArgumentParser();p.add_argument("--repo",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
packages={x.metadata["Name"]:x.version for x in importlib.metadata.distributions() if x.metadata.get("Name")}
try:
    gpu=subprocess.check_output(["nvidia-smi","--query-gpu=name,driver_version,memory.total","--format=csv,noheader"],text=True).strip()
except (FileNotFoundError,subprocess.CalledProcessError):gpu="UNAVAILABLE"
env={"python":sys.version,"os":platform.platform(),"torch":torch.__version__,"torch_cuda":torch.version.cuda,
    "cuda_available":torch.cuda.is_available(),"gpu_driver_summary":gpu,"packages":dict(sorted(packages.items())),
    "note":"Existing environment snapshot, not a claim of clean-machine installation; no secret or direct-url export."}
atomic_json(a.output/"environment.json",env)
required=["torch","numpy","pandas","matplotlib","scikit-learn","PyYAML","h5py","pyarrow","pytest"]
(a.output/"requirements-observed.txt").write_text("\n".join(k+"=="+importlib.metadata.version(k) for k in required)+"\n")
paths=["src/openew/paper3/wisig/models.py","src/openew/paper3/wisig/data.py",
    "src/openew/paper3/wisig_v2/models.py","src/openew/paper3/wisig_v2/runner.py",
    "src/openew/paper3/wisig_v2/support.py","src/openew/paper3/wisig_v2/statistics.py",
    "src/openew/paper3/receiver_adaptation/oracle.py","src/openew/paper3/receiver_adaptation/shen_adapter.py",
    "configs/paper3/wisig_v2/methods_v2.yaml"]
atomic_json(a.output/"frozen_method_code_hashes.json",{"baseline_merge":"7cc9a27a6cf049690c881068d9163b942c6a2110",
    "files":{v:sha256(a.repo/v) for v in paths},"method_changes":0})
print(json.dumps({k:v for k,v in env.items() if k!="packages"},indent=2))
