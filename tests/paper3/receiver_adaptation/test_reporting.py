from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from openew.paper3.receiver_adaptation.reporting import (
    _calibration_metrics,
    analysis_manifest,
    receiver_difficulty,
    summarize_catastrophic,
    summarize_hardware,
    summarize_receiver_results,
    summarize_support_budgets,
)


def _averaged() -> pd.DataFrame:
    rows = []
    for receiver, family, p0 in (("01", "A", .6), ("02", "A", .7), ("03", "B", .8)):
        for model, delta in (("P0", 0), ("T3A", .1), ("P2", .02), ("RX_NORM", -.01), ("SUP_FT_128", .12)):
            rows.append({"model": model, "receiver_id": receiver, "hardware_family": family, "macro_f1": p0 + delta, "accuracy": p0, "balanced_accuracy": p0, "ece": .1})
    return pd.DataFrame(rows)


def test_receiver_summary_uses_receiver_rows():
    result = summarize_receiver_results(_averaged())
    row = result[(result.model == "T3A") & (result.metric == "macro_f1")].iloc[0]
    assert row.receiver_count == 3
    assert row["mean"] == pytest.approx(.8)


def test_receiver_summary_rejects_bad_schema():
    with pytest.raises(ValueError, match="missing result"):
        summarize_receiver_results(pd.DataFrame({"model": ["P0"]}))


def test_hardware_summary_is_descriptive():
    result = summarize_hardware(_averaged())
    row = result[(result.model == "T3A") & (result.hardware_family == "A")].iloc[0]
    assert row.receiver_count == 2
    assert row.delta_from_p0 == pytest.approx(.1)


def test_receiver_difficulty_has_expected_deltas():
    detail, correlations = receiver_difficulty(_averaged())
    assert np.allclose(detail.t3a_minus_p0, .1)
    assert len(correlations) == 4
    assert correlations.diagnostic_only.all()


def test_catastrophic_summary_respects_frozen_boolean():
    source = pd.DataFrame({"model": ["A", "A"], "receiver_id": ["1", "2"], "seed": [1, 1], "delta_from_p0": [-.06, .01], "catastrophic": [True, False]})
    result = summarize_catastrophic(source).iloc[0]
    assert result.catastrophic_count == 1
    assert result.catastrophic_fraction == .5
    assert result.threshold == -.05


def test_catastrophic_summary_rejects_bad_schema():
    with pytest.raises(ValueError, match="wrong schema"):
        summarize_catastrophic(pd.DataFrame({"model": ["A"]}))


def test_budget_summary_averages_seed_inside_receiver():
    source = pd.DataFrame({"method": ["A"] * 4, "support_budget": [16] * 4, "receiver_id": ["1", "1", "2", "2"], "macro_f1": [.5, .7, .7, .9], "ece": [.1] * 4})
    result = summarize_support_budgets(source).iloc[0]
    assert result.receiver_count == 2
    assert result.macro_f1_mean == pytest.approx(.7)


@pytest.mark.parametrize("probabilities, expected", [
    (np.asarray([[.8, .2], [.1, .9]]), -np.log([.8, .9]).mean()),
    (np.asarray([[1., 0.], [0., 1.]]), 0.),
])
def test_calibration_metrics(probabilities, expected):
    nll, entropy = _calibration_metrics(np.asarray([0, 1]), probabilities)
    assert nll == pytest.approx(expected)
    assert np.isfinite(entropy)


def test_calibration_metrics_rejects_nonfinite():
    with pytest.raises(FloatingPointError):
        _calibration_metrics(np.asarray([0]), np.asarray([[np.nan, np.nan]]))


def test_analysis_manifest_is_deterministic(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    first = analysis_manifest(tmp_path)
    second = analysis_manifest(tmp_path)
    assert first == second
    assert first["file_count"] == 1


def test_analysis_manifest_excludes_itself(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "analysis_manifest.json").write_text(json.dumps({"old": True}))
    result = analysis_manifest(tmp_path)
    assert result["file_count"] == 1
    assert result["files"][0]["path"] == "a.txt"


def test_analysis_manifest_detects_content_change(tmp_path):
    target = tmp_path / "a.txt"
    target.write_text("a")
    first = analysis_manifest(tmp_path)["manifest_sha256"]
    target.write_text("b")
    assert analysis_manifest(tmp_path)["manifest_sha256"] != first
