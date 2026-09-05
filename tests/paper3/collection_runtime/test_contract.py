import copy,json
from pathlib import Path
import pytest
from openew.paper3.collection_runtime.schema import *
from openew.paper3.collection_runtime.synthetic import campaign,receiver,session,capture,stamp,uid
from openew.paper3.collection_runtime.storage import canonical

SPECS={"campaign":campaign(),"receiver":receiver(),"session":session(),
"capture":{"capture_uuid":uid("c"),"session_uuid":uid("s"),"receiver_uuid":uid("r"),"start_utc":stamp(),
"sample_counter_start":0,"sample_count":32,"sample_format":"cf32_le","source_path":"opaque.bin"},
"session_close":{"session_uuid":uid("s"),"end_utc":stamp(1),"sample_counter_end":32},
"annotation":{"capture_uuid":uid("c"),"target":"0001","annotation_source":"manual","annotation_timestamp":stamp(2)}}
REQUIRED=[(kind,key) for kind,spec in SPECS.items() for key in spec if key!="notes"]

@pytest.mark.parametrize("kind",SPECS)
def test_valid_boundary(kind): boundary(SPECS[kind],kind)

@pytest.mark.parametrize("kind,key",REQUIRED)
def test_missing_required(kind,key):
    value=copy.deepcopy(SPECS[kind]);value.pop(key)
    with pytest.raises(ValueError):boundary(value,kind)

@pytest.mark.parametrize("kind",["campaign","receiver","session","capture","session_close"])
@pytest.mark.parametrize("key",["target","transmitter_id","class","label","ood","prediction","correctness","domain_target"])
def test_forbidden_boundary(kind,key):
    with pytest.raises(ValueError):boundary({**SPECS[kind],key:"x"},kind)

@pytest.mark.parametrize("value",["","2026-01-01","2026-01-01Z","2026-01-01 00:00:00Z","2026-01-01T00:00:00","2026-01-01T00:00:00+00:00","2026-13-01T00:00:00Z","2026-01-32T00:00:00Z","2026-01-01T24:00:00Z","2026-01-01T00:00:60Z",None,123," 2026-01-01T00:00:00Z"])
def test_bad_utc(value):
    with pytest.raises((ValueError,TypeError)):utc(value)

@pytest.mark.parametrize("value",[stamp(),stamp(1),"2026-01-01T00:00:00.000001Z","2024-02-29T23:59:59Z"])
def test_good_utc(value): assert utc(value).utcoffset().total_seconds()==0

@pytest.mark.parametrize("value",["001","abc","","00000000",123,None,uid(1).upper(),"{"+uid(1)+"}"])
def test_bad_uuid(value):
    with pytest.raises((ValueError,AttributeError,TypeError)):opaque(value)

@pytest.mark.parametrize("value",[-1,0,float("nan"),float("inf"),float("-inf"),True,False,"1",None,[],{}])
def test_bad_numeric(value):
    with pytest.raises(ValueError):positive(value,"rate")

@pytest.mark.parametrize("value",[1,32,1e6,.01])
def test_positive_numeric(value):assert positive(value,"rate")==value

@pytest.mark.parametrize("value",[1.0,1.5,"1",True,-1])
def test_counter_integer(value):
    with pytest.raises(ValueError):positive(value,"counter",integer=True,zero=True)

@pytest.mark.parametrize("value",["../x","/absolute","C:\\data\\x","x/../../z","class/a","transmitter/abc","tx12.bin","jammer.bin","target-2/a","occupancy/raw","technology.raw","scenario-a.bin","label_01.bin","device/abc"])
def test_target_paths_rejected(value):
    with pytest.raises(ValueError):neutral_path(value)

@pytest.mark.parametrize("value",["raw/"+uid(1)+".sigmf-data",uid(2)+".sigmf-meta","campaign/opaque","rx001/raw","0000123"])
def test_neutral_paths(value):neutral_path(value)

def test_custom_path_vocabulary():
    with pytest.raises(ValueError):neutral_path("zigbee.bin",{"zigbee"})

@pytest.mark.parametrize("kind",SPECS)
def test_no_mutation(kind):
    value=copy.deepcopy(SPECS[kind]);before=canonical(value);boundary(value,kind);assert canonical(value)==before

def test_annotation_leading_zero():
    boundary(SPECS["annotation"],"annotation");assert SPECS["annotation"]["target"]=="0001"

def test_unicode_operator():
    value={**campaign(),"operator":"익명-001"};boundary(value,"campaign")

def test_schema_stability():
    assert SCHEMA_VERSION=="openew-collection/1.0"
    assert set(FIELDS)=={"campaign","receiver","session","capture","session_close","annotation"}
    assert not {"label","transmitter_id","prediction"} & set.union(*(FIELDS[x] for x in FIELDS if x!="annotation"))
