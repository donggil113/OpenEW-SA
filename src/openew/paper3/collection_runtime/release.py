"""Metadata-only exports and collection readiness; never authorizes training."""
import csv,io,json,time
from pathlib import Path
from .runtime import Collector
from .storage import atomic_bytes,atomic_json,sha256
from .synthetic import TIERS

def export_metadata(root,out,*,parquet=False):
    c=Collector(root); audit=c.validate()
    if audit["status"]!="PASS": raise ValueError("invalid collection")
    state=c._state(); out=Path(out); out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for cap,row in sorted(state["captures"].items()):
        session=state["sessions"][row["session_uuid"]]
        rows.append({key:row[key] for key in ("capture_uuid","session_uuid","receiver_uuid","session_role","start_utc","end_utc","sample_count","sample_counter_start","sample_format","sha256")})
        rows[-1].update(campaign_uuid=state["campaign"]["campaign_uuid"],site_id=state["campaign"]["site_id"],
            sample_rate_hz=state["campaign"]["sample_rate_hz"],center_frequency_hz=state["campaign"]["frequency_hz"],
            clock_reset_id=session["clock_reset_id"],synthetic=state["campaign"]["synthetic"])
    if not rows: raise ValueError("no complete records")
    text=io.StringIO(newline=""); writer=csv.DictWriter(text,fieldnames=list(rows[0]),lineterminator="\n")
    writer.writeheader(); writer.writerows(rows); start=time.perf_counter()
    atomic_bytes(out/"acquisition_metadata.csv",text.getvalue().encode("utf-8"))
    csv_seconds=time.perf_counter()-start
    parquet_seconds=None
    if parquet:
        import pandas as pd
        start=time.perf_counter(); data=pd.DataFrame(rows).to_parquet(index=False)
        atomic_bytes(out/"acquisition_metadata.parquet",data); parquet_seconds=time.perf_counter()-start
    report={"status":"PASS","rows":len(rows),"annotation_accessed":False,"synthetic":state["campaign"]["synthetic"],
        "csv_seconds":csv_seconds,"parquet_seconds":parquet_seconds,"training_authorized":False,
        "files":[{"path":p.name,"sha256":sha256(p)} for p in sorted(out.iterdir())]}
    atomic_json(out/"export_manifest.json",report)
    return report

def assess_collection(roots,tier,annotation_files=None):
    if tier not in TIERS: raise ValueError("unknown collection tier")
    expected_rx,expected_family,expected_sites,expected_days=TIERS[tier]
    issues=[]; receivers={}; sites=set(); days=set(); roles={}; captures=set(); hashes=set(); synthetic=[]
    for root in roots:
        c=Collector(root); audit=c.validate(); s=c._state()
        if audit["status"]!="PASS": issues.append("collection_integrity")
        if not s["closed"]: issues.append("campaign_not_closed")
        synthetic.append(s["campaign"]["synthetic"]); sites.add(s["campaign"]["site_id"])
        for rx,row in s["receivers"].items():
            identity=(row["manufacturer"],row["model"],row["serial_hash"])
            if rx in receivers and receivers[rx]!=identity: issues.append("receiver_identity_conflict")
            receivers[rx]=identity
        for row in s["sessions"].values(): roles.setdefault(row["receiver_uuid"],set()).add(row["role"])
        for cap,row in s["captures"].items():
            if cap in captures or row["sha256"] in hashes: issues.append("duplicate_source_record")
            captures.add(cap); hashes.add(row["sha256"]); days.add(row["start_utc"][:10])
        annotation=(annotation_files or {}).get(str(Path(root)))
        if not annotation: issues.append("annotation_mix_qa_missing")
        elif c.annotation_qa(annotation)["status"]!="PASS": issues.append("annotation_mix_qa_failed")
    if len(set(v[2] for v in receivers.values()))!=len(receivers): issues.append("serial_alias_receiver")
    families={(v[0],v[1]) for v in receivers.values()}
    for name,actual,required in [("receivers",len(receivers),expected_rx),("hardware_families",len(families),expected_family),
        ("sites",len(sites),expected_sites),("days",len(days),expected_days)]:
        if actual<required: issues.append("insufficient_"+name)
    if any(roles.get(rx,set())!={"CALIBRATION","QUERY"} for rx in receivers): issues.append("physical_roles_missing")
    return {"status":"PASS" if not issues else "FAIL","tier":tier,"issues":sorted(set(issues)),
        "receivers":len(receivers),"hardware_families":len(families),"sites":len(sites),"days":len(days),
        "synthetic":any(synthetic),"hardware_validated":False,"training_authorized":False,
        "interpretation":"Metadata QA only. Physical identity, acquired episodes, licence and frozen scientific gates require review."}

def estimate_storage(receivers,sample_rate,sample_bytes,seconds,captures_per_session,sessions_per_receiver,sites,days):
    values=(receivers,sample_rate,sample_bytes,seconds,captures_per_session,sessions_per_receiver,sites,days)
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or v<=0 for v in values): raise ValueError("positive finite inputs required")
    import math
    if not all(math.isfinite(v) for v in values): raise ValueError("nonfinite")
    captures=receivers*captures_per_session*sessions_per_receiver*sites*days
    raw=captures*seconds*sample_rate*sample_bytes
    # Example feature reserve: each nonoverlapping 256-IQ window stored in float32 IQ.
    derived=captures*math.ceil(seconds*sample_rate/256)*256*8
    return {"raw_bytes":raw,"converted_float32_iq_bytes":derived,"capture_receiver_seconds":captures*seconds,
        "parallel_all_receivers_seconds_lower_bound":captures*seconds/receivers,
        "recommended_disk_bytes":1.25*(2*raw+2*derived),"checkpoint_reserve_not_included":True,
        "note":"Uncompressed conservative two-copy raw and two-pass conversion; no scientific sample-size claim."}
