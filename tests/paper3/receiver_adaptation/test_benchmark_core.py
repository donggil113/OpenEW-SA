from __future__ import annotations

import numpy as np
import pytest
import torch
from torch import nn

from openew.paper3.receiver_adaptation.analysis import _extended_metrics, _manifest_hash
from openew.paper3.receiver_adaptation.budget import budget_plan, budget_run_id
from openew.paper3.receiver_adaptation.oracle import ORACLE_CANDIDATES, OracleHyperparameters, _head_probabilities, adapt_linear_classifier, oracle_run_id


@pytest.mark.parametrize("learning_rate", [1e-4, 5e-4, 1e-3])
@pytest.mark.parametrize("steps", [5, 20])
def test_oracle_grid_exact(learning_rate: float, steps: int) -> None:
    candidate = OracleHyperparameters(learning_rate, steps).validate()
    assert candidate in ORACLE_CANDIDATES


@pytest.mark.parametrize("learning_rate", [-1.0, 0.0, 1e-5, 2e-4, 1e-2, 1.0])
def test_oracle_rejects_learning_rate(learning_rate: float) -> None:
    with pytest.raises(ValueError, match="outside"):
        OracleHyperparameters(learning_rate, 5).validate()


@pytest.mark.parametrize("steps", [-1, 0, 1, 4, 6, 10, 21, 100])
def test_oracle_rejects_steps(steps: int) -> None:
    with pytest.raises(ValueError, match="outside"):
        OracleHyperparameters(1e-4, steps).validate()


@pytest.mark.parametrize("classes", [2, 3, 6, 10])
@pytest.mark.parametrize("candidate", ORACLE_CANDIDATES)
def test_classifier_adaptation_is_finite_and_copy_safe(classes: int, candidate: OracleHyperparameters) -> None:
    torch.manual_seed(829)
    classifier = nn.Linear(8, classes)
    before = {key: value.detach().clone() for key, value in classifier.state_dict().items()}
    embeddings = torch.randn(32, 8)
    labels = torch.arange(32) % classes
    adapted, losses = adapt_linear_classifier(classifier, embeddings, labels, candidate)
    assert len(losses) == candidate.steps and np.isfinite(losses).all()
    assert all(torch.equal(before[key], classifier.state_dict()[key]) for key in before)
    assert any(not torch.equal(before[key], adapted.state_dict()[key]) for key in before)


def test_classifier_adaptation_rejects_non_linear() -> None:
    with pytest.raises(TypeError, match="linear"):
        adapt_linear_classifier(nn.Sequential(nn.Linear(4, 2)), torch.ones(2, 4), torch.zeros(2, dtype=torch.long), ORACLE_CANDIDATES[0])  # type: ignore[arg-type]


@pytest.mark.parametrize("embeddings,labels,pattern", [
    (torch.ones(2, 5), torch.zeros(2, dtype=torch.long), "shape"),
    (torch.ones(2, 4), torch.zeros(3, dtype=torch.long), "align"),
    (torch.ones(0, 4), torch.zeros(0, dtype=torch.long), "requires labeled"),
    (torch.ones(2, 4), torch.tensor([-1, 0]), "outside"),
    (torch.ones(2, 4), torch.tensor([0, 2]), "outside"),
])
def test_classifier_adaptation_rejects_bad_support(embeddings, labels, pattern: str) -> None:
    with pytest.raises(ValueError, match=pattern):
        adapt_linear_classifier(nn.Linear(4, 2), embeddings, labels, ORACLE_CANDIDATES[0])


@pytest.mark.parametrize("rows", [1, 2, 31, 128, 1025])
@pytest.mark.parametrize("classes", [2, 6])
def test_head_probability_shape_and_simplex(rows: int, classes: int) -> None:
    torch.manual_seed(829)
    probabilities = _head_probabilities(nn.Linear(8, classes), torch.randn(rows, 8), batch_size=31)
    assert probabilities.shape == (rows, classes)
    assert np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-6)
    assert np.isfinite(probabilities).all()


@pytest.mark.parametrize("protocol", ["receiver_loso_00", "receiver_loso_09", "receiver_loso_31"])
@pytest.mark.parametrize("seed", [829, 1829, 2829, 3829, 4829])
def test_run_ids_are_deterministic(protocol: str, seed: int) -> None:
    assert oracle_run_id(protocol, seed) == oracle_run_id(protocol, seed)
    assert budget_run_id(protocol, seed) == budget_run_id(protocol, seed)
    assert protocol in oracle_run_id(protocol, seed)


def test_budget_plan_exact_grid() -> None:
    plan = budget_plan()
    assert len(plan) == 160 and len(set(plan)) == 160
    assert {protocol for protocol, _ in plan} == {f"receiver_loso_{index:02d}" for index in range(32)}
    assert {seed for _, seed in plan} == {829, 1829, 2829, 3829, 4829}


@pytest.mark.parametrize("classes", [2, 3, 6])
def test_extended_metrics_perfect(classes: int) -> None:
    labels = np.arange(classes, dtype=np.int64)
    probabilities = np.eye(classes, dtype=np.float32)
    metrics = _extended_metrics(labels, probabilities)
    assert metrics["macro_f1"] == pytest.approx(1.0)
    assert metrics["accuracy"] == pytest.approx(1.0)
    assert metrics["nll"] == pytest.approx(0.0)
    assert metrics["predictive_entropy"] == pytest.approx(0.0)


def test_extended_metrics_rejects_nonfinite() -> None:
    probabilities = np.asarray([[np.nan, 0.0], [0.0, 1.0]], dtype=np.float32)
    with pytest.raises((FloatingPointError, ValueError)):
        _extended_metrics(np.asarray([0, 1]), probabilities)


@pytest.mark.parametrize("count", [1, 2, 5, 16])
def test_manifest_hash_is_order_invariant(count: int) -> None:
    rows = [{"run_id": f"r{index}", "sha256": f"{index:064x}"} for index in range(count)]
    assert _manifest_hash(rows) == _manifest_hash(list(reversed(rows)))


def test_manifest_hash_changes_on_content() -> None:
    first = [{"run_id": "r", "sha256": "0" * 64}]
    second = [{"run_id": "r", "sha256": "1" * 64}]
    assert _manifest_hash(first) != _manifest_hash(second)
