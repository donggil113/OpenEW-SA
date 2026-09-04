from __future__ import annotations

import unittest

from openew.paper3.wisig_v2.hashing import canonical_json_bytes


class CanonicalJsonTests(unittest.TestCase):
    def test_finite_payload_is_canonical(self) -> None:
        self.assertEqual(canonical_json_bytes({"b": 2, "a": 1}), b'{"a":1,"b":2}\n')

    def test_nan_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonical_json_bytes({"value": float("nan")})

    def test_positive_infinity_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonical_json_bytes({"value": float("inf")})


if __name__ == "__main__":
    unittest.main()
