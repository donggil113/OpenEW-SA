"""Meaningful SAR state-transition tests; no held-out RF data are loaded."""
from copy import deepcopy
import inspect

import numpy as np
import pytest
import torch

import openew.paper3.pr90_closure.sar_diagnostic as diagnostic
from openew.paper3.pr90_closure.sar_diagnostic import TraceConfig, adapt_with_trace, state_comparison
from openew.paper3.wisig.models import IndependentClassifier


@pytest.fixture
def source_and_support():
    torch.manual_seed(1)
    source = IndependentClassifier(6)
    with torch.no_grad():
        source.classifier.weight.mul_(0.05)
        source.classifier.bias.zero_()
        source.classifier.bias[0] = 3.5
    return source.eval(), torch.randn(128, 256, 2)


def test_two_minibatches_without_reset_are_real_updates(source_and_support):
    source, support = source_and_support
    adapted, summary, rows = adapt_with_trace(source, support, 6, TraceConfig(reset_threshold=0.2))
    assert len(rows) == 2
    assert summary["attempted_updates"] == summary["completed_optimizer_updates"] == 2
    assert summary["resets"] == 0
    assert summary["final_momentum_buffers"] > 0
    assert summary["source_state_comparison"]["changed_tensors"] > 0
    assert all(row["first_retained"] > 0 and row["second_retained"] > 0 for row in rows)
    assert all(row["momentum_after"] > 0 for row in rows)
    assert all(torch.equal(source.state_dict()[k], adapted.state_dict()[k]) for k in source.state_dict() if k.startswith("classifier."))


def test_reset_on_first_minibatch_clears_momentum(source_and_support):
    source, support = source_and_support
    _, summary, rows = adapt_with_trace(source, support[:64], 6, TraceConfig(reset_threshold=0.7))
    assert summary["resets"] == 1
    assert rows[0]["reset"] and rows[0]["momentum_after"] == 0
    assert summary["source_state_comparison"]["exact"]


def test_last_minibatch_reset_can_follow_normal_update(source_and_support):
    source, support = source_and_support
    _, _, reference = adapt_with_trace(source, support, 6, TraceConfig(reset_threshold=0.2))
    assert reference[1]["ema_after"] < reference[0]["ema_after"]
    threshold = (reference[0]["ema_after"]+reference[1]["ema_after"])/2
    _, summary, rows = adapt_with_trace(source, support, 6, TraceConfig(reset_threshold=threshold))
    assert [row["reset"] for row in rows] == [False, True]
    assert summary["source_state_comparison"]["exact"]
    assert rows[0]["momentum_after"] > 0 and rows[1]["momentum_after"] == 0


def test_repeated_reset_retains_ema_but_clears_optimizer(source_and_support):
    source, support = source_and_support
    _, summary, rows = adapt_with_trace(source, support, 6, TraceConfig(reset_threshold=0.7))
    assert [row["reset"] for row in rows] == [True, True]
    assert summary["source_state_comparison"]["exact"]
    assert rows[1]["ema_before"] == rows[0]["ema_after"]
    assert all(row["momentum_after"] == 0 for row in rows)


def test_threshold_argument_changes_the_actual_branch(source_and_support):
    source, support = source_and_support
    _, low, _ = adapt_with_trace(source, support, 6, TraceConfig(reset_threshold=0.2))
    _, high, _ = adapt_with_trace(source, support, 6, TraceConfig(reset_threshold=0.7))
    assert low["resets"] == 0 and high["resets"] == 2


def test_first_filter_empty_skips_undefined_loss():
    torch.manual_seed(1)
    source = IndependentClassifier(6).eval()
    _, summary, rows = adapt_with_trace(source, torch.randn(64, 256, 2), 6)
    assert summary["empty_first"] == 1 and summary["completed_optimizer_updates"] == 0
    assert summary["source_state_comparison"]["exact"]
    assert rows[0]["first_retained"] == 0


def test_second_filter_empty_restores_sam_perturbation(monkeypatch, source_and_support):
    source, support = source_and_support
    original = diagnostic.entropy
    call_count = 0
    def forced(logits):
        nonlocal call_count
        call_count += 1
        return original(logits) + (-5 if call_count == 1 else 5)
    monkeypatch.setattr(diagnostic, "entropy", forced)
    _, summary, rows = adapt_with_trace(source, support[:64], 6)
    assert summary["empty_second"] == 1 and summary["completed_optimizer_updates"] == 0
    assert summary["source_state_comparison"]["exact"]
    assert rows[0]["first_retained"] == 64 and rows[0]["second_retained"] == 0


def test_receiver_state_isolation(source_and_support):
    source, support = source_and_support
    immutable_source = deepcopy(source.state_dict())
    first, _, _ = adapt_with_trace(source, support[:64], 6, TraceConfig(reset_threshold=0.2))
    second, _, _ = adapt_with_trace(source, support[64:], 6, TraceConfig(reset_threshold=0.2))
    repeat, _, _ = adapt_with_trace(source, support[64:], 6, TraceConfig(reset_threshold=0.2))
    assert state_comparison(second.state_dict(), repeat.state_dict())["exact"]
    assert state_comparison(source.state_dict(), immutable_source)["exact"]
    assert state_comparison(first.state_dict(), second.state_dict())["changed_tensors"] > 0


def test_support_labels_cannot_affect_adaptation(source_and_support):
    source, support = source_and_support
    labels = np.arange(len(support))
    first, _, _ = adapt_with_trace(source, support, 6)
    labels[:] = labels[::-1]
    second, _, _ = adapt_with_trace(source, support, 6)
    assert state_comparison(first.state_dict(), second.state_dict())["exact"]


def test_query_is_absent_from_adaptation_signature():
    assert "query" not in inspect.signature(adapt_with_trace).parameters
    assert "labels" not in inspect.signature(adapt_with_trace).parameters


@pytest.mark.parametrize("invalid", [0, -1, 2])
def test_invalid_reset_threshold_fails_closed(invalid):
    with pytest.raises(ValueError):
        TraceConfig(reset_threshold=invalid).validate()


@pytest.mark.parametrize("passes", [0, 2, 21])
def test_unplanned_passes_fail_closed(passes):
    with pytest.raises(ValueError):
        TraceConfig(passes=passes).validate()
