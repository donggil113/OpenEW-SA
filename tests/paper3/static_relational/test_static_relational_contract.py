from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

from openew.paper3.relational_audit import read_metadata_preserve_strings, validate_relation_fields
from openew.paper3.static_relational.checkpoint import atomic_write_json, compatible_completed_run
from openew.paper3.static_relational.graph import build_context_batch, build_relation_plan
from openew.paper3.static_relational.hypergraph import to_torch_context
from openew.paper3.static_relational.metrics import require_finite_probabilities
from openew.paper3.static_relational.models import NonFiniteModelOutput, build_classifier
from openew.paper3.static_relational.relation_contract import (
    LeakageContractViolation,
    SplitContaminationError,
    validate_partition_membership,
    validate_relation_types,
)
from openew.paper3.static_relational.runner import plan_full_suite


def _jamshield_frame(size: int = 12) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sample_id": [f"sample_{index:04d}" for index in range(size)],
            "rx_id": [f"station_{index % 3}" for index in range(size)],
            "abnormal_event_label": ["normal" if index % 2 else "abnormal_interference" for index in range(size)],
        }
    )


def _electrosense_frame(size: int = 12) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sample_id": [f"es_{index:04d}" for index in range(size)],
            "rx_id": [f"receiver_{index % 3}" for index in range(size)],
            "source_date_id": [f"date_{index % 2}" for index in range(size)],
            "frequency_band": [f"forbidden_{index % 2}" for index in range(size)],
            "situation_label": ["fm" if index % 2 else "lte" for index in range(size)],
        }
    )


class RelationContractTests(unittest.TestCase):
    def test_01_forbidden_relation_type_is_rejected(self) -> None:
        with self.assertRaises(LeakageContractViolation):
            validate_relation_types("jamshield", ["scenario"])

    def test_02_domain_id_cannot_be_a_model_relation(self) -> None:
        with self.assertRaises(ValueError):
            validate_relation_fields("jamshield", ["domain_id"], ["domain_id"])

    def test_03_target_ood_correctness_and_prediction_fields_are_rejected(self) -> None:
        for field in ("abnormal_event_label", "ood_label", "prediction_correct", "predicted_label"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_relation_fields("jamshield", [field], [field])

    def test_04_relation_group_cannot_cross_split_boundaries(self) -> None:
        with self.assertRaises(SplitContaminationError):
            validate_partition_membership({"station": np.asarray([0, 0, 1])}, np.asarray(["train", "test", "train"]))

    def test_05_electrosense_frequency_relation_is_forbidden(self) -> None:
        with self.assertRaises(ValueError):
            validate_relation_fields("electrosense", ["frequency_band"], ["frequency_band"])

    def test_06_deepsense_relation_request_is_rejected(self) -> None:
        with self.assertRaises(LeakageContractViolation):
            validate_relation_types("deepsense", ["receiver"])

    def test_07_unseen_receiver_needs_no_categorical_embedding(self) -> None:
        model = build_classifier("electrosense", "m2", ("receiver",), 4, 3, 8, 0.0)
        self.assertFalse(any(isinstance(module, nn.Embedding) for module in model.modules()))
        frame = pd.DataFrame({"sample_id": ["a", "b"], "rx_id": ["never_seen", "never_seen"], "source_date_id": ["d", "d"]})
        plan = build_relation_plan(frame, "electrosense", "heldout", ("receiver",), 829, 64)
        context = build_context_batch(plan, np.asarray([0, 1]))
        logits = model(torch.ones((2, 4)), to_torch_context(context, torch.device("cpu")))
        self.assertEqual(tuple(logits.shape), (2, 3))

    def test_08_symbolic_identifiers_retain_leading_zeros(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.csv"
            path.write_text("sample_id,occupancy_label\na,0000\nb,0010\n", encoding="utf-8")
            frame = read_metadata_preserve_strings(path)
            self.assertEqual(frame["occupancy_label"].tolist(), ["0000", "0010"])

    def test_09_relation_construction_is_deterministic_for_seed(self) -> None:
        frame = _jamshield_frame(30)
        left = build_relation_plan(frame, "jamshield", "train", ("station",), 829, 4)
        right = build_relation_plan(frame, "jamshield", "train", ("station",), 829, 4)
        np.testing.assert_array_equal(left.group_ids_by_type["station"], right.group_ids_by_type["station"])

    def test_10_changing_labels_does_not_change_relation_incidence(self) -> None:
        frame = _jamshield_frame(30)
        changed = frame.copy()
        changed["abnormal_event_label"] = list(reversed(changed["abnormal_event_label"].tolist()))
        left = build_relation_plan(frame, "jamshield", "train", ("station",), 829, 4)
        right = build_relation_plan(changed, "jamshield", "train", ("station",), 829, 4)
        np.testing.assert_array_equal(left.group_ids_by_type["station"], right.group_ids_by_type["station"])

    def test_11_relation_corruption_mask_is_label_independent(self) -> None:
        frame = _electrosense_frame(40)
        changed = frame.copy()
        changed["situation_label"] = "different"
        left = build_relation_plan(frame, "electrosense", "train", ("receiver", "date"), 1829, 8, retention=0.5)
        right = build_relation_plan(changed, "electrosense", "train", ("receiver", "date"), 1829, 8, retention=0.5)
        for relation_type in left.relation_types:
            np.testing.assert_array_equal(left.group_ids_by_type[relation_type], right.group_ids_by_type[relation_type])

    def test_12_zero_retention_preserves_nodes_features_and_m0_output(self) -> None:
        frame = _jamshield_frame(8)
        plan = build_relation_plan(frame, "jamshield", "test", ("station",), 829, 64, retention=0.0)
        self.assertEqual(plan.n_nodes, len(frame))
        features = torch.arange(32, dtype=torch.float32).reshape(8, 4)
        anchors = np.arange(8, dtype=np.int64)
        context = build_context_batch(plan, anchors)
        torch.manual_seed(829)
        m0 = build_classifier("jamshield", "m0", (), 4, 2, 8, 0.0)
        torch.manual_seed(829)
        m2 = build_classifier("jamshield", "m2", ("station",), 4, 2, 8, 0.0)
        m0.eval()
        m2.eval()
        np.testing.assert_allclose(
            m0(features).detach().numpy(),
            m2(features, to_torch_context(context, torch.device("cpu"))).detach().numpy(),
            rtol=0,
            atol=0,
        )

    def test_13_relation_audit_does_not_mutate_source_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.csv"
            frame = _jamshield_frame(12)
            frame.to_csv(path, index=False)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            build_relation_plan(frame, "jamshield", "train", ("station",), 829, 4)
            after = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(before, after)

    def test_14_large_groups_use_linear_not_quadratic_storage(self) -> None:
        frame = pd.DataFrame({"sample_id": [f"n{index}" for index in range(10000)], "rx_id": ["one_station"] * 10000})
        plan = build_relation_plan(frame, "jamshield", "train", ("station",), 829, 64)
        self.assertLessEqual(plan.storage_items, 2 * len(frame))
        self.assertEqual(max(len(group) for group in plan.members_by_type["station"].values()), 64)

    def test_15_isolated_nodes_are_finite(self) -> None:
        frame = _jamshield_frame(5)
        plan = build_relation_plan(frame, "jamshield", "test", ("station",), 829, 64, retention=0.0)
        context = build_context_batch(plan, np.arange(5))
        model = build_classifier("jamshield", "m2", ("station",), 4, 2, 8, 0.0)
        logits = model(torch.ones((5, 4)), to_torch_context(context, torch.device("cpu")))
        self.assertTrue(torch.isfinite(logits).all())

    def test_16_nonfinite_probabilities_and_logits_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            require_finite_probabilities(np.asarray([[np.nan, np.nan]]))
        model = build_classifier("jamshield", "m0", (), 4, 2, 8, 0.0)
        with self.assertRaises(NonFiniteModelOutput):
            model(torch.full((1, 4), float("nan")))

    def test_17_completed_run_resume_returns_identical_metadata(self) -> None:
        signature = {
            "config_hash": "c",
            "source_hash": "s",
            "artifact_hashes": {"a": "h"},
            "split_hashes": {"split": "h"},
        }
        payload = signature | {"status": "COMPLETED", "run_id": "r", "metric": 0.25}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.json"
            atomic_write_json(path, payload)
            self.assertEqual(compatible_completed_run(path, signature), payload)

    def test_18_shuffling_preserves_typewise_group_size_multiset(self) -> None:
        frame = _electrosense_frame(60)
        actual = build_relation_plan(frame, "electrosense", "test", ("receiver", "date"), 829, 64)
        shuffled = build_relation_plan(frame, "electrosense", "test", ("receiver", "date"), 829, 64, shuffled=True)
        for relation_type in actual.relation_types:
            actual_sizes = sorted(len(group) for group in actual.members_by_type[relation_type].values())
            shuffled_sizes = sorted(len(group) for group in shuffled.members_by_type[relation_type].values())
            self.assertEqual(actual_sizes, shuffled_sizes)

    def test_19_full_suite_plan_has_140_deduplicated_runs(self) -> None:
        config = {"seeds": [829, 1829, 2829, 3829, 4829], "retention_levels": [1.0, 0.75, 0.5, 0.25, 0.0]}
        specs = plan_full_suite(config)
        self.assertEqual(len(specs), 140)
        self.assertEqual(len({item.scientific_key() for item in specs}), 140)


if __name__ == "__main__":
    unittest.main()
