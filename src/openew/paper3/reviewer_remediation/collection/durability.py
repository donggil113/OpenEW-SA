"""Deterministic fault-transition model plus actual POSIX durable-store exercises."""
from collections import Counter
import copy, hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from openew.paper3.collection_runtime.storage import Store,atomic_json,read_json,canonical

FAULTS=("partial_capture","disk_full","clock_reset","corrupt_journal","duplicate_uuid",
        "metadata_payload_mismatch","checksum_failure","abrupt_termination")
def transition(state,event):
    """Fail-closed reference state machine, not a physical SDR simulation."""
    result=copy.deepcopy(state)
    if event=="open":
        if result["phase"]!="CLOSED": raise ValueError("session already active")
        result["phase"]="OPEN"
    elif event=="begin":
        if result["phase"]!="OPEN": raise ValueError("capture requires open session")
        result["phase"]="WRITING"
    elif event=="finalize":
        if result["phase"]!="WRITING": raise ValueError("nothing to finalize")
        result["phase"]="OPEN";result["complete"]+=1
    elif event=="close":
        if result["phase"]!="OPEN": raise ValueError("unresolved capture")
        result["phase"]="CLOSED"
    elif event in FAULTS:
        if result["phase"]!="WRITING": raise ValueError("fault requires capture transaction")
        result["phase"]="QUARANTINED";result["quarantine"]+=1
    elif event=="recover":
        if result["phase"]!="QUARANTINED": raise ValueError("no recovery evidence")
        result["phase"]="OPEN"
    else: raise ValueError("unknown event")
    result["transitions"]+=1
    return result

def generated_stress(cases=25000,seed=20260906):
    if cases<1: raise ValueError("positive transition count")
    rng=np.random.default_rng(seed);state={"phase":"CLOSED","complete":0,"quarantine":0,"transitions":0}
    counts=Counter();trace=hashlib.sha256()
    for _ in range(cases):
        phase=state["phase"]
        if phase=="CLOSED":event="open"
        elif phase=="OPEN":event="close" if rng.random()<.05 else "begin"
        elif phase=="QUARANTINED":event="recover"
        else:event="finalize" if rng.random()<.55 else FAULTS[int(rng.integers(len(FAULTS)))]
        before=copy.deepcopy(state);state=transition(state,event);counts[event]+=1
        assert state["complete"]==before["complete"]+int(event=="finalize")
        if event in FAULTS: assert state["phase"]=="QUARANTINED" and state["complete"]==before["complete"]
        trace.update(canonical({"event":event,"state":state}))
    return {"label":"SYNTHETIC_STATE_TRANSITIONS_NOT_HARDWARE","generated_transitions":cases,
            "counts":dict(counts),"final_state":state,"trace_sha256":trace.hexdigest(),"hardware_validated":False}

def durable_store_stress(root,rounds=24):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    outcomes=[]
    for index in range(rounds):
        case=root/f"case_{index:03d}";store=Store(case)
        store.commit({"revision":0,"captures":[],"synthetic":True},"init")
        mode=("after_journal","after_state","disk_full","process_exit")[index%4]
        if mode=="process_exit":
            code="""import os,sys
from openew.paper3.collection_runtime.storage import Store
s=Store(sys.argv[1])
try:s.commit(s.state(),'abrupt',failpoint='after_journal')
except InterruptedError:os._exit(73)
"""
            result=subprocess.run([sys.executable,"-c",code,str(case)],check=False)
            assert result.returncode==73
        else:
            try: store.commit(store.state(),"fault",failpoint=mode)
            except (InterruptedError,OSError): pass
            else: raise AssertionError("fault did not fire")
        assert store.pending()
        actions=store.recover_transactions()
        assert store.state()["revision"]==2 and not store.pending()
        outcomes.append({"mode":mode,"recovered":True,"actions":actions})
    # Actual corrupt journal must stop, preserving evidence and prior state.
    corrupt=Store(root/"corrupt")
    corrupt.commit({"revision":0,"captures":[]},"init")
    try:corrupt.commit(corrupt.state(),"fault",failpoint="after_journal")
    except InterruptedError:pass
    event=corrupt.pending()[0]; envelope=read_json(event);envelope["state"]["captures"]=["tampered"]
    # Fault injection is intentionally an in-place corruption of a synthetic journal only.
    event.write_bytes(canonical(envelope))
    try:corrupt.recover_transactions()
    except RuntimeError:pass
    else:raise AssertionError("corrupt journal accepted")
    assert corrupt.state()["revision"]==1 and event.exists()
    return {"label":"SYNTHETIC_POSIX_DURABILITY","actual_fault_transactions":rounds+1,
            "abrupt_subprocess_exits":rounds//4,"corrupt_journal_rejected":True,
            "outcomes":outcomes,"hardware_validated":False}
