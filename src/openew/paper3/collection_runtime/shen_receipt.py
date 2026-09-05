"""Lawful receipt and deterministic bounded conversion; no training or download."""
from pathlib import Path
import csv, hashlib,json
import numpy as np
import h5py
from openew.paper3.receiver_adaptation.shen_adapter import (
    EXPECTED_KEYS,FROZEN_TRANSFER_RULE,inspect_shen_hdf5,reconstruct_complex,transfer_crops,
    opaque_sample_id,receiver_hardware)
from .storage import sha256,atomic_json

def inspect_receipt(path,receiver_id,chunk=512):
    path=Path(path)
    if path.is_symlink() or chunk<1: raise ValueError("unsafe source or chunk")
    digest=sha256(path)
    with h5py.File(path,"r") as h:
        if set(h)!=EXPECTED_KEYS: raise ValueError("unknown HDF5 schema")
        for key in EXPECTED_KEYS:
            if not isinstance(h.get(key,getlink=True),h5py.HardLink) or not isinstance(h[key],h5py.Dataset):
                raise ValueError("external/soft link or group forbidden")
            if h[key].is_virtual or h[key].external: raise ValueError("external/virtual storage forbidden")
    schema=inspect_shen_hdf5(path,receiver_id)
    if schema.row_count==0: raise ValueError("empty payload")
    targets=set()
    with h5py.File(path,"r") as h:
        for start in range(0,schema.row_count,chunk):
            end=min(start+chunk,schema.row_count)
            # Official side fields permit [N] or [N,1], never ambiguous arbitrary reshape.
            for name in ("label","SNR","CFO"):
                if h[name].shape not in ((schema.row_count,),(schema.row_count,1)): raise ValueError("unsupported side-field shape")
                values=np.asarray(h[name][start:end]).reshape(-1)
                if not np.isfinite(values).all(): raise ValueError("nonfinite side field")
                if name=="label":
                    if not np.equal(values,np.floor(values)).all(): raise ValueError("fractional transmitter label")
                    targets.update(str(int(x)) for x in values)
            transfer_crops(reconstruct_complex(np.asarray(h["data"][start:end])),FROZEN_TRANSFER_RULE)
    if sha256(path)!=digest: raise ValueError("source changed during inspection")
    return {"schema":schema.to_dict(),"source_sha256":digest,"bytes":path.stat().st_size,
            "receiver_id":receiver_id,"hardware_family":receiver_hardware(receiver_id),
            "transmitter_ids":sorted(targets),"transmitter_count":len(targets),"status":"PASS",
            "target_metrics_computed":False,"transfer_rule":FROZEN_TRANSFER_RULE}

def convert_receipt(path,receiver_id,out,*,chunk=512,synthetic=False):
    receipt=inspect_receipt(path,receiver_id,chunk)
    out=Path(out); out.mkdir(parents=True,exist_ok=False)
    with (out/"acquisition_metadata.csv").open("w",newline="") as acq,(out/"annotations.csv").open("w",newline="") as ann,h5py.File(path,"r") as h:
        aw=csv.writer(acq,lineterminator="\n"); lw=csv.writer(ann,lineterminator="\n")
        aw.writerow(["sample_id","receiver_id","hardware_family","source_record_index","sample_rate_hz","center_frequency_hz"])
        lw.writerow(["sample_id","task_name","transmitter_id"])
        for shard,start in enumerate(range(0,receipt["schema"]["row_count"],chunk)):
            end=min(start+chunk,receipt["schema"]["row_count"])
            crop=transfer_crops(reconstruct_complex(np.asarray(h["data"][start:end])),FROZEN_TRANSFER_RULE)
            x=np.stack([crop.real,crop.imag],axis=-1).astype("<f4")
            np.save(out/f"features_{shard:05d}.npy",x,allow_pickle=False)
            labels=np.asarray(h["label"][start:end]).reshape(-1)
            for offset,index in enumerate(range(start,end)):
                sid=opaque_sample_id(receipt["source_sha256"],receiver_id,index)
                aw.writerow([sid,receiver_id,receiver_hardware(receiver_id),index,1000000,868100000])
                lw.writerow([sid,"transmitter_identification",str(int(labels[offset]))])
    # Paths and timestamps excluded from deterministic manifests; provenance remains explicit.
    atomic_json(out/"provenance.json",{"source_sha256":receipt["source_sha256"],"parser_version":"collection-runtime/1.0",
        "transfer_rule":FROZEN_TRANSFER_RULE,"synthetic":synthetic,
        "field_sources":{"receiver_id":"operator-supplied official receiver map; verify before real use",
                        "transmitter_id":"HDF5 label, annotation only","features":"data real-half/imag-half; centered 256",
                        "SNR_CFO":"audit-only; not model input"},
        "warnings":["No acquired-calibration claim","Transfer rule frozen before payload; scientific suitability unresolved"]})
    atomic_json(out/"manifest.json",{"files":[{"path":p.name,"sha256":sha256(p)} for p in sorted(out.iterdir())],
                                   "synthetic":synthetic,"source_sha256":receipt["source_sha256"]})
    return out

def qualify(spec,receipt):
    """Gate consumes explicit human licence attestation and bound QA reports, not model scores."""
    allowed={"synthetic","source_url","source_version","license_review","license_evidence_path","license_evidence_sha256",
        "lawful_local_processing_authorized","receipt_sha256","qa_reports","method_sha256","split_sha256","preregistration_sha256"}
    if set(spec)-allowed: raise ValueError("unknown qualification field")
    reasons=[]
    if spec.get("synthetic") is not False: reasons.append("SYNTHETIC_OR_UNKNOWN")
    evidence=Path(spec.get("license_evidence_path",""))
    legal=(spec.get("license_review")=="APPROVED_LOCAL_RESEARCH" and spec.get("lawful_local_processing_authorized") is True
           and evidence.is_file() and sha256(evidence)==spec.get("license_evidence_sha256"))
    if not legal: reasons.append("LICENSE_GATE_BLOCKED")
    if not spec.get("source_url","").startswith("https://") or not spec.get("source_version"): reasons.append("PROVENANCE_BLOCKED")
    if receipt.get("status")!="PASS" or spec.get("receipt_sha256")!=receipt.get("source_sha256"): reasons.append("RECEIPT_NOT_BOUND")
    conversion=not reasons
    reports=spec.get("qa_reports",{})
    required=("two_pass","proxy","class_support","receiver_support","split_integrity","method_hash")
    def bound(name):
        p=Path(reports.get(name,""))
        if not p.is_file(): return False
        value=json.loads(p.read_text())
        return (value.get("status")=="PASS" and value.get("data_sha256")==receipt.get("source_sha256")
            and value.get("method_sha256")==spec.get("method_sha256") and value.get("split_sha256")==spec.get("split_sha256"))
    import re
    hashes=all(re.fullmatch("[0-9a-f]{64}",spec.get(key,"")) for key in ("method_sha256","split_sha256","preregistration_sha256"))
    smoke=conversion and hashes and all(bound(name) for name in required)
    benchmark=smoke and all(bound(name) for name in ("source_smoke","analysis_code_freeze","blinding"))
    return {"AUTHORIZED_FOR_CONVERSION":conversion,"AUTHORIZED_FOR_SOURCE_SMOKE":smoke,
            "AUTHORIZED_FOR_BLIND_BENCHMARK":benchmark,"reasons":reasons,
            "gate_type":"evidence attestation; not legal advice or physical hardware verification",
            "training_launched":False}
