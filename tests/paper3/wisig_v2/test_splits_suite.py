from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

from openew.paper3.wisig.data import ManyRxBundle
from openew.paper3.wisig_v2.runner import remap_bundle_to_split_targets

from openew.paper3.wisig_v2.splits import _balanced_receiver_groups, load_hardware_map, select_validation_receivers
from openew.paper3.wisig_v2.suite import (
    PRIMARY_MODELS,
    context_k_plan,
    day_secondary_plan,
    deduplicate_plan,
    plan_summary,
    primary_loso_plan,
    support_budget_plan,
    is_fatal_failure,
)


REPOSITORY = Path(__file__).resolve().parents[3]


class SplitSuiteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.hardware = {"a": "A", "b": "B", "c": "C", "d": "A", "e": "B", "f": "C"}

    def test_validation_count(self) -> None:
        result = select_validation_receivers(list(self.hardware), "a", self.hardware)
        self.assertEqual(len(result), 3)

    def test_validation_excludes_test(self) -> None:
        self.assertNotIn("a", select_validation_receivers(list(self.hardware), "a", self.hardware))

    def test_validation_covers_hardware(self) -> None:
        result = select_validation_receivers(list(self.hardware), "a", self.hardware)
        self.assertEqual({self.hardware[value] for value in result}, {"A", "B", "C"})

    def test_validation_deterministic(self) -> None:
        left = select_validation_receivers(list(self.hardware), "a", self.hardware)
        right = select_validation_receivers(list(reversed(self.hardware)), "a", self.hardware)
        self.assertEqual(left, right)

    def test_not_enough_receivers_rejected(self) -> None:
        with self.assertRaises(ValueError):
            select_validation_receivers(["a", "b"], "a", {"a": "A", "b": "B"})

    def test_hardware_config_has_32_receivers(self) -> None:
        mapping = load_hardware_map(REPOSITORY / "configs/paper3/wisig_v2/receiver_hardware_v1.json")
        self.assertEqual(len(mapping), 32)

    def test_hardware_config_families(self) -> None:
        mapping = load_hardware_map(REPOSITORY / "configs/paper3/wisig_v2/receiver_hardware_v1.json")
        self.assertEqual(set(mapping.values()), {"B210", "N210", "X310"})

    def test_primary_plan_count(self) -> None:
        self.assertEqual(len(primary_loso_plan()), 32 * len(PRIMARY_MODELS) * 5)

    def test_day_plan_count(self) -> None:
        self.assertEqual(len(day_secondary_plan()), 4 * len(PRIMARY_MODELS) * 5)

    def test_support_plan_count(self) -> None:
        self.assertEqual(len(support_budget_plan()), 32 * 5 * 5)

    def test_context_k_plan_count(self) -> None:
        self.assertEqual(len(context_k_plan()), 32 * 4 * 5)

    def test_all_primary_blinded(self) -> None:
        self.assertTrue(all(config.blind_target_metrics for _, config in primary_loso_plan()))

    def test_all_primary_five_seeds(self) -> None:
        self.assertEqual({config.seed for _, config in primary_loso_plan()}, {829, 1829, 2829, 3829, 4829})

    def test_primary_support_128(self) -> None:
        self.assertEqual({config.support_budget for _, config in primary_loso_plan()}, {128})

    def test_primary_k_32(self) -> None:
        self.assertEqual({config.context_k for _, config in primary_loso_plan()}, {32})

    def test_support_16_uses_k16(self) -> None:
        values = [config.context_k for _, config in support_budget_plan() if config.support_budget == 16]
        self.assertEqual(set(values), {16})

    def test_dedup_reuses_primary_p2(self) -> None:
        rows = primary_loso_plan() + support_budget_plan() + context_k_plan()
        self.assertLess(len(deduplicate_plan(rows)), len(rows))

    def test_plan_summary_primary_unit(self) -> None:
        self.assertTrue(plan_summary()["receiver_is_primary_evaluation_unit"])

    def test_preregistration_has_no_dynamic_claim(self) -> None:
        text = (REPOSITORY / "papers/paper3_wisig_methods_remediation/methods_remediation_preregistration_v2.md").read_text(encoding="utf-8").lower()
        self.assertIn("no dynamic", text)

    def test_information_matrix_denies_labels(self) -> None:
        text = (REPOSITORY / "papers/paper3_wisig_methods_remediation/information_budget_matrix.md").read_text(encoding="utf-8")
        self.assertNotIn("| Yes | Yes | Yes |", text)

    def test_runner_exposes_explicit_blind_flag(self) -> None:
        text = (REPOSITORY / "scripts/paper3/wisig_v2/run_v2_suite.py").read_text(encoding="utf-8")
        self.assertIn("--blind-target-metrics", text)

    def test_full_execution_requires_an_explicit_phase(self) -> None:
        from openew.paper3.wisig_v2.suite import execute_suite

        with self.assertRaisesRegex(ValueError, "explicit phase"):
            execute_suite(".", ".", ".", ".", phases=None, smoke=False)

    def test_sensitivities_cannot_retrain_p2(self) -> None:
        from openew.paper3.wisig_v2.suite import execute_suite

        for phase in ({"support_budget"}, {"context_k"}):
            with self.assertRaisesRegex(ValueError, "reuse primary P2 checkpoints"):
                execute_suite(".", ".", ".", ".", phases=phase, smoke=False)

    def test_grouped_secondary_has_four_equal_folds(self) -> None:
        import pandas as pd
        receivers = tuple(f"rx{index:02d}" for index in range(32))
        frame = pd.DataFrame({"receiver_id": list(receivers) * 2, "transmitter_id": ["a"] * 32 + ["b"] * 32})
        hardware = {receiver: ("A", "B", "C")[index % 3] for index, receiver in enumerate(receivers)}
        folds = _balanced_receiver_groups(frame, receivers, hardware, repeat=0)
        self.assertEqual([len(fold) for fold in folds], [8, 8, 8, 8])

    def test_grouped_secondary_covers_each_receiver_once(self) -> None:
        import pandas as pd
        receivers = tuple(f"rx{index:02d}" for index in range(32))
        frame = pd.DataFrame({"receiver_id": receivers, "transmitter_id": ["a"] * 32})
        hardware = {receiver: "A" for receiver in receivers}
        values = [value for fold in _balanced_receiver_groups(frame, receivers, hardware, repeat=1) for value in fold]
        self.assertEqual(sorted(values), list(receivers)); self.assertEqual(len(values), len(set(values)))

    def test_grouped_secondary_is_deterministic(self) -> None:
        import pandas as pd
        receivers = tuple(f"rx{index:02d}" for index in range(32))
        frame = pd.DataFrame({"receiver_id": receivers, "transmitter_id": ["a"] * 32})
        hardware = {receiver: "A" for receiver in receivers}
        self.assertEqual(_balanced_receiver_groups(frame, receivers, hardware, 2), _balanced_receiver_groups(frame, receivers, hardware, 2))

    def test_grouped_secondary_protocol_is_declared_secondary(self) -> None:
        text = (REPOSITORY / "papers/paper3_wisig_methods_remediation/grouped_receiver_secondary_protocol.md").read_text(encoding="utf-8")
        self.assertIn("secondary", text.lower()); self.assertIn("180", text)

    def test_grouped_runner_requires_blind_flag(self) -> None:
        text = (REPOSITORY / "scripts/paper3/wisig_v2/run_grouped_secondary.py").read_text(encoding="utf-8")
        self.assertIn("--blind-target-metrics", text); self.assertNotIn("held_out_metrics", text)

    def test_integrity_failures_abort_suites(self) -> None:
        for message in ("split mismatch", "target metrics exposed", "annotation leak", "non-finite output"):
            self.assertTrue(is_fatal_failure(message))
        self.assertFalse(is_fatal_failure("CUDA out of memory"))

    def test_split_target_remap_is_contiguous(self) -> None:
        bundle = ManyRxBundle(
            features=np.zeros((4, 2, 2), dtype=np.float32),
            sample_ids=np.asarray(["a", "b", "c", "d"]),
            receiver_ids=np.asarray(["r"] * 4),
            day_ids=np.asarray(["d"] * 4),
            labels=np.asarray([0, 1, 2, 1]),
            transmitter_ids=("t0", "t1", "t2"),
            sample_index={"a": 0, "b": 1, "c": 2, "d": 3},
            manifest_sha256="x",
        )
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "summary.json"
            path.write_text(json.dumps({"eligible_transmitter_ids": ["t1", "t2"]}), encoding="utf-8")
            remapped = remap_bundle_to_split_targets(bundle, path)
        self.assertEqual(remapped.transmitter_ids, ("t1", "t2"))
        self.assertEqual(remapped.labels.tolist(), [-1, 0, 1, 0])

    def test_split_target_remap_unknown_rejected(self) -> None:
        bundle = ManyRxBundle(np.zeros((1, 2, 2), dtype=np.float32), np.asarray(["a"]), np.asarray(["r"]), np.asarray(["d"]), np.asarray([0]), ("t0",), {"a": 0}, "x")
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "summary.json"
            path.write_text(json.dumps({"eligible_transmitter_ids": ["missing"]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                remap_bundle_to_split_targets(bundle, path)


if __name__ == "__main__":
    unittest.main()
