import csv,json
from pathlib import Path
import pytest
from openew.paper3.collection_runtime.synthetic import campaign,receiver,session,capture,dry_campaign,uid
from openew.paper3.collection_runtime.runtime import Collector
from openew.paper3.collection_runtime.schema import boundary
from openew.paper3.collection_runtime.release import export_metadata,assess_collection,estimate_storage
from openew.paper3.collection_runtime.storage import sha256

@pytest.mark.parametrize("kind,factory",[
    ("campaign",campaign),("receiver",receiver),("session",session)])
@pytest.mark.parametrize("bad",[None,[],{},3,False])
def test_string_fields_reject_other_types(kind,factory,bad):
    spec=factory(); key={"campaign":"site_id","receiver":"model","session":"role"}[kind]; spec[key]=bad
    with pytest.raises(ValueError):boundary(spec,kind)

@pytest.mark.parametrize("bad",[None,[""],["ABC"],[4],{},"target"])
def test_vocabulary_strict(bad):
    s=campaign();s["forbidden_vocabulary"]=bad
    with pytest.raises(ValueError):boundary(s,"campaign")

def test_export_without_annotations(tmp_path):
    dry_campaign(tmp_path/"dry",events=3)
    root=tmp_path/"dry"/"campaign";before=sha256(root/"state.json")
    result=export_metadata(root,tmp_path/"export",parquet=True)
    assert result["rows"]==4 and not result["annotation_accessed"]
    assert sha256(root/"state.json")==before
    rows=list(csv.DictReader((tmp_path/"export"/"acquisition_metadata.csv").open()))
    assert not {"target","transmitter","source_path"}&rows[0].keys()
    import pandas as pd
    assert pd.read_parquet(tmp_path/"export"/"acquisition_metadata.parquet").capture_uuid.tolist()==[r["capture_uuid"] for r in rows]

def test_invalid_collection_export_rejected(tmp_path):
    c=Collector(tmp_path/"c");c.campaign_init(campaign());c.receiver_register(receiver());c.session_open(session())
    with pytest.raises(ValueError):export_metadata(c.root,tmp_path/"out")

def test_freeze_manifest_change_detected(tmp_path):
    dry_campaign(tmp_path/"dry",events=2);c=Collector(tmp_path/"dry"/"campaign")
    p=next((c.root/"freezes").glob("*.json"));v=json.loads(p.read_text());v["files"]=[]
    p.write_text(json.dumps(v))
    assert c.validate()["status"]=="FAIL"

@pytest.mark.parametrize("tier",["SMALL","MEDIUM","FULL"])
def test_dry_run_not_scientific_auth(tmp_path,tier):
    dry_campaign(tmp_path/"dry",events=2)
    result=assess_collection([tmp_path/"dry"/"campaign"],tier)
    assert result["status"]=="FAIL" and result["synthetic"] and not result["training_authorized"]
    assert "annotation_mix_qa_missing" in result["issues"]

@pytest.mark.parametrize("value",[-1,0,float("nan"),float("inf"),True,"1"])
@pytest.mark.parametrize("index",range(8))
def test_estimator_fail_closed(value,index):
    args=[8,1000,8,1,2,2,2,1];args[index]=value
    with pytest.raises(ValueError):estimate_storage(*args)

def test_storage_exact():
    r=estimate_storage(8,1000,8,1,2,2,2,1)
    assert r["raw_bytes"]==512000
    assert r["capture_receiver_seconds"]==64

def test_real_process_exit_recovery(tmp_path):
    # Process exits without exception cleanup after durable journal but before state.
    import subprocess,sys,os
    root=tmp_path/"campaign"
    code="from openew.paper3.collection_runtime.runtime import Collector\nfrom openew.paper3.collection_runtime.synthetic import campaign\nimport os\ntry: Collector("+repr(str(root))+").campaign_init(campaign(),failpoint='after_journal')\nexcept InterruptedError: os._exit(73)\n"
    result=subprocess.run([sys.executable,"-c",code],env=os.environ.copy())
    assert result.returncode==73
    audit=Collector(root).recover()
    assert audit["status"]=="PASS" and audit["actions"]==["replayed_revision_1"]
