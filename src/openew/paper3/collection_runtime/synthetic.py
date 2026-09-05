"""SYNTHETIC operator workflow fixtures. Not RF evidence or hardware validation."""
from datetime import datetime,timedelta,timezone
import hashlib, uuid
from pathlib import Path
from .runtime import Collector
from .schema import SCHEMA_VERSION
from .storage import atomic_json

def uid(n): return str(uuid.uuid5(uuid.NAMESPACE_URL,f"openew-synthetic-collection/{n}"))
def stamp(seconds=0): return (datetime(2026,9,1,tzinfo=timezone.utc)+timedelta(seconds=seconds)).isoformat().replace("+00:00","Z")

def campaign(receivers=1):
    return {"campaign_uuid":uid("campaign"),"site_id":"site-001","start_utc":stamp(),
        "operator":"operator-pseudonym","schema_version":SCHEMA_VERSION,
        "approved_receivers":[uid(f"rx-{i}") for i in range(receivers)],"frequency_hz":2462000000,
        "sample_rate_hz":1000,"task":"closed_set_identification","annotation_policy":"SEPARATE","synthetic":True}

def receiver(i=0):
    return {"receiver_uuid":uid(f"rx-{i}"),"manufacturer":"MOCK","model":f"family-{i%4}",
        "serial_hash":hashlib.sha256(f"synthetic-{i}".encode()).hexdigest(),"firmware":"mock-1",
        "driver":"external-sdr-adapter","antenna":"antenna-001","host":"host-001","clock_source":"SYNTHETIC_UTC","notes":""}

def session(n=0,rx=0,role="CALIBRATION",seconds=1):
    return {"session_uuid":uid(f"session-{n}"),"receiver_uuid":uid(f"rx-{rx}"),
        "campaign_uuid":uid("campaign"),"role":role,"start_utc":stamp(seconds),
        "clock_reset_id":uid(f"clock-{n}"),"sample_counter_start":0}

def capture(incoming,n=0,session_n=0,rx=0,seconds=2,counter=0):
    incoming=Path(incoming); incoming.mkdir(parents=True,exist_ok=True)
    path=incoming/(uid(f"capture-{n}")+".bin")
    if not path.exists(): path.write_bytes(hashlib.sha256(f"synthetic-payload-{n}".encode()).digest()*8)
    return {"capture_uuid":uid(f"capture-{n}"),"session_uuid":uid(f"session-{session_n}"),
        "receiver_uuid":uid(f"rx-{rx}"),"start_utc":stamp(seconds),"sample_counter_start":counter,
        "sample_count":32,"sample_format":"cf32_le","source_path":str(path)}

TIERS={"SMALL":(8,3,2,1),"MEDIUM":(12,3,2,2),"FULL":(20,4,3,2)}
def templates(out):
    out=Path(out)
    for name,(receivers,families,sites,days) in TIERS.items():
        value=campaign(receivers); value["synthetic"]=False
        # An unfilled template is not an initialized or authorized collection.
        atomic_json(out/(name.lower()+"_campaign.json"),value)
        atomic_json(out/(name.lower()+"_requirements.json"),{"tier":name,"receivers":receivers,
            "minimum_hardware_families":families,"sites":sites,"days":days,
            "roles_per_receiver":["CALIBRATION","QUERY"],"status":"TEMPLATE_NOT_COLLECTED"})
    return TIERS

def dry_campaign(root,*,events=1000):
    root=Path(root); c=Collector(root/"campaign"); c.campaign_init(campaign())
    c.receiver_register(receiver()); c.session_open(session())
    for n in range(events):
        c.capture_register(capture(root/"incoming",n=n,seconds=2+n,counter=n*32))
    c.session_close({"session_uuid":uid("session-0"),"end_utc":stamp(events+3),"sample_counter_end":events*32})
    c.session_open(session(1,role="QUERY",seconds=events+5))
    c.capture_register(capture(root/"incoming",n=events,session_n=1,seconds=events+6))
    c.session_close({"session_uuid":uid("session-1"),"end_utc":stamp(events+7),"sample_counter_end":32})
    audit=c.validate(); c.freeze_day("2026-09-01"); c.campaign_close()
    return {**c.validate(),"events":c.status()["revision"],"hardware_validated":False,"synthetic":True}
