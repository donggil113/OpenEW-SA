"""Read-only post-hoc P0 rescore on the frozen common-256 query universe."""
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig.metrics import classification_metrics
from openew.paper3.wisig_v2.runner import remap_bundle_to_split_targets
from openew.paper3.wisig_v2.support import freeze_support_query
from openew.paper3.wisig_v2.blinding import read_blind_predictions
from openew.paper3.wisig_v2.hashing import sha256_file

p=argparse.ArgumentParser()
p.add_argument("--data-root",type=Path,required=True)
p.add_argument("--output",type=Path,required=True)
a=p.parse_args()
if a.output.exists() and any(a.output.iterdir()): raise FileExistsError(a.output)
a.output.mkdir(parents=True,exist_ok=True)
root=a.data_root/"paper3"
bundle=ManyRxBundle.load(root/"wisig/converted/pass_a")
splits=root/"wisig_v2/splits_v2_frozen"
runs=root/"wisig_v2/experiments/confirmatory_v2/runs"
frozen=pd.read_csv(root/"wisig_v2/analysis/confirmatory_v2/primary_receiver_seed_results.csv")
budget=pd.read_csv(root/"v2_addendum/analysis_support_budget.csv")
prior=budget[budget.method=="T3A"]
assert len(prior)==32*5*5 and set(prior.support_budget)=={16,32,64,128,256}
rows=[]
for receiver_number in range(32):
 protocol=f"receiver_loso_{receiver_number:02d}"
 local=remap_bundle_to_split_targets(bundle,splits/protocol/"split_summary.json")
 roles=local.split_indices(splits/protocol/"split_manifest.csv")
 receiver=str(local.receiver_ids[roles["test"][0]])
 lookup={str(sid):i for i,sid in enumerate(local.sample_ids)}
 for seed in [829,1829,2829,3829,4829]:
  run=runs/f"{protocol}__p0__s{seed}__b128__k32__r100__raw"
  record=json.loads((run/"run.json").read_text())
  archive=run/"predictions_blind.npz"
  assert sha256_file(archive)==record["target_prediction_sha256"]
  payload=read_blind_predictions(archive)
  primary=freeze_support_query(roles["test"],local.sample_ids,local.receiver_ids,receiver_id=receiver,support_budget=128,seed=seed)
  common=freeze_support_query(roles["test"],local.sample_ids,local.receiver_ids,receiver_id=receiver,support_budget=256,seed=seed)
  primary_ids=local.sample_ids[np.asarray(primary.query_indices)]
  common_ids=local.sample_ids[np.asarray(common.query_indices)]
  if not np.array_equal(payload["sample_ids"],primary_ids):raise RuntimeError("P0 primary query identity mismatch")
  index={str(sid):i for i,sid in enumerate(payload["sample_ids"])}
  if len(index)!=len(primary_ids) or not set(map(str,common_ids)).issubset(index):raise RuntimeError("common query not subset of primary")
  baseline=frozen[(frozen.protocol_id==protocol)&(frozen.seed==seed)&(frozen.model=="P0")]
  if len(baseline)!=1 or int(baseline.iloc[0].query_count)!=len(primary_ids):raise RuntimeError("frozen row mismatch")
  source_labels=local.labels[np.asarray(primary.query_indices)]
  source_f1=classification_metrics(source_labels,payload["probabilities"])["macro_f1"]
  if abs(source_f1-float(baseline.iloc[0].macro_f1))>1e-10:raise RuntimeError("P0 frozen metric not reproduced")
  subset=np.asarray([index[str(sid)] for sid in common_ids])
  labels=local.labels[np.asarray([lookup[str(sid)] for sid in common_ids])]
  p0=classification_metrics(labels,payload["probabilities"][subset])["macro_f1"]
  t=prior[(prior.protocol_id==protocol)&(prior.seed==seed)]
  if len(t)!=5 or not (t.query_count==len(common_ids)).all() or not (t.common_query_budget==256).all():raise RuntimeError("budget query scope mismatch")
  for _,r in t.iterrows():
   rows.append(dict(protocol_id=protocol,receiver_id=receiver,seed=seed,support_budget=int(r.support_budget),
    common_query_count=len(common_ids),p0_common_query_f1=p0,t3a_common_query_f1=float(r.macro_f1),
    t3a_minus_p0=float(r.macro_f1)-p0,p0_prediction_sha256=sha256_file(archive),
    source_budget_row="v2_addendum/analysis_support_budget.csv",status="POST_HOC_RESCORING_NO_NEW_PREDICTION"))
frame=pd.DataFrame(rows).sort_values(["protocol_id","seed","support_budget"])
assert len(frame)==800
frame.to_csv(a.output/"matched_p0_budget_receiver_seed.csv",index=False)
rec=frame.groupby(["receiver_id","support_budget"])[["p0_common_query_f1","t3a_common_query_f1","t3a_minus_p0"]].mean().reset_index()
summary=rec.groupby("support_budget")[["p0_common_query_f1","t3a_common_query_f1","t3a_minus_p0"]].mean().reset_index()
summary.to_csv(a.output/"matched_p0_budget_summary.csv",index=False)
payload={"status":"PASS","evidence":"POST_HOC_RESCORING_OF_FROZEN_P0_PREDICTIONS","receiver_count":32,"seeds":5,
 "primary_query_budget":128,"common_query_budget":256,"receiver_seed_budget_rows":800,
 "all_primary_p0_metrics_reproduced":True,"no_new_model_prediction":True,
 "source_p0_archives":160,"support_budget_rows_per_pair":5,
 "frozen_v2_primary_csv_sha256":sha256_file(root/"wisig_v2/analysis/confirmatory_v2/primary_receiver_seed_results.csv"),
 "frozen_t3a_budget_csv_sha256":sha256_file(root/"v2_addendum/analysis_support_budget.csv"),
 "summary_sha256":sha256_file(a.output/"matched_p0_budget_summary.csv")}
(a.output/"matched_p0_budget_audit.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
print(summary.to_string(index=False))
