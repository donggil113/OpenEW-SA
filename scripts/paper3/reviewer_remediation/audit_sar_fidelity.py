"""Numerical fidelity audit against externally inspected official SAR, no RF metrics."""
import argparse,importlib.util,json,sys
from pathlib import Path
from copy import deepcopy
import numpy as np
import torch
from openew.paper3.wisig.models import IndependentClassifier
from openew.paper3.reviewer_remediation.methods import sar_adapt
from openew.paper3.reviewer_remediation.contracts import file_sha,create_once
p=argparse.ArgumentParser();p.add_argument("--official",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
sar=load("official_sar",a.official/"sar.py");sam=load("official_sam",a.official/"sam.py")
torch.set_num_threads(2);rows=[]
for seed in range(10):
    torch.manual_seed(seed);source=IndependentClassifier(6).eval()
    with torch.no_grad():
        source.classifier.weight.mul_(.05);source.classifier.bias.zero_();source.classifier.bias[0]=4
    x=torch.randn(64,256,2)
    ours,report=sar_adapt(source,x,6)
    official=sar.configure_model(deepcopy(source));params,_=sar.collect_params(official)
    adapter=sar.SAR(official,sam.SAM(params,torch.optim.SGD,lr=.00025,momentum=.9),margin_e0=.4*np.log(6))
    adapter(x)
    differences=[float((ours.state_dict()[k]-v).abs().max()) for k,v in official.state_dict().items()]
    error=max(differences);assert error<1e-6,(seed,error)
    assert report["gradient_steps"]==1 and report["recoveries"]==0
    rows.append({"seed":seed,"max_parameter_abs_error":error,"updated":True})
create_once(a.output,{"status":"PASS","scope":"10 synthetic single-update noncollapse cases, official SAR/SAM",
    "sar_sha256":file_sha(a.official/"sar.py"),"sam_sha256":file_sha(a.official/"sam.py"),"rows":rows,
    "limitation":"Support-only query protocol is intentionally different. Empty reliable subsets skip. Recovery clears SGD momentum, matching intended source reset; upstream SAM wrapper does not reliably restore base-optimizer momentum."})
print(json.dumps({"status":"PASS","cases":len(rows),"max_error":max(r["max_parameter_abs_error"] for r in rows)}))
