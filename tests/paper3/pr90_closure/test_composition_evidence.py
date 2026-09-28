"""Targeted checks for frozen composition evidence lineage and grain."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/paper3/pr90_closure"))
from build_composition_evidence import (  # noqa: E402
    ORACLES, aggregate, latex_table, verify_natural_query_archives,
    verify_pr87_sources,
)
from openew.paper3.wisig_v2.hashing import stable_digest  # noqa: E402


def rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    primary = []
    oracle = []
    for receiver, value, count in (("r0", 0.9, 100), ("r1", 0.1, 10)):
        protocol = "receiver_loso_" + receiver[-1]
        for seed in (1, 2):
            for model in ("T3A", "P2", "RX_NORM"):
                primary.append(dict(protocol_id=protocol, receiver_id=receiver,
                                    seed=seed, model=model, query_count=count,
                                    macro_f1=value))
                for condition in ORACLES:
                    oracle.append(dict(protocol_id=protocol, receiver_id=receiver,
                                       seed=seed, method=model.replace("_", "-"),
                                       condition=condition, query_count=count,
                                       evaluable_query_count=count, macro_f1=value,
                                       mean_peer_count=10,
                                       evidence_category="ORACLE_DIAGNOSTIC"))
    return pd.DataFrame(primary), pd.DataFrame(oracle)


def test_equal_receiver_not_packet_weighted():
    primary, oracle = rows()
    summary = aggregate(primary, oracle, receivers=2, seeds=(1, 2))
    natural = summary[(summary.method == "T3A") &
                      (summary.condition == "NATURAL")].iloc[0]
    assert natural.receiver_equal_macro_f1 == pytest.approx(.5)
    assert natural.query_records == 220
    assert natural.query_coverage == 1
    assert len(summary) == 12


def test_missing_receiver_seed_rejected():
    primary, oracle = rows()
    with pytest.raises(ValueError, match="incomplete"):
        aggregate(primary, oracle.iloc[1:], receivers=2, seeds=(1, 2))


def test_duplicate_key_rejected():
    primary, oracle = rows()
    with pytest.raises(ValueError, match="duplicate"):
        aggregate(primary, pd.concat([oracle, oracle.iloc[[0]]]),
                  receivers=2, seeds=(1, 2))


def test_query_coverage_loss_rejected():
    primary, oracle = rows()
    oracle.loc[0, "evaluable_query_count"] = 9
    with pytest.raises(ValueError, match="lost query coverage"):
        aggregate(primary, oracle, receivers=2, seeds=(1, 2))


def test_query_universe_count_mismatch_rejected():
    primary, oracle = rows()
    oracle.loc[0, "query_count"] = 99
    oracle.loc[0, "evaluable_query_count"] = 99
    with pytest.raises(ValueError, match="query counts"):
        aggregate(primary, oracle, receivers=2, seeds=(1, 2))


def test_oracle_category_required():
    primary, oracle = rows()
    oracle.loc[0, "evidence_category"] = "DEPLOYABLE_METHOD"
    with pytest.raises(ValueError, match="diagnostic labeling"):
        aggregate(primary, oracle, receivers=2, seeds=(1, 2))


def test_original_concatenation_verified():
    _, oracle = rows()
    p2 = oracle[oracle.method == "P2"].drop(
        columns=["method", "evidence_category"])
    tta = oracle[oracle.method != "P2"]
    verify_pr87_sources(oracle, p2, tta)
    bad = oracle.copy()
    bad.loc[0, "macro_f1"] = 0
    with pytest.raises(ValueError, match="macro_f1"):
        verify_pr87_sources(bad, p2, tta)


def test_latex_records_unevaluated_methods_and_coverage():
    primary, oracle = rows()
    rendered = latex_table(aggregate(primary, oracle, receivers=2, seeds=(1, 2)))
    assert "EMB-STD and SAR-GN: NOT EVALUATED" in rendered
    assert "100\\%" in rendered
    assert "Same-class excluded" in rendered
    assert "128 bank; $\\leq32$ selected" in rendered


def test_natural_archive_query_id_audit(tmp_path):
    split_root = tmp_path / "splits"
    run_root = tmp_path / "runs"
    protocol = "receiver_loso_0"
    split = split_root / protocol
    split.mkdir(parents=True)
    sample_ids = [f"{i:032d}" for i in range(132)]
    with (split / "split_manifest.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["sample_id", "split"])
        writer.writeheader()
        writer.writerows({"sample_id": value, "split": "test"}
                         for value in sample_ids)
    expected = sorted(sample_ids, key=lambda value: stable_digest(
        1, "r0", value, namespace="wisig-v2-support"))[128:]
    for name in ("p2", "t3a", "rx_norm"):
        path = run_root / "runs" / f"{protocol}__{name}__s1__b128__k32__r100__raw"
        path.mkdir(parents=True)
        np.savez_compressed(path / "predictions_blind.npz",
                            sample_ids=np.asarray(expected))
    primary = pd.DataFrame([dict(protocol_id=protocol, receiver_id="r0",
                                 seed=1, model="P2", query_count=4)])
    audit = verify_natural_query_archives(primary, split_root, run_root,
                                          receivers=1, seeds=(1,))
    assert audit["natural_prediction_archives_exact_query_match"] == 3
    assert audit["protocol_seed_query_sets"] == 1
    path = run_root / "runs" / f"{protocol}__t3a__s1__b128__k32__r100__raw"
    np.savez_compressed(path / "predictions_blind.npz",
                        sample_ids=np.asarray(expected[::-1]))
    with pytest.raises(ValueError, match="query IDs differ"):
        verify_natural_query_archives(primary, split_root, run_root,
                                      receivers=1, seeds=(1,))
