"""One GPU worker, source-only smoke or fully blinded support adaptation."""
import argparse,json,subprocess
from pathlib import Path
from openew.paper3.reviewer_remediation.runner import run_job
from openew.paper3.reviewer_remediation.contracts import SEEDS
from openew.paper3.wisig.data import ManyRxBundle

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data-root",type=Path,required=True)
    p.add_argument("--output-root",type=Path,required=True)
    p.add_argument("--repository",type=Path,default=Path.cwd())
    p.add_argument("--source-only-smoke",action="store_true")
    p.add_argument("--start-receiver",type=int,default=0)
    p.add_argument("--end-receiver",type=int,default=32)
    a=p.parse_args()
    if not a.source_only_smoke:
        if subprocess.check_output(["git","status","--porcelain"],cwd=a.repository,text=True).strip():
            raise RuntimeError("blind execution requires clean committed implementation")
        if not (a.output_root/"execution_freeze.json").exists():
            raise RuntimeError("execution freeze missing")
    bundle=ManyRxBundle.load(a.data_root/"paper3/wisig/converted/pass_a")
    receivers=[0] if a.source_only_smoke else range(a.start_receiver,a.end_receiver)
    for r in receivers:
        for seed in ([829] if a.source_only_smoke else SEEDS):
            result=run_job(a.data_root,a.output_root,a.repository,f"receiver_loso_{r:02d}",seed,bundle,a.source_only_smoke)
            print(json.dumps(result),flush=True)
if __name__=="__main__":main()
