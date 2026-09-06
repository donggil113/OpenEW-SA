from copy import deepcopy
import inspect
import numpy as np
import pytest
import torch
from torch import nn
from openew.paper3.wisig.models import IndependentClassifier
from openew.paper3.reviewer_remediation.methods import (
    sar_adapt,supervised_full,moments,transport_embeddings,norm_parameters,ORACLE_GRID)

torch.set_num_threads(2)

@pytest.mark.parametrize("seed",range(8))
def test_sar_preserves_source_and_only_updates_gn(seed):
    torch.manual_seed(seed);model=IndependentClassifier(6).eval()
    before=deepcopy(model.state_dict())
    adapted,report=sar_adapt(model,torch.randn(32,256,2),6)
    allowed={n for n,_ in norm_parameters(model)}
    for name,value in model.state_dict().items():assert torch.equal(value,before[name])
    for name,value in adapted.state_dict().items():
        if name not in allowed:assert torch.equal(value,before[name])
    assert all(not p.requires_grad for p in adapted.parameters())
    assert report["sam_backward_passes"]<=2

@pytest.mark.parametrize("n",[0,1,16,32,64,128,256])
def test_sar_zero_and_bounded_steps(n):
    model=IndependentClassifier(6).eval();adapted,report=sar_adapt(model,torch.randn(n,256,2),6)
    assert report["gradient_steps"]<=(n+63)//64
    if n==0:
        for k,v in model.state_dict().items():assert torch.equal(v,adapted.state_dict()[k])

def test_sar_no_gn_rejected():
    with pytest.raises(ValueError):sar_adapt(nn.Sequential(nn.Flatten(),nn.Linear(512,6)),torch.randn(2,256,2),6)

def test_deployable_signatures_do_not_accept_labels_or_queries():
    assert "labels" not in inspect.signature(sar_adapt).parameters
    assert "query" not in inspect.signature(sar_adapt).parameters
    assert "labels" not in inspect.signature(transport_embeddings).parameters

@pytest.mark.parametrize("seed",range(10))
def test_moment_transport_recovers_source_coordinates(seed):
    rng=np.random.default_rng(seed);source=rng.normal(size=(100,64))
    offset=rng.normal(size=64);scale=rng.uniform(.1,4,64)
    target=source*scale+offset
    result=transport_embeddings(target,target,moments(source))
    assert np.allclose(result,source,atol=2e-6)

@pytest.mark.parametrize("dimension",[1,2,6,16,32,64,128])
def test_constant_embedding_std_finite(dimension):
    a=np.ones((16,dimension))
    z=transport_embeddings(a,a,moments(a))
    assert np.isfinite(z).all() and np.allclose(z,a)

@pytest.mark.parametrize("seed",range(5))
def test_zero_support_is_identity(seed):
    z=np.random.default_rng(seed).normal(size=(12,64)).astype(np.float32)
    assert np.array_equal(z,transport_embeddings(z,np.empty((0,64)),moments(z)))

@pytest.mark.parametrize("recipe",ORACLE_GRID)
def test_full_oracle_parameter_scope_and_source_immutable(recipe):
    model=IndependentClassifier(6).eval();before=deepcopy(model.state_dict())
    adapted,report=supervised_full(model,torch.randn(12,256,2),torch.arange(12)%6,recipe)
    assert report["adapted_parameters"]==64774
    assert report["gradient_steps"]==recipe[1]
    assert report["oracle"]
    assert any(not torch.equal(adapted.state_dict()[k],v) for k,v in before.items() if "backbone" in k)
    assert all(torch.equal(model.state_dict()[k],v) for k,v in before.items())

@pytest.mark.parametrize("recipe",[(1e-3,20),(1e-4,50),(0,0),(.1,5)])
def test_unfrozen_recipe_rejected(recipe):
    with pytest.raises(ValueError):supervised_full(IndependentClassifier(6),torch.randn(2,256,2),torch.tensor([0,1]),recipe)

@pytest.mark.parametrize("bad",[np.nan,np.inf,-np.inf])
def test_nonfinite_moments_rejected(bad):
    with pytest.raises(ValueError):moments([[bad,1]])

def test_wrong_target_embedding_dimension():
    with pytest.raises(ValueError):transport_embeddings(np.ones((4,3)),np.ones((4,2)),moments(np.ones((4,2))))
