import numpy as np
import pytest
from openew.paper3.reviewer_remediation.calibration import (
    probability_metrics,reliability,apply_temperature,fit_source_temperature)
from openew.paper3.reviewer_remediation.contracts import validate_probabilities

@pytest.mark.parametrize("seed",range(20))
def test_metric_identities(seed):
    rng=np.random.default_rng(seed);p=rng.dirichlet(np.ones(6),size=91);y=rng.integers(0,6,91)
    m=probability_metrics(y,p)
    assert m["mean_correctness"]==m["accuracy"]
    assert m["confidence_accuracy_gap"]==pytest.approx(m["mean_confidence"]-m["accuracy"])
    assert m["nll"]==pytest.approx(-np.log(p[np.arange(len(y)),y]).mean())
    assert m["brier"]==pytest.approx(np.square(p-np.eye(6)[y]).sum(1).mean())
    assert 0<=m["ece"]<=1 and 0<=m["adaptive_ece"]<=1

@pytest.mark.parametrize("bins",[1,2,3,5,10,15,20])
@pytest.mark.parametrize("adaptive",[True,False])
def test_bin_mass_conservation(bins,adaptive):
    p=np.array([[1.,0],[0,1],[.5,.5],[.25,.75]])
    rows=reliability(np.array([0,1,0,1]),p,bins,adaptive)
    assert len(rows)==bins and sum(x["count"] for x in rows)==4
    assert sum(x["mass"] for x in rows)==1
    assert all(x["confidence"] is None for x in rows if x["count"]==0)

@pytest.mark.parametrize("boundary",range(16))
def test_ece_boundary_assignment(boundary):
    # Six-class predictions require max >=1/6; binary symmetric pair checks endpoints.
    c=.5+boundary/32
    p=np.array([[c,1-c]])
    rows=reliability(np.array([0]),p)
    assert rows[min(int(c*15),14)]["count"]==1

@pytest.mark.parametrize("temperature",[.05,.1,.5,1,2,10,20])
@pytest.mark.parametrize("seed",range(4))
def test_temperature_preserves_argmax(temperature,seed):
    p=np.random.default_rng(seed).dirichlet(np.ones(6),40)
    result=apply_temperature(p,temperature)
    assert np.array_equal(result.argmax(1),p.argmax(1))
    assert np.allclose(result.sum(1),1)

@pytest.mark.parametrize("temperature",[0,-1,np.nan,np.inf,-np.inf])
def test_bad_temperature_rejected(temperature):
    with pytest.raises(ValueError):apply_temperature(np.array([[.8,.2]]),temperature)

@pytest.mark.parametrize("role",["test","target","query","train","validation",""])
def test_target_temperature_fit_rejected(role):
    with pytest.raises(ValueError):
        fit_source_temperature(np.array([0,1]),np.array([[.8,.2],[.2,.8]]),["r1","r2"],role=role)

@pytest.mark.parametrize("p",[
    [[np.nan,.5]],[[np.inf,.5]],[[-.1,1.1]],[[.2,.2]],[[1.2,-.2]],
    [],[.4,.6],[[1]],[[.3,.7],[.4,.5]]])
def test_invalid_probabilities(p):
    with pytest.raises(ValueError):validate_probabilities(np.arange(len(p)),np.array(p))

@pytest.mark.parametrize("seed",range(5))
def test_temperature_source_objective_improves(seed):
    rng=np.random.default_rng(seed);p=rng.dirichlet(np.ones(3),90);y=rng.integers(0,3,90)
    fitted=fit_source_temperature(y,p,np.repeat(["s1","s2","s3"],30),role="source_validation")
    assert .05<=fitted["temperature"]<=20
    assert fitted["source_nll_after"]<=fitted["source_nll_before"]+1e-7
    assert not fitted["target_labels_used"]

def test_perfect_prediction_quality():
    m=probability_metrics(np.array([0,1]),np.eye(2))
    assert m["brier"]==m["nll"]==m["ece"]==m["confidence_accuracy_gap"]==0

def test_ece_does_not_determine_overconfidence():
    under=probability_metrics(np.array([0,1]),np.array([[.6,.4],[.4,.6]]))
    over=probability_metrics(np.array([1,0]),np.array([[.6,.4],[.4,.6]]))
    assert under["ece"]>0 and under["confidence_accuracy_gap"]<0
    assert over["ece"]>0 and over["confidence_accuracy_gap"]>0

def test_single_validation_receiver_rejected():
    with pytest.raises(ValueError):
        fit_source_temperature(np.array([0,1]),np.eye(2),["r","r"],role="source_validation")
