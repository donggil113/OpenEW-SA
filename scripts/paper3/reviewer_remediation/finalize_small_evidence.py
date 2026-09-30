"""Finalize portable small technical summaries after immutable core analysis."""
import argparse,json,shutil
from pathlib import Path
import pandas as pd
from openew.paper3.reviewer_remediation.contracts import file_sha
p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--repository",type=Path,default=Path.cwd());a=p.parse_args()
d=a.repository/"papers/paper3_reviewer_remediation/evidence";r=a.output_root
timing=pd.read_csv(r/"timing_replay/timing_records.csv")
timing["total_samples_per_second"]=timing["query_count"]/timing["total_seconds"]
timing.groupby(["receiver","method"]).mean(numeric_only=True).groupby("method").mean(numeric_only=True).reset_index().to_csv(d/"timing_summary.csv",index=False)
cost=pd.read_csv(r/"analysis/compute_records.csv");cost=cost[cost.scope=="primary"]
cost.groupby("method").mean(numeric_only=True).reset_index().to_csv(d/"execution_cost_summary.csv",index=False)
jobs=[json.loads(x.read_text()) for x in sorted((r/"experiments").glob("*/source_validation.json"))]
recipes=pd.Series([str(x["selected_oracle_recipe"]) for x in jobs]).value_counts().rename_axis("source_selected_recipe").reset_index(name="protocol_seed_count")
recipes.to_csv(d/"oracle_recipe_counts.csv",index=False)
for src,name in [(r/"timing_replay/manifest.json","timing_manifest.json"),(r/"collection_stress_v1/stress_report.json","collection_stress.json"),
(r/"execution_freeze.json","execution_freeze.json"),(r/"unblinding_manifest.json","unblinding_manifest.json")]:
 shutil.copyfile(src,d/name)
prior=a.repository/"papers/paper3_receiver_adaptation_manuscript/evidence"
shutil.copyfile(prior/"receiver_level_inference.json",d/"prior_receiver_inference.json")
manifest=json.loads((d/"source_manifest.json").read_text())
manifest["exports"]={p.name:file_sha(p) for p in sorted(d.iterdir()) if p.is_file() and p.name!="source_manifest.json"}
(d/"source_manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
print(timing.groupby("method")[["total_seconds","samples_per_second"]].mean().to_string())
print(cost[cost.method=="SAR_GN"][["gradient_steps","recoveries","empty_first_filter","empty_second_filter"]].describe().to_string())
