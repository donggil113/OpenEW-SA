import csv,json,hashlib,tempfile
from pathlib import Path
import pytest
from openew.paper3.collection_runtime.runtime import Collector
from openew.paper3.collection_runtime.storage import Store,sha256,canonical,atomic_json
from openew.paper3.collection_runtime.synthetic import *

@pytest.fixture
def work(tmp_path):
    # Incoming path itself stays target neutral even when a test name describes a leakage attack.
    with tempfile.TemporaryDirectory(prefix="openew-") as incoming:
        c=Collector(tmp_path/"campaign");c.campaign_init(campaign());c.receiver_register(receiver());c.session_open(session())
        yield c,Path(incoming)

def one(work):
    c,inc=work; row=c.capture_register(capture(inc))
    c.session_close({"session_uuid":uid("session-0"),"end_utc":stamp(4),"sample_counter_end":32})
    return c,row

def test_full_operator_cycle(work):
    c,row=one(work); assert c.validate()["status"]=="PASS"
    c.session_open(session(1,role="QUERY",seconds=5))
    c.capture_register(capture(work[1],n=1,session_n=1,seconds=6))
    c.session_close({"session_uuid":uid("session-1"),"end_utc":stamp(7),"sample_counter_end":32})
    c.freeze_day("2026-09-01");assert c.campaign_close()["closed"]
    assert not c.validate()["training_authorized"]

def test_no_annotations_required(work):c,row=one(work);assert c.validate()["status"]=="PASS"
def test_capture_hash(work):c,row=one(work);assert sha256(c.root/row["payload_path"])==row["sha256"]
def test_capture_name_opaque(work):
    c,row=one(work);assert Path(row["payload_path"]).name==row["capture_uuid"]+".sigmf-data"
def test_source_unchanged(work):
    spec=capture(work[1]);before=sha256(spec["source_path"]);work[0].capture_register(spec);assert sha256(spec["source_path"])==before
def test_path_quarantine(work):
    c,row=one(work);assert "source_path" not in row;assert len(row["source_path_sha256"])==64
def test_sigmf_separation(work):
    c,row=one(work);m=json.loads((c.root/row["metadata_path"]).read_text())
    assert m["annotations"]==[];assert "target" not in m["global"]["openew:record"]

@pytest.mark.parametrize("fault",["capture_partial","disk_full","after_payload","after_metadata"])
def test_capture_power_loss_never_promotes(work,fault):
    c,inc=work
    with pytest.raises((OSError,InterruptedError)):c.capture_register(capture(inc),failpoint=fault)
    report=c.recover();assert report["status"]=="FAIL";assert c.status()["captures"]==0
    assert any("partial" in x or "orphan" in x for x in report["issues"])

@pytest.mark.parametrize("fault",["after_journal","after_state"])
def test_capture_journal_recovery(work,fault):
    c,inc=work
    with pytest.raises(InterruptedError):c.capture_register(capture(inc),failpoint=fault)
    assert c.store.pending()
    c.recover();assert c.status()["captures"]==1;assert not c.store.pending()

@pytest.mark.parametrize("fault",["after_journal","after_state"])
def test_session_open_recovery(tmp_path,fault):
    c=Collector(tmp_path);c.campaign_init(campaign());c.receiver_register(receiver())
    with pytest.raises(InterruptedError):c.session_open(session(),failpoint=fault)
    report=c.recover();assert len(c.status()["unclosed_sessions"])==1;assert report["status"]=="FAIL"

@pytest.mark.parametrize("fault",["after_journal","after_state"])
def test_campaign_init_recovery(tmp_path,fault):
    c=Collector(tmp_path)
    with pytest.raises(InterruptedError):c.campaign_init(campaign(),failpoint=fault)
    c.recover();assert c.status()["revision"]==1

def test_freeze_partial(work):
    c,row=one(work)
    with pytest.raises(InterruptedError):c.freeze_day("2026-09-01",failpoint="freeze_partial")
    assert c.recover()["status"]=="FAIL"
    with pytest.raises((ValueError,FileExistsError)):c.freeze_day("2026-09-01")

def test_freeze_create_once(work):
    c,row=one(work);c.freeze_day("2026-09-01")
    with pytest.raises(FileExistsError):c.freeze_day("2026-09-01")
def test_frozen_day_blocks_new_sessions(work):
    c,row=one(work);c.freeze_day("2026-09-01")
    with pytest.raises(ValueError):c.session_open(session(2,seconds=20))
def test_freeze_detects_checksum(work):
    c,row=one(work);c.freeze_day("2026-09-01");(c.root/row["payload_path"]).write_bytes(b"x")
    assert c.validate()["status"]=="FAIL"
def test_corrupt_payload(work):
    c,row=one(work);(c.root/row["payload_path"]).write_bytes(b"x")
    assert any("checksum_mismatch" in x for x in c.validate()["issues"])
def test_missing_payload(work):
    c,row=one(work);(c.root/row["payload_path"]).unlink()
    assert any("missing_payload" in x for x in c.validate()["issues"])
def test_missing_metadata(work):
    c,row=one(work);(c.root/row["metadata_path"]).unlink()
    assert any("missing_metadata" in x for x in c.validate()["issues"])
def test_unknown_metadata(work):
    c,row=one(work);p=c.root/row["metadata_path"];m=json.loads(p.read_text());m["target"]="1";p.write_text(json.dumps(m))
    assert c.validate()["status"]=="FAIL"
def test_metadata_annotation_rejected(work):
    c,row=one(work);p=c.root/row["metadata_path"];m=json.loads(p.read_text());m["annotations"]=[{"label":"1"}];p.write_text(json.dumps(m))
    assert c.validate()["status"]=="FAIL"
def test_state_tamper(work):
    c,_=work;s=c.store.state();s["campaign"]["frequency_hz"]=1;c.store.path.write_text(json.dumps(s))
    with pytest.raises(RuntimeError):c.validate()
def test_journal_corruption(work):
    c,inc=work
    with pytest.raises(InterruptedError):c.capture_register(capture(inc),failpoint="after_journal")
    p=c.store.pending()[0];s=json.loads(p.read_text());s["state"]["revision"]=999;p.write_text(json.dumps(s))
    with pytest.raises(RuntimeError):c.recover()

@pytest.mark.parametrize("key,value",[
("receiver_uuid",uid("wrong")),("session_uuid",uid("wrong")),("sample_count",0),
("sample_count",33),("sample_counter_start",1),("sample_format","object"),
("start_utc",stamp(0)),("start_utc",""),("capture_uuid","target-1")])
def test_capture_errors(work,key,value):
    spec=capture(work[1]);spec[key]=value
    with pytest.raises(ValueError):work[0].capture_register(spec)

def test_duplicate_capture(work):
    c,inc=work;spec=capture(inc);c.capture_register(spec)
    with pytest.raises(ValueError):c.capture_register(spec)
def test_duplicate_source(work):
    c,inc=work;spec=capture(inc);c.capture_register(spec)
    next=capture(inc,n=1,seconds=3,counter=32);Path(next["source_path"]).write_bytes(Path(spec["source_path"]).read_bytes())
    with pytest.raises(ValueError):c.capture_register(next)
def test_source_symlink(work):
    spec=capture(work[1]);link=work[1]/(uid("link")+".bin");link.symlink_to(spec["source_path"]);spec["source_path"]=str(link)
    with pytest.raises(ValueError):work[0].capture_register(spec)
def test_source_target_filename(work):
    spec=capture(work[1]);p=work[1]/"transmitter_1.bin";p.write_bytes(Path(spec["source_path"]).read_bytes());spec["source_path"]=str(p)
    with pytest.raises(ValueError):work[0].capture_register(spec)
def test_open_session_overlap(work):
    with pytest.raises(ValueError):work[0].session_open(session(1,seconds=2))
def test_missing_receiver(work):
    with pytest.raises(ValueError):work[0].session_open(session(1,rx=2))
def test_wrong_role(work):
    with pytest.raises(ValueError):work[0].session_open(session(1,role="TARGET"))
def test_duplicate_time(work):
    c,row=one(work)
    with pytest.raises(ValueError):c.session_open(session(1,seconds=4))
def test_clock_reset_accepted(work):
    c,row=one(work);assert c.session_open(session(1,seconds=5))["sample_counter_start"]==0
def test_counter_without_reset(work):
    c,row=one(work);s=session(1,seconds=5);s["clock_reset_id"]=uid("clock-0")
    with pytest.raises(ValueError):c.session_open(s)
def test_empty_session_not_final(work):
    with pytest.raises(ValueError):work[0].session_close({"session_uuid":uid("session-0"),"end_utc":stamp(2),"sample_counter_end":0})
def test_role_pair_required(work):
    c,row=one(work)
    with pytest.raises(ValueError):c.campaign_close()
def test_campaign_cannot_overwrite(work):
    with pytest.raises(FileExistsError):work[0].campaign_init(campaign())
def test_receiver_not_approved(work):
    with pytest.raises(ValueError):work[0].receiver_register(receiver(1))

@pytest.mark.parametrize("labels,expected",[(None,"FAIL"),(["0001"],"FAIL"),(["0001","0001"],"FAIL"),(["0001","0002"],"PASS")])
def test_annotation_qa(work,labels,expected):
    c,inc=work;c.capture_register(capture(inc));c.capture_register(capture(inc,n=1,seconds=3,counter=32))
    p=inc/"annotations.csv"
    with p.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["capture_uuid","target","annotation_source","annotation_timestamp"]);w.writeheader()
        for i,label in enumerate(labels or []):w.writerow({"capture_uuid":uid(f"capture-{i}"),"target":label,"annotation_source":"manual","annotation_timestamp":stamp(10)})
    before=canonical(c.store.state());report=c.annotation_qa(p)
    assert report["status"]==expected;assert canonical(c.store.state())==before;assert not report["training_authorized"]

def test_templates(tmp_path):
    templates(tmp_path);assert len(list(tmp_path.glob("*.json")))==6
    for name in TIERS:assert json.loads((tmp_path/(name.lower()+"_campaign.json")).read_text())["synthetic"] is False

def test_synthetic_dry_cycle(tmp_path):
    report=dry_campaign(tmp_path,events=5);assert report["status"]=="PASS";assert report["hardware_validated"] is False
