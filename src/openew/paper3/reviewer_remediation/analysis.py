"""Create-once unblinding; post-hoc receiver-level metrics, no packet inference."""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig_v2.runner import remap_bundle_to_split_targets
from openew.paper3.wisig_v2.support import freeze_support_query
from openew.paper3.wisig_v2.blinding import read_blind_predictions
from openew.paper3.wisig_v2.statistics import receiver_bootstrap, receiver_sign_flip
from .contracts import grid, key, digest, file_sha, create_once, validate_probabilities, EVIDENCE, SEEDS
from .calibration import probability_metrics, reliability, apply_temperature
from .runner import method_tree

REFERENCES = ("P0","P0_WIDE","P1","P2","P2_SHUFFLED","P2_NULL","P2_MISMATCHED_RX",
              "RX_NORM","T3A","DG_CORAL","DG_GROUPDRO","DG_DANN","SOURCE_NORM")

def clean_sha(repo):
    if subprocess.check_output(["git","status","--porcelain"],cwd=repo,text=True).strip():
        raise RuntimeError("clean committed analysis required")
    return subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip()

def freeze_execution(repo, root):
    repo, root = Path(repo), Path(root)
    sha = clean_sha(repo)
    if not (root/"frozen_before.json").exists():
        raise RuntimeError("frozen prior integrity report missing")
    integrity = json.loads((root/"frozen_before.json").read_text())
    if integrity["status"]!="PASS":
        raise RuntimeError("prior integrity failed")
    report = {"git_sha":sha, "method_tree_sha256":method_tree(repo),
              "protocol_sha256":file_sha(repo/"configs/paper3/reviewer_remediation/protocol.json"),
              "preregistration_sha256":file_sha(repo/"papers/paper3_reviewer_remediation/reviewer_remediation_preregistration.md"),
              "grid_sha256":digest(grid()),"expected_records":2400,"evidence":EVIDENCE,
              "utc":datetime.now(timezone.utc).isoformat()}
    create_once(root/"execution_freeze.json",report)
    return report

def preflight(data_root, root, repo):
    root, repo = Path(root), Path(repo)
    freeze = json.loads((root/"execution_freeze.json").read_text())
    if freeze["method_tree_sha256"] != method_tree(repo):
        raise RuntimeError("scientific implementation changed after execution freeze")
    bundle = ManyRxBundle.load(Path(data_root)/"paper3/wisig/converted/pass_a")
    splits = Path(data_root)/"paper3/wisig_v2/splits_v2_frozen"
    planned = grid()
    records = sorted((root/"experiments").glob("*/*/run.json"))
    if len(records)!=len(planned):
        raise RuntimeError(f"expected {len(planned)} records, got {len(records)}")
    manifests = {}
    expected_keys = {key(*g) for g in planned}
    found = set()
    for receiver in range(32):
        protocol = f"receiver_loso_{receiver:02d}"
        local = remap_bundle_to_split_targets(bundle,splits/protocol/"split_summary.json")
        roles = local.split_indices(splits/protocol/"split_manifest.csv")
        rx = sorted(set(map(str,local.receiver_ids[roles["test"]])))
        if len(rx)!=1:
            raise RuntimeError("receiver LOSO mismatch")
        for seed in SEEDS:
            job = root/"experiments"/f"{protocol}__s{seed}"
            source_path = job/"source_validation.json"
            source = json.loads(source_path.read_text())
            if set(source["source_receiver_ids"]) & set(rx) or source["test_receiver_used"]:
                raise RuntimeError("source validation target receiver contamination")
            for item in source["predictions"]:
                if file_sha(job/item["path"])!=item["sha256"]:
                    raise RuntimeError("source prediction changed")
            for p in sorted(job.glob("*/run.json")):
                r = json.loads(p.read_text())
                expected = key(r["protocol"],r["seed"],r["method"],r["budget"],r["scope"])
                if r["key"]!=expected or expected in found or r["status"]!="COMPLETE":
                    raise RuntimeError("incomplete/duplicate/wrong-key record")
                found.add(expected)
                if r["target_metrics"] is not None or r["query_used_for_adaptation"] or r["evidence_status"]!=EVIDENCE:
                    raise RuntimeError("blind information boundary violation")
                if r["support_labels_used"] != (r["method"]=="SUP_FT_FULL_128"):
                    raise RuntimeError("oracle label contract mismatch")
                c = r["compatibility"]
                if c["method_tree_sha256"]!=freeze["method_tree_sha256"] or c["data_sha256"]!=local.manifest_sha256:
                    raise RuntimeError("data/method mismatch")
                if c["split_sha256"]!=file_sha(splits/protocol/"split_manifest.csv"):
                    raise RuntimeError("frozen split changed")
                source_runs = Path(data_root)/"paper3/wisig_v2/experiments/confirmatory_v2/runs"
                for base in ("p0","p2"):
                    cp = source_runs/f"{protocol}__{base}__s{seed}__b128__k32__r100__raw"/"checkpoint.pt"
                    if file_sha(cp)!=c[f"{base}_checkpoint_sha256"]:
                        raise RuntimeError("source checkpoint changed")
                if file_sha(source_path)!=r["source_cache_sha256"]:
                    raise RuntimeError("source recipe cache changed")
                pred_path = p.parent/"predictions_blind.npz"
                if file_sha(pred_path)!=r["prediction_sha256"]:
                    raise RuntimeError("prediction changed")
                if r["checkpoint_sha256"] and file_sha(p.parent/"adapted.pt")!=r["checkpoint_sha256"]:
                    raise RuntimeError("adapted checkpoint changed")
                payload = read_blind_predictions(pred_path)
                if set(payload)!={"sample_ids","probabilities"}:
                    raise RuntimeError("unexpected blind field")
                validate_probabilities(payload["sample_ids"],payload["probabilities"])
                split = freeze_support_query(roles["test"],local.sample_ids,local.receiver_ids,receiver_id=rx[0],
                    support_budget=128 if r["scope"]=="primary" else 256,seed=seed)
                q = np.asarray(split.query_indices)
                s = np.asarray(split.support_indices[:r["budget"]],dtype=int)
                if not np.array_equal(payload["sample_ids"],local.sample_ids[q]):
                    raise RuntimeError("query order/identity mismatch")
                if digest(local.sample_ids[q].tolist())!=r["query_ids_sha256"] or digest(local.sample_ids[s].tolist())!=r["support_ids_sha256"]:
                    raise RuntimeError("support/query hash mismatch")
                if set(s)&set(q):
                    raise RuntimeError("support/query overlap")
                manifests[str(pred_path.relative_to(root))]=r["prediction_sha256"]
    if found!=expected_keys:
        raise RuntimeError("frozen grid mismatch")
    return {"status":"PASS","complete":len(found),"failed":0,"primary":480,"budget":1920,
            "prediction_hashes":manifests,"prediction_manifest_sha256":digest(manifests),
            "execution_freeze_sha256":file_sha(root/"execution_freeze.json"),"no_target_metric_join":True}

def paired_inference(primary):
    averaged = primary.groupby(["receiver","method"],sort=True)["macro_f1"].mean().unstack()
    if len(averaged)!=32 or averaged.isna().any().any():
        raise ValueError("receiver coverage incomplete")
    result = {}
    for method in ("SAR_GN","EMB_STD","SUP_FT_FULL_128"):
        for reference in ("P0","T3A"):
            differences = (averaged[method]-averaged[reference]).to_numpy()
            sd = differences.std(ddof=1)
            result[method+"_MINUS_"+reference] = {
                "evidence":EVIDENCE,"seed_handling":"five-seed mean within receiver","unit":"receiver",
                "positive":int((differences>0).sum()),"negative":int((differences<0).sum()),
                "median":float(np.median(differences)),
                "standardized_paired_effect":float(differences.mean()/sd) if sd else None,
                "bootstrap":receiver_bootstrap(differences,replicates=10000,seed=20260906),
                "sign_flip":receiver_sign_flip(differences,permutations=100000,seed=20260906),
                "p_value_status":"EXPLORATORY_POST_HOC_UNADJUSTED","holm_family":[]}
    return result

def analyze(data_root, root, repo, resume=False):
    root, repo, data_root = Path(root),Path(repo),Path(data_root)
    sha = clean_sha(repo)
    manifest_path = root/"unblinding_manifest.json"
    if manifest_path.exists() and not resume:
        raise FileExistsError("one unblinding event only")
    if resume and not manifest_path.exists():
        raise RuntimeError("analysis resume requires existing unblinding")
    check = preflight(data_root,root,repo)
    if not resume:
        create_once(root/"prediction_manifest.json",check)
        create_once(manifest_path,{"utc":datetime.now(timezone.utc).isoformat(),"git_sha":sha,
            "prediction_manifest_sha256":check["prediction_manifest_sha256"],"complete":2400,"evidence":EVIDENCE,
            "execution_freeze_sha256":check["execution_freeze_sha256"]})
    else:
        prior = json.loads(manifest_path.read_text())
        if prior["prediction_manifest_sha256"]!=check["prediction_manifest_sha256"]:
            raise RuntimeError("cannot resume changed prediction package")
    out = root/"analysis";out.mkdir(exist_ok=True)
    if (out/"core_analysis_manifest.json").exists():
        raise FileExistsError("analysis core already frozen")
    bundle = ManyRxBundle.load(data_root/"paper3/wisig/converted/pass_a")
    v2 = data_root/"paper3/wisig_v2"
    rows,bins,costs,temperature_rows = [],[],[],[]
    for receiver in range(32):
        protocol = f"receiver_loso_{receiver:02d}"
        local = remap_bundle_to_split_targets(bundle,v2/"splits_v2_frozen"/protocol/"split_summary.json")
        for seed in SEEDS:
            job = root/"experiments"/f"{protocol}__s{seed}"
            source = json.loads((job/"source_validation.json").read_text())
            files = []
            for method in REFERENCES:
                folder = v2/"experiments/confirmatory_v2/runs"/f"{protocol}__{method.lower()}__s{seed}__b128__k32__r100__raw"
                record = json.loads((folder/"run.json").read_text())
                pred = folder/"predictions_blind.npz"
                if file_sha(pred)!=record["target_prediction_sha256"]:
                    raise RuntimeError("frozen reference prediction changed")
                files.append((method,"primary",128,pred,None,"FROZEN_REFERENCE"))
            head = data_root/"paper3/receiver_adaptation_benchmark/runs"/f"{protocol}__sup_ft_128__s{seed}"
            hr = json.loads((head/"run.json").read_text())
            if file_sha(head/"predictions_blind.npz")!=hr["prediction_sha256"]:
                raise RuntimeError("frozen head oracle changed")
            files.append(("SUP_FT_HEAD_128","primary",128,head/"predictions_blind.npz",None,"FROZEN_ORACLE"))
            for path in sorted(job.glob("*/run.json")):
                r = json.loads(path.read_text())
                files.append((r["method"],r["scope"],r["budget"],path.parent/"predictions_blind.npz",r,EVIDENCE))
            for method,scope,budget,path,record,status in files:
                payload = read_blind_predictions(path)
                indices = np.asarray([local.sample_index[str(s)] for s in payload["sample_ids"]])
                labels = local.labels[indices]  # First new target metric join is after create-once manifest above.
                p = payload["probabilities"]
                rx = sorted(set(map(str,local.receiver_ids[indices])))
                if len(rx)!=1:
                    raise RuntimeError("prediction has multiple test receivers")
                metrics = probability_metrics(labels,p)
                identity = {"protocol":protocol,"receiver":rx[0],"seed":seed,"method":method,
                            "scope":scope,"budget":budget,"evidence":status,"prediction_sha256":file_sha(path)}
                rows.append({**identity,**metrics,"temperature":1.0,"probability_variant":"raw"})
                if scope=="primary":
                    bins.extend([{**identity,"probability_variant":"raw",**b} for b in reliability(labels,p)])
                    if method in source["temperatures"]:
                        t = source["temperatures"][method]
                        calibrated = apply_temperature(p,t["temperature"])
                        tm = probability_metrics(labels,calibrated)
                        # Positive scalar temperature must not change class decisions.
                        if not np.array_equal(p.argmax(1),calibrated.argmax(1)):
                            raise RuntimeError("temperature changed original decisions")
                        rows.append({**identity,**tm,"temperature":t["temperature"],"probability_variant":"source_temperature"})
                        bins.extend([{**identity,"probability_variant":"source_temperature",**b} for b in reliability(labels,calibrated)])
                        temperature_rows.append({"protocol":protocol,"seed":seed,"method":method,**t})
                if record:
                    costs.append({**identity,**{k:v for k,v in record["costs"].items() if not isinstance(v,(dict,list))}})
    frame = pd.DataFrame(rows)
    raw = frame[(frame.scope=="primary")&(frame.probability_variant=="raw")]
    if raw.duplicated(["receiver","method","seed"]).any() or len(raw)!=32*5*17:
        raise RuntimeError("primary receiver-method-seed grid mismatch")
    numeric = list(probability_metrics(np.array([0,1]),np.array([[.7,.3],[.4,.6]])).keys())
    if not np.isfinite(frame[numeric].to_numpy()).all():
        raise RuntimeError("nonfinite analysis")
    frame.to_csv(out/"receiver_seed_metrics.csv",index=False)
    averaged = frame.groupby(["receiver","method","scope","budget","probability_variant"],sort=True)[numeric].mean().reset_index()
    averaged.to_csv(out/"receiver_averaged_metrics.csv",index=False)
    averaged.groupby(["method","scope","budget","probability_variant"])[numeric].agg(["mean","std","median","min","max"]).to_csv(out/"summary.csv")
    pd.DataFrame(bins).to_csv(out/"reliability_bins.csv",index=False)
    pd.DataFrame(temperature_rows).to_csv(out/"source_temperatures.csv",index=False)
    pd.DataFrame(costs).to_csv(out/"compute_records.csv",index=False)
    inference = paired_inference(raw)
    create_once(out/"receiver_inference.json",inference)
    base = raw[raw.method=="P0"][["receiver","seed","macro_f1"]].rename(columns={"macro_f1":"p0"})
    deltas = raw.merge(base,on=["receiver","seed"],validate="many_to_one")
    deltas["delta"]=deltas.macro_f1-deltas.p0
    catastrophic = []
    for method,group in deltas.groupby("method"):
        means = group.groupby("receiver")["delta"].mean()
        catastrophic.append({"method":method,"receiver_seed_catastrophic":int((group.delta<-.05).sum()),
            "receiver_catastrophic":int((means<-.05).sum()),"positive_receivers":int((means>0).sum()),
            "mean_delta":float(means.mean())})
    deltas.to_csv(out/"paired_receiver_seed_deltas.csv",index=False)
    pd.DataFrame(catastrophic).to_csv(out/"catastrophic_adaptation.csv",index=False)
    create_once(out/"analysis_validation.json",{"status":"PASS","receivers":32,"seeds":5,"primary_methods":17,
        "new_primary":480,"new_budget":1920,"bootstrap":10000,"sign_flips":100000,"unit":"receiver",
        "evidence":EVIDENCE,"holm":[],"source_temperature_only":True,"query_decisions_unchanged_by_temperature":True,
        "unblinding_manifest_sha256":file_sha(manifest_path)})
    artifacts = {p.name:file_sha(p) for p in sorted(out.iterdir()) if p.is_file()}
    create_once(out/"core_analysis_manifest.json",{"files":artifacts,"git_sha":sha,"analysis_sha256":digest(artifacts)})
    return {"status":"COMPLETE","analysis_sha256":digest(artifacts),"new_evaluations":2400}
