"""Checkpoint-reusing, support-only blind execution for post-hoc reviewer completeness."""
from __future__ import annotations
import json
import os
import subprocess
import time
from pathlib import Path
import numpy as np
import torch

from openew.paper3.wisig.checkpoint import atomic_json, atomic_torch_save
from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig.metrics import classification_metrics
from openew.paper3.wisig_v2.runner import (
    RunConfig, _encode_backbone, _independent_probabilities, _load_base_model,
    _to_tensor, _evaluate_condition_on_role, remap_bundle_to_split_targets, set_determinism)
from openew.paper3.wisig_v2.blinding import write_blind_predictions, read_blind_predictions
from openew.paper3.wisig_v2.support import freeze_support_query
from .contracts import SEEDS, METHODS, BUDGETS, EVIDENCE, digest, file_sha, key, output_boundary, validate_probabilities
from .methods import sar_adapt, supervised_full, ORACLE_GRID, moments, transport_embeddings
from .calibration import fit_source_temperature

def method_tree(repository):
    root = Path(repository)
    files = sorted((root/"src/openew/paper3/reviewer_remediation").glob("*.py"))
    files += sorted((root/"configs/paper3/reviewer_remediation").glob("*"))
    files += [root/"scripts/paper3/reviewer_remediation"/name for name in ("run_blind.py", "freeze_and_analyze.py")]
    return digest({str(p.relative_to(root)): file_sha(p) for p in files if p.is_file()})

def sync(device):
    if device.type == "cuda":
        torch.cuda.synchronize(device)

def load_model(root, protocol, seed, stage, classes, device):
    cfg = RunConfig(protocol, stage, seed)
    return _load_base_model(cfg, root, classes, 28, device)

def split_for(bundle, indices, receiver, seed, budget=128):
    return freeze_support_query(indices, bundle.sample_ids, bundle.receiver_ids,
                                receiver_id=receiver, seed=seed, support_budget=budget)

def predict_new(method, model, bundle, support, query, device, source_moments, recipe=None):
    """Unlabeled methods receive no label input; oracle obtains support labels explicitly."""
    support, query = np.asarray(support, dtype=int), np.asarray(query, dtype=int)
    if set(support) & set(query):
        raise ValueError("support/query overlap")
    sync(device)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    start = time.perf_counter()
    report = {"parameter_count": sum(p.numel() for p in model.parameters()), "gradient_steps": 0,
              "adapted_parameters": 0, "support_encoding_seconds": 0.0}
    adapted = None
    if method == "EMB_STD":
        enc_start = time.perf_counter()
        support_z = _encode_backbone(model, bundle, support, device, 1024)
        sync(device)
        report["support_encoding_seconds"] = time.perf_counter()-enc_start
    elif method == "SAR_GN":
        x = _to_tensor(bundle.features[support], device)
        adapted, details = sar_adapt(model, x, len(bundle.transmitter_ids))
        report.update(details)
    elif method == "SUP_FT_FULL_128":
        x = _to_tensor(bundle.features[support], device)
        # This is the only new adapter allowed to index target support annotations.
        labels = torch.as_tensor(bundle.labels[support], dtype=torch.long, device=device)
        adapted, details = supervised_full(model, x, labels, recipe)
        report.update(details)
    else:
        raise ValueError("unfrozen method")
    sync(device)
    report["adaptation_seconds"] = time.perf_counter()-start
    start = time.perf_counter()
    if method == "EMB_STD":
        query_z = _encode_backbone(model, bundle, query, device, 1024)
        transported = transport_embeddings(query_z, support_z, source_moments)
        with torch.no_grad():
            p = model.classifier(torch.from_numpy(transported).to(device)).softmax(-1).cpu().numpy()
    else:
        p = _independent_probabilities(adapted, bundle, query, device, 1024)
    sync(device)
    report["prediction_seconds"] = time.perf_counter()-start
    report["query_count"] = len(query)
    report["support_count"] = len(support)
    report["samples_per_second"] = len(query)/max(report["prediction_seconds"], 1e-12)
    report["peak_gpu_memory_bytes"] = int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else 0
    validate_probabilities(bundle.sample_ids[query], p)
    return p, report, adapted

def prepare_source(bundle, roles, model, p2, run_root, protocol, seed, device, output, compatibility):
    path = output/"source_validation.json"
    if path.exists():
        result = json.loads(path.read_text())
        if result["compatibility"] != compatibility:
            raise ValueError("source cache incompatible with frozen code/checkpoint")
        for item in result["predictions"]:
            if file_sha(output/item["path"]) != item["sha256"]:
                raise ValueError("source prediction cache corrupt")
        return result
    source_start = time.perf_counter()
    embeddings = _encode_backbone(model, bundle, roles["train"], device, 1024)
    mu, sigma = moments(embeddings)
    del embeddings
    source_time = time.perf_counter()-source_start
    val_rx = sorted(set(map(str, bundle.receiver_ids[roles["validation"]])))
    test_rx = set(map(str, bundle.receiver_ids[roles["test"]]))
    if len(val_rx) != 3 or set(val_rx) & test_rx:
        raise ValueError("source validation receiver mapping mismatch")
    validation_splits = [split_for(bundle, roles["validation"], r, seed) for r in val_rx]
    candidates = []
    for recipe in ORACLE_GRID:
        scores = []
        for split in validation_splits:
            q = np.asarray(split.query_indices)
            p, _, _ = predict_new("SUP_FT_FULL_128", model, bundle, split.support_indices,
                                  q, device, (mu,sigma), recipe)
            scores.append(classification_metrics(bundle.labels[q], p)["macro_f1"])
        candidates.append({"recipe": list(recipe), "receiver_macro_f1": scores, "mean": float(np.mean(scores))})
    selected = max(range(len(candidates)), key=lambda i: (candidates[i]["mean"], -i))
    recipe = tuple(candidates[selected]["recipe"])
    predictions, temperatures = [], {}
    frozen_t3a = json.loads((run_root/"runs"/f"{protocol}__t3a__s{seed}__b128__k32__r100__raw"/"run.json").read_text())
    filter_k = frozen_t3a["selected_t3a_filter_source_validation_only"]
    for method in ("P0","T3A","P2","SAR_GN","EMB_STD"):
        if method in ("P0","T3A","P2"):
            used = p2 if method == "P2" else model
            indices, probs, _ = _evaluate_condition_on_role(method, used, bundle, roles["validation"],
                roles["train"], device, RunConfig(protocol,method,seed), t3a_filter_k=filter_k)
        else:
            indices, parts = [], []
            for split in validation_splits:
                q = np.asarray(split.query_indices)
                p, _, _ = predict_new(method, model, bundle, split.support_indices, q, device, (mu,sigma))
                indices.extend(q); parts.append(p)
            indices, probs = np.asarray(indices), np.concatenate(parts)
        if set(indices) & set(roles["test"]):
            raise ValueError("target rows entered source temperature fitting")
        temperatures[method] = fit_source_temperature(bundle.labels[indices], probs,
            bundle.receiver_ids[indices], role="source_validation")
        dest = output/f"source_{method.lower()}.npz"
        sha = write_blind_predictions(dest, bundle.sample_ids[indices], probs)
        predictions.append({"method":method,"path":dest.name,"sha256":sha})
    result = {"compatibility":compatibility,"source_mean":mu.tolist(),"source_std":sigma.tolist(),
              "source_moment_seconds":source_time,"selected_oracle_recipe":list(recipe),
              "source_oracle_selection":candidates,"temperatures":temperatures,"predictions":predictions,
              "source_receiver_ids":val_rx,"test_receiver_used":False}
    atomic_json(result,path)
    return result

def run_job(data_root, output_root, repository, protocol, seed, bundle=None, source_only=False):
    root, out, repo = Path(data_root)/"paper3", Path(output_root), Path(repository)
    if seed not in SEEDS or protocol not in {f"receiver_loso_{i:02d}" for i in range(32)}:
        raise ValueError("unfrozen protocol/seed")
    output_boundary(out, [root/"wisig",root/"wisig_v2",root/"receiver_adaptation_benchmark",root/"v2_addendum"])
    v2 = root/"wisig_v2"; run_root = v2/"experiments/confirmatory_v2"
    split_root = v2/"splits_v2_frozen"
    split_path = split_root/protocol/"split_manifest.csv"
    tree_sha = method_tree(repo)
    model_sha = file_sha(run_root/"runs"/f"{protocol}__p0__s{seed}__b128__k32__r100__raw"/"checkpoint.pt")
    base = bundle or ManyRxBundle.load(root/"wisig/converted/pass_a")
    local = remap_bundle_to_split_targets(base,split_root/protocol/"split_summary.json")
    roles = local.split_indices(split_path)
    compatibility = {"method_tree_sha256":tree_sha, "p0_checkpoint_sha256":model_sha,
                     "split_sha256":file_sha(split_path), "data_sha256":local.manifest_sha256,
                     "p2_checkpoint_sha256":file_sha(run_root/"runs"/f"{protocol}__p2__s{seed}__b128__k32__r100__raw"/"checkpoint.pt")}
    job = out/("smoke" if source_only else "experiments")/f"{protocol}__s{seed}"
    job.mkdir(parents=True,exist_ok=True)
    set_determinism(seed)
    torch.set_num_threads(4)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model,_,_ = load_model(run_root,protocol,seed,"P0",len(local.transmitter_ids),device)
    p2,_,_ = load_model(run_root,protocol,seed,"P2",len(local.transmitter_ids),device)
    model.eval(); p2.eval()
    source = prepare_source(local,roles,model,p2,run_root,protocol,seed,device,job,compatibility)
    if source_only:
        return {"status":"SOURCE_ONLY_COMPLETE","protocol":protocol,"seed":seed,"target_predictions":0,
                "selected_oracle_recipe":source["selected_oracle_recipe"]}
    test_rx = sorted(set(map(str,local.receiver_ids[roles["test"]])))
    if len(test_rx)!=1:
        raise ValueError("LOSO test receiver mismatch")
    primary = split_for(local,roles["test"],test_rx[0],seed,128)
    maximum = split_for(local,roles["test"],test_rx[0],seed,256)
    source_moments = (np.array(source["source_mean"]),np.array(source["source_std"]))
    rows = []
    for method in METHODS:
        for scope,budgets in (("primary",(128,)),("budget",BUDGETS if method!="SUP_FT_FULL_128" else ())):
            for budget in budgets:
                condition = key(protocol,seed,method,budget,scope)
                folder = job/condition
                folder.mkdir(exist_ok=True)
                record_path = folder/"run.json"
                if record_path.exists():
                    prior = json.loads(record_path.read_text())
                    if prior["status"]=="COMPLETE":
                        if prior["compatibility"]!=compatibility or file_sha(folder/"predictions_blind.npz")!=prior["prediction_sha256"]:
                            raise ValueError("completed record incompatible/corrupt; do not overwrite")
                        rows.append(prior); continue
                    raise RuntimeError("interrupted/failed record requires documented technical recovery")
                support = np.array(primary.support_indices if scope=="primary" else maximum.support_indices[:budget],dtype=int)
                query = np.array(primary.query_indices if scope=="primary" else maximum.query_indices,dtype=int)
                record = {"status":"RUNNING","key":condition,"protocol":protocol,"receiver":test_rx[0],"seed":seed,
                    "method":method,"budget":budget,"scope":scope,"evidence_status":EVIDENCE,
                    "compatibility":compatibility,"git_sha":subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),
                    "support_ids_sha256":digest(local.sample_ids[support].tolist()),
                    "query_ids_sha256":digest(local.sample_ids[query].tolist()),"target_metrics":None,
                    "support_labels_used":method=="SUP_FT_FULL_128","query_used_for_adaptation":False,
                    "source_cache_sha256":file_sha(job/"source_validation.json")}
                atomic_json(record,record_path)
                try:
                    probs, costs, adapted = predict_new(method,model,local,support,query,device,source_moments,
                                                       tuple(source["selected_oracle_recipe"]))
                    sha = write_blind_predictions(folder/"predictions_blind.npz",local.sample_ids[query],probs)
                    checkpoint_sha = None
                    if adapted is not None:
                        atomic_torch_save({"model_state":adapted.state_dict(),"compatibility":compatibility},folder/"adapted.pt")
                        checkpoint_sha = file_sha(folder/"adapted.pt")
                    record.update(status="COMPLETE",prediction_sha256=sha,checkpoint_sha256=checkpoint_sha,costs=costs)
                    atomic_json(record,record_path)
                    rows.append(record)
                except Exception as exc:
                    record.update(status="FAILED",failure=f"{type(exc).__name__}: {exc}")
                    atomic_json(record,record_path)
                    raise
    atomic_json({"status":"COMPLETE","records":len(rows),"keys":[r["key"] for r in rows],
                 "compatibility":compatibility,"source_cache_sha256":file_sha(job/"source_validation.json")},job/"job.json")
    return {"status":"COMPLETE","protocol":protocol,"seed":seed,"records":len(rows)}
