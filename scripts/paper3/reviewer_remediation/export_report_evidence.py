"""Export small, hash-linked derived summaries; no RF or sample-level predictions."""
import argparse,json,shutil,hashlib,subprocess
from pathlib import Path
import pandas as pd
from openew.paper3.reviewer_remediation.contracts import file_sha,digest
p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--repository",type=Path,default=Path.cwd());a=p.parse_args()
repo=a.repository;root=a.output_root;analysis=root/"analysis";dest=repo/"papers/paper3_reviewer_remediation/evidence";dest.mkdir(exist_ok=True)
manifest=json.loads((analysis/"core_analysis_manifest.json").read_text())
for name,sha in manifest["files"].items():
 if file_sha(analysis/name)!=sha:raise RuntimeError("core analysis hash mismatch")
frame=pd.read_csv(analysis/"receiver_averaged_metrics.csv")
primary=frame[frame.scope=="primary"]
primary.to_csv(dest/"receiver_averages.csv",index=False)
cols=["macro_f1","accuracy","balanced_accuracy","ece","adaptive_ece","nll","brier","mean_confidence","confidence_accuracy_gap","entropy"]
primary.groupby(["method","probability_variant"])[cols].mean().reset_index().to_csv(dest/"primary_summary.csv",index=False)
frame[frame.scope=="budget"].groupby(["method","budget"])[cols].mean().reset_index().to_csv(dest/"new_budget_summary.csv",index=False)
bins=pd.read_csv(analysis/"reliability_bins.csv")
bins=bins[bins.method.isin(["P0","T3A","P2","SAR_GN","EMB_STD"])]
bins["confidence_sum"]=bins.confidence.fillna(0)*bins["count"];bins["correct_sum"]=bins.accuracy.fillna(0)*bins["count"]
agg=bins.groupby(["receiver","method","probability_variant","bin"])[["count","confidence_sum","correct_sum"]].sum().reset_index()
agg.to_csv(dest/"reliability_receiver_bins.csv",index=False)
for name in ("receiver_inference.json","catastrophic_adaptation.csv","analysis_validation.json","source_temperatures.csv"):
 shutil.copyfile(analysis/name,dest/name)
prior=repo/"papers/paper3_receiver_adaptation_manuscript/evidence"
for name in ("support_budget_summary.csv","hardware_family_summary.csv"):
 shutil.copyfile(prior/name,dest/("prior_"+name))
# No field is manually retyped into numerical claims.
lineage={"analysis_sha256":manifest["analysis_sha256"],"analysis_git_sha":manifest["git_sha"],
 "core_manifest_sha256":file_sha(analysis/"core_analysis_manifest.json"),"evidence":"POST_HOC_BASELINE_COMPLETENESS",
 "source_files":manifest["files"],"prior_evidence_manifest_sha256":file_sha(prior/"source_manifest.json"),
 "exports":{p.name:file_sha(p) for p in sorted(dest.iterdir()) if p.is_file() and p.name!="source_manifest.json"}}
(dest/"source_manifest.json").write_text(json.dumps(lineage,sort_keys=True,indent=2)+"\n")
print(pd.read_csv(dest/"primary_summary.csv").query("method in ['P0','P2','T3A','SAR_GN','EMB_STD','SUP_FT_FULL_128']")[["method","probability_variant","macro_f1","ece","nll","brier","mean_confidence","confidence_accuracy_gap"]].to_string(index=False))
