"""Timing-only replay: no metrics, no checkpoints/predictions overwritten."""
import argparse,json,time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from openew.paper3.reviewer_remediation.runner import load_model,predict_new,split_for,sync
from openew.paper3.reviewer_remediation.contracts import create_once,file_sha
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig_v2.runner import remap_bundle_to_split_targets,RunConfig,_evaluate_condition_on_role,_encode_backbone,set_determinism
from openew.paper3.wisig_v2.blinding import read_blind_predictions
p=argparse.ArgumentParser();p.add_argument("--data-root",type=Path,required=True);p.add_argument("--output-root",type=Path,required=True)
a=p.parse_args();out=a.output_root/"timing_replay"
if not (a.output_root/"analysis/core_analysis_manifest.json").exists():raise RuntimeError("core analysis must be frozen first")
out.mkdir(exist_ok=False);root=a.data_root/"paper3";v2=root/"wisig_v2";runs=v2/"experiments/confirmatory_v2"
base=ManyRxBundle.load(root/"wisig/converted/pass_a");device=torch.device("cuda")
torch.set_num_threads(4);set_determinism(829);rows=[]
for receiver in range(32):
 protocol=f"receiver_loso_{receiver:02d}";local=remap_bundle_to_split_targets(base,v2/"splits_v2_frozen"/protocol/"split_summary.json")
 roles=local.split_indices(v2/"splits_v2_frozen"/protocol/"split_manifest.csv")
 rx=sorted(set(map(str,local.receiver_ids[roles["test"]])))[0];split=split_for(local,roles["test"],rx,829)
 p0,_,_=load_model(runs,protocol,829,"P0",6,device);p2,_,_=load_model(runs,protocol,829,"P2",6,device)
 job=a.output_root/"experiments"/f"{protocol}__s829";source=json.loads((job/"source_validation.json").read_text())
 moments=(np.array(source["source_mean"]),np.array(source["source_std"]))
 t3a=json.loads((runs/"runs"/f"{protocol}__t3a__s829__b128__k32__r100__raw"/"run.json").read_text())["selected_t3a_filter_source_validation_only"]
 for method in ("P0","T3A","P2","SAR_GN","EMB_STD","SUP_FT_FULL_128"):
  old=method in ("P0","T3A","P2");model=p2 if method=="P2" else p0;model.eval()
  if old:ref=runs/"runs"/f"{protocol}__{method.lower()}__s829__b128__k32__r100__raw"/"predictions_blind.npz"
  else:
   record=next(x for x in job.glob("*/run.json") if (lambda r:r["method"]==method and r["scope"]=="primary")(json.loads(x.read_text())))
   ref=record.parent/"predictions_blind.npz"
  frozen=read_blind_predictions(ref)
  # Warm-up fixed shape; never adapts query data.
  with torch.no_grad():_encode_backbone(model,local,split.support_indices,device,1024)
  for repetition in range(3):
   sync(device);torch.cuda.reset_peak_memory_stats(device);start=time.perf_counter()
   if old:
    order,probs,_=_evaluate_condition_on_role(method,model,local,roles["test"],roles["validation"],device,RunConfig(protocol,method,829),t3a_filter_k=t3a)
    costs={}
   else:
    probs,costs,_=predict_new(method,p0,local,split.support_indices,split.query_indices,device,moments,tuple(source["selected_oracle_recipe"]))
    order=np.asarray(split.query_indices)
   sync(device);elapsed=time.perf_counter()-start
   if not np.array_equal(local.sample_ids[order],frozen["sample_ids"]) or not np.allclose(probs,frozen["probabilities"],rtol=1e-5,atol=1e-6):
    raise RuntimeError("timing replay changed frozen prediction content")
   rows.append({"receiver":rx,"protocol":protocol,"seed":829,"method":method,"repetition":repetition,
    "total_seconds":elapsed,"query_count":len(order),"samples_per_second":len(order)/elapsed,
    "peak_gpu_memory_bytes":torch.cuda.max_memory_allocated(device),"parameter_count":sum(x.numel() for x in model.parameters()),
    "prediction_sha256":file_sha(ref),"max_probability_error":float(np.max(np.abs(probs-frozen["probabilities"]))),
    **costs})
 print(json.dumps({"timing_receiver_complete":receiver}),flush=True)
pd.DataFrame(rows).to_csv(out/"timing_records.csv",index=False)
create_once(out/"manifest.json",{"status":"PASS","records":len(rows),"receivers":32,"seed":829,"repeats":3,
 "hardware":torch.cuda.get_device_name(),"torch":torch.__version__,"cuda":torch.version.cuda,
 "kind":"TIMING_ONLY_REPLAY_NO_NEW_METRICS","sha256":file_sha(out/"timing_records.csv"),
 "scope":"Resident converted data; P0 and P2 resident; includes support selection and CPU context assembly for old methods; excludes checkpoint IO.",
 "limitations":"One seed for timing only; three repeats; no isolated prototype/query split for T3A; GPU peak includes resident models."})
