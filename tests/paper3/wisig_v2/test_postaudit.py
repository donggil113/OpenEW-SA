from __future__ import annotations

import unittest

import pandas as pd

from openew.paper3.wisig_v2.postaudit import correlation_diagnostic


class PostAuditTests(unittest.TestCase):
    def test_finite_correlation_is_reported(self) -> None:
        result = correlation_diagnostic(pd.DataFrame({"x": [1, 2, 3], "y": [2, 4, 6]}), "x", "y")
        self.assertTrue(result["defined"])
        self.assertAlmostEqual(result["pearson"], 1.0)

    def test_constant_variable_is_null_not_nan(self) -> None:
        result = correlation_diagnostic(pd.DataFrame({"x": [1, 1, 1], "y": [1, 2, 3]}), "x", "y")
        self.assertFalse(result["defined"])
        self.assertIsNone(result["pearson"])
        self.assertIsNone(result["spearman"])
        self.assertEqual(result["reason"], "constant_variable")

    def test_too_few_rows_are_explicit(self) -> None:
        result = correlation_diagnostic(pd.DataFrame({"x": [1, 2], "y": [2, 3]}), "x", "y")
        self.assertEqual(result["reason"], "fewer_than_three_complete_rows")

    def test_missing_rows_are_excluded(self) -> None:
        result = correlation_diagnostic(pd.DataFrame({"x": [1, None, 2], "y": [2, 3, 4]}), "x", "y")
        self.assertFalse(result["defined"])
        self.assertEqual(result["row_count"], 2)


if __name__ == "__main__":
    unittest.main()
