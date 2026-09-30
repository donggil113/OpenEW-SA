import json
import numpy as np
import pandas as pd
import pytest
from openew.paper3.reviewer_remediation.contracts import (
    grid,key,SEEDS,create_once,output_boundary,digest)
from openew.paper3.reviewer_remediation.analysis import paired_inference
from openew.paper3.wisig_v2.support import freeze_support_query

def test_grid_exact_counts():
    g=grid()
    assert len(g)==len(set(g))==2400
    assert sum(x[-1]=="primary" for x in g)==480
    assert sum(x[-1]=="budget" for x in g)==1920
    assert len({x[0] for x in g})==32 and {x[1] for x in g}==set(SEEDS)

@pytest.mark.parametrize("seed",SEEDS)
def test_support_label_permutation_invariance(seed):
    ids=np.array([f"{i:032x}" for i in range(300)])
    rx=np.repeat("r",300);idx=np.arange(300)
    before=freeze_support_query(idx,ids,rx,receiver_id="r",seed=seed)
    annotations=np.random.default_rng(seed).permutation(np.arange(300)%6)
    after=freeze_support_query(idx,ids,rx,receiver_id="r",seed=seed)
    assert len(annotations)==300 and before==after
    assert not set(before.query_indices)&set(before.support_indices)

@pytest.mark.parametrize("budget",[16,32,64,128,256])
def test_nested_support_same_common_queries(budget):
    ids=np.array([f"{i:032x}" for i in range(300)]);rx=np.repeat("r",300)
    a=freeze_support_query(np.arange(300),ids,rx,receiver_id="r",support_budget=budget)
    b=freeze_support_query(np.arange(300),ids,rx,receiver_id="r",support_budget=256)
    assert a.support_indices==b.support_indices[:budget]

@pytest.mark.parametrize("bad",[
    ("receiver_loso_32",829,"SAR_GN",128,"primary"),
    ("receiver_loso_00",42,"SAR_GN",128,"primary"),
    ("receiver_loso_00",829,"P2",128,"primary"),
    ("receiver_loso_00",829,"SAR_GN",64,"primary"),
    ("receiver_loso_00",829,"SUP_FT_FULL_128",16,"budget"),
    ("receiver_loso_00",829,"SAR_GN",128,"oracle")])
def test_unplanned_condition_rejected(bad):
    with pytest.raises(ValueError):key(*bad)

def test_create_once_never_overwrites(tmp_path):
    p=tmp_path/"unblinding.json";create_once(p,{"event":1})
    with pytest.raises(FileExistsError):create_once(p,{"event":2})
    assert json.loads(p.read_text())["event"]==1

@pytest.mark.parametrize("relative",["frozen","frozen/nested","."])
def test_frozen_path_overlap(tmp_path,relative):
    frozen=tmp_path/"frozen"
    with pytest.raises(ValueError):output_boundary(tmp_path/relative,[frozen])

def test_external_new_root_allowed(tmp_path):
    assert output_boundary(tmp_path/"new",[tmp_path/"old"])==tmp_path/"new"

def test_canonical_hash_order():
    assert digest({"a":1,"b":2})==digest({"b":2,"a":1})

def test_receiver_inference_averages_seeds():
    rows=[]
    for r in range(32):
        for s in SEEDS:
            for method,mean in (("P0",.5),("T3A",.55),("SAR_GN",.53),("EMB_STD",.51),("SUP_FT_FULL_128",.6)):
                rows.append({"receiver":str(r),"seed":s,"method":method,"macro_f1":mean+(r-15)*.0001})
    result=paired_inference(pd.DataFrame(rows))
    x=result["SAR_GN_MINUS_P0"]
    assert x["bootstrap"]["receiver_count"]==32 and x["bootstrap"]["replicates"]==10000
    assert x["sign_flip"]["permutations"]==100000
    assert x["bootstrap"]["mean_difference"]==pytest.approx(.03)
    assert x["holm_family"]==[] and "POST_HOC" in x["p_value_status"]

def test_inference_missing_receiver_rejected():
    frame=pd.DataFrame([{"receiver":"r","method":m,"macro_f1":.5} for m in ("P0","T3A","SAR_GN","EMB_STD","SUP_FT_FULL_128")])
    with pytest.raises(ValueError):paired_inference(frame)
