import copy,uuid
import numpy as np
import pytest
from openew.paper3.reviewer_remediation.collection.adapters import *
from openew.paper3.reviewer_remediation.collection.durability import *
def spec():
    return StreamSpec(str(uuid.UUID(int=1)),str(uuid.UUID(int=2)),1e6,868e6,"MOCK_UTC",str(uuid.UUID(int=3)))
@pytest.mark.parametrize("seed",range(20))
def test_mock(seed):
    a=stream_digest(MockAdapter(seed,13),spec(),257);b=stream_digest(MockAdapter(seed,128),spec(),257)
    assert a==b and a["bytes"]==2056 and not a["hardware_validated"]
@pytest.mark.parametrize("ecosystem",["uhd","SoapySDR"])
def test_hardware_opt_in(ecosystem):
    with pytest.raises(PermissionError):list(DriverAdapter(ecosystem).frames(spec(),10))
@pytest.mark.parametrize("mode",["counter","reset","overflow","dtype","shape","nan","empty"])
def test_frame_reject(mode):
    values=np.ones(8,dtype="<c8");counter=0;reset=spec().clock_reset_id;overflow=False
    if mode=="counter":counter=1
    if mode=="reset":reset=str(uuid.UUID(int=4))
    if mode=="overflow":overflow=True
    if mode=="dtype":values=values.astype("complex128")
    if mode=="shape":values=values.reshape(2,4)
    if mode=="nan":values[0]=np.nan
    if mode=="empty":values=values[:0]
    with pytest.raises(ValueError):Frame(counter,values,reset,overflow).validate(spec(),0)
@pytest.mark.parametrize("fault",FAULTS)
def test_quarantine_never_promoted(fault):
    s={"phase":"WRITING","complete":0,"quarantine":0,"transitions":0};before=copy.deepcopy(s)
    q=transition(s,fault);assert s==before and q["complete"]==0
    with pytest.raises(ValueError):transition(q,"finalize")
    assert transition(q,"recover")["phase"]=="OPEN"
@pytest.mark.parametrize("seed",range(10))
def test_generated(seed):
    a=generated_stress(1000,seed);assert a==generated_stress(1000,seed)
    assert sum(a["counts"].values())==1000 and all(a["counts"][f]>0 for f in FAULTS)
def test_25000_transition_contract():
    r=generated_stress();assert r["generated_transitions"]==25000
    assert r["final_state"]["complete"]==r["counts"]["finalize"]
def test_real_posix_durability(tmp_path):
    r=durable_store_stress(tmp_path/"durable",4)
    assert r["actual_fault_transactions"]==5 and r["abrupt_subprocess_exits"]==1
    assert r["corrupt_journal_rejected"]
@pytest.mark.parametrize("phase",["CLOSED","OPEN","WRITING","QUARANTINED"])
def test_unknown_transition(phase):
    with pytest.raises(ValueError):transition({"phase":phase},"promote_partial")
