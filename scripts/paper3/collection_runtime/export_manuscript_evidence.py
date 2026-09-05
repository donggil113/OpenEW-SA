"""Read frozen results; export small, traceable manuscript evidence. Never train."""
from pathlib import Path
import argparse, hashlib, json, subprocess
import numpy as np
import pandas as pd

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+"\n")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,required=True)
    p.add_argument("--data-root",type=Path,required=True)
    a=p.parse_args()
    out=a.repo/"papers/paper3_receiver_adaptation_manuscript/evidence"
    out.mkdir(parents=True,exist_ok=True)
    root=a.data_root/"paper3/receiver_adaptation_benchmark/analysis"
    manifest=json.loads((root/"analysis_manifest.json").read_text())
    for item in manifest["files"]:
        assert sha(root/item["path"])==item["sha256"],item["path"]
    sources={}; trace=[]
    names=["benchmark_summary.csv","benchmark_receiver_averaged_results.csv","benchmark_receiver_seed_results.csv",
           "primary_receiver_summary.csv","support_budget_summary.csv","calibration_quality_summary.csv",
           "hardware_family_summary.csv","compute_fairness_summary.csv","catastrophic_failure_summary.csv"]
    textcols={"method","model","metric","receiver_id","hardware_family","protocol_id","condition","reference","comparison"}
    for name in names:
        path=root/name
        frame=pd.read_csv(path,keep_default_na=False)
        frame=frame.drop(columns=[c for c in frame if "prediction_sha" in c],errors="ignore")
        frame.to_csv(out/name,index=False,float_format="%.17g")
        sources[name]={"source_file":str(path),"sha256":sha(path),"export_sha256":sha(out/name),
                      "row_count":len(frame),"analysis_sha":manifest["manifest_sha256"],
                      "git_sha":"9ed8dc8b89b6dbaf11191e4932320f857ec0817a",
                      "protocol":"WiSig V2 32-receiver LOSO; support-budget query reserves 256",
                      "unit":"receiver x seed" if "seed_results" in name else "receiver; five seeds averaged within receiver"}
        if "seed_results" not in name:
            for i,row in frame.iterrows():
                keys=", ".join(f"{c}={row[c]}" for c in frame if c in textcols or c=="support_budget")
                trace.append(f"| {name} | CSV data row {i+1}: {keys} | all numeric columns, verbatim | receiver / seed-within-receiver | {sources[name]['sha256']} |")
    inference=json.loads((root/"receiver_level_inference.json").read_text())
    dump(out/"receiver_level_inference.json",inference)
    sources["receiver_level_inference.json"]={"source_file":str(root/"receiver_level_inference.json"),
        "sha256":sha(root/"receiver_level_inference.json"),"export_sha256":sha(out/"receiver_level_inference.json"),
        "analysis_sha":manifest["manifest_sha256"],"git_sha":"9ed8dc8b89b6dbaf11191e4932320f857ec0817a",
        "unit":"receiver-level paired difference after within-receiver five-seed averaging"}
    add=a.data_root/"paper3/v2_addendum"
    for name in ["summary_composition_stress.csv","summary_query_coupling.csv","summary_shuffled_training.csv","summary_support_budget.csv"]:
        frame=pd.read_csv(add/name,keep_default_na=False)
        frame.to_csv(out/("addendum_"+name),index=False,float_format="%.17g")
        key="addendum_"+name
        sources[key]={"source_file":str(add/name),"sha256":sha(add/name),"export_sha256":sha(out/key),
                     "git_sha":subprocess.check_output(["git","log","-1","--format=%H","d4112ba","--","src/openew/paper3/v2_addendum"],cwd=a.repo,text=True).strip(),
                     "analysis_sha":sha(add/"analysis_manifest.json") if (add/"analysis_manifest.json").exists() else "see PR87 immutable manifest",
                     "evidence_type":"POST-HOC","unit":"receiver; five seeds averaged"}
        for i,row in frame.iterrows():
            trace.append(f"| {key} | data row {i+1}: "+", ".join(f"{c}={row[c]}" for c in frame if c in textcols)+" | numeric columns verbatim | POST-HOC receiver | "+sources[key]["sha256"]+" |")
    seed=pd.read_csv(out/"benchmark_receiver_seed_results.csv",keep_default_na=False)
    assert not seed.duplicated(["receiver_id","seed","model"]).any()
    assert seed.receiver_id.nunique()==32
    assert set(seed.seed)=={829,1829,2829,3829,4829}
    for _,group in seed.groupby("model"):
        assert len(group)==160
        assert np.isfinite(group[["macro_f1","accuracy","balanced_accuracy","ece"]].to_numpy(float)).all()
    grouped=seed.groupby(["receiver_id","model"]).macro_f1.mean().unstack()
    d=grouped.T3A-grouped.P0
    frozen=inference["T3A_MINUS_P0"]
    assert np.isclose(d.mean(),frozen["receiver_delta_summary"]["mean"],atol=1e-13)
    assert int((d>0).sum())==31
    summary=pd.read_csv(out/"benchmark_summary.csv")
    for model,values in grouped.items():
        value=summary[(summary.model==model)&(summary.metric=="macro_f1")]["mean"].item()
        assert np.isclose(value,values.mean(),atol=1e-13)
    dump(out/"source_manifest.json",{"schema_version":1,"sources":sources,
        "baseline_merge":"7cc9a27a6cf049690c881068d9163b942c6a2110",
        "frozen_package_manifest_file_sha256":sha(root/"analysis_manifest.json"),
        "scientific_new_runs":0,"validated_rows":len(seed),"validated_receivers":32,
        "note":"No packet features, packet annotations, original target-bearing paths, or prediction arrays. Aggregate provenance includes source-summary paths."})
    tracehead="""# Numerical traceability matrix

Generated BEFORE manuscript prose by export_manuscript_evidence.py. Exact export code and source hashes are committed.
Every source row below is copied without re-estimation; row numbering excludes the header.
Machine-readable evidence/source_manifest.json supplies each source's absolute path, original SHA256, analysis SHA and Git SHA.
The primary outcome is the equal-weight mean over 32 receivers after averaging five seeds within receiver.
Macro-F1 is in [0,1]; differences are absolute, not relative percentages.
Budget results use a common query pool reserving 256 and must not be substituted for the 128-support primary mean.
The addendum is POST-HOC. Later T3A inference was specified after earlier WiSig outcomes, not independent confirmatory replication.

| Source export | Row/key / method | Numerical claim mapping | Unit/protocol | Original source SHA256 |
|---|---|---|---|---|
"""
    (out.parent/"numerical_traceability_matrix.md").write_text(tracehead+"\n".join(trace)+"\n\n## Inferential keys\n\nreceiver_level_inference.json: T3A_MINUS_P0.bootstrap, .sign_flip, .receiver_delta_summary, .positive_receivers, .negative_receivers, .standardized_mean_difference, and holm_adjusted.T3A_MINUS_P0 map exactly to manuscript inference macros. Protocol constants map to frozen papers/paper3_wisig_methods_remediation/{split_freeze_v2,model_config_freeze_v2,methods_remediation_preregistration_v2}.md; the baseline Git merge is recorded in the manifest. No approximate values substitute for exact exported cells.\n")
    print(json.dumps({"status":"PASS","sources":len(sources),"rows":len(seed),"receivers":32,"output":str(out)}))
if __name__=="__main__": main()
