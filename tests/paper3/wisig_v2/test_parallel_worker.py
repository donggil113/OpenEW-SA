from __future__ import annotations

import unittest
from pathlib import Path

from openew.paper3.wisig_v2.parallel import receiver_worker_plan


class ParallelWorkerTests(unittest.TestCase):
    def test_one_receiver_has_all_65_frozen_conditions(self) -> None:
        plan = receiver_worker_plan([31])
        self.assertEqual(len(plan), 65)
        self.assertEqual({config.protocol_id for config in plan}, {"receiver_loso_31"})
        self.assertTrue(all(config.blind_target_metrics for config in plan))

    def test_receiver_order_is_preserved(self) -> None:
        plan = receiver_worker_plan([31, 30])
        self.assertTrue(all(config.protocol_id == "receiver_loso_31" for config in plan[:65]))
        self.assertTrue(all(config.protocol_id == "receiver_loso_30" for config in plan[65:]))

    def test_invalid_receiver_plan_fails_closed(self) -> None:
        for receivers in ([], [0, 0], [-1], [32]):
            with self.assertRaises(ValueError):
                receiver_worker_plan(receivers)

    def test_frozen_high_worker_has_780_conditions(self) -> None:
        self.assertEqual(len(receiver_worker_plan(list(range(31, 19, -1)))), 780)

    def test_worker_does_not_write_global_suite_status(self) -> None:
        repository = Path(__file__).resolve().parents[3]
        source = (repository / "scripts/paper3/wisig_v2/run_primary_worker.py").read_text(encoding="utf-8")
        self.assertNotIn('"suite_status.json"', source)
        self.assertIn('f"{args.worker_name}_status.json"', source)


if __name__ == "__main__":
    unittest.main()
