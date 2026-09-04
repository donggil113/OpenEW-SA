from __future__ import annotations

import unittest

from openew.paper3.wisig_v2.inference_benchmark import select_benchmark_records
from openew.paper3.wisig_v2.suite import PRIMARY_MODELS


def records() -> list[dict[str, object]]:
    return [
        {
            "protocol_id": f"receiver_loso_{receiver:02d}",
            "model_stage": model,
            "status": "COMPLETE",
            "config": {"seed": seed},
        }
        for receiver in range(32)
        for model in PRIMARY_MODELS
        for seed in (829, 1829)
    ]


class InferenceBenchmarkTests(unittest.TestCase):
    def test_selects_one_frozen_seed_for_all_receivers_and_models(self) -> None:
        selected = select_benchmark_records(records())
        self.assertEqual(len(selected), 32 * len(PRIMARY_MODELS))
        self.assertEqual({int(row["config"]["seed"]) for row in selected}, {829})

    def test_rejects_missing_receiver_model_condition(self) -> None:
        values = records()
        values.pop(0)
        with self.assertRaisesRegex(RuntimeError, "requires"):
            select_benchmark_records(values)

    def test_rejects_incomplete_condition(self) -> None:
        values = records()
        values[0]["status"] = "FAILED"
        with self.assertRaisesRegex(RuntimeError, "complete"):
            select_benchmark_records(values)


if __name__ == "__main__":
    unittest.main()
