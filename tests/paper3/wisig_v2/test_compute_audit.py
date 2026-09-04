from __future__ import annotations

import unittest
from pathlib import Path

from openew.paper3.wisig_v2.compute_audit import backbone_forward_flops, conv1d_flops, forward_flops


class ComputeAuditTests(unittest.TestCase):
    def test_conv_multiply_add_count(self) -> None:
        self.assertEqual(conv1d_flops(10, 2, 3, 5), 600)

    def test_conv_rejects_bad_dimension(self) -> None:
        with self.assertRaises(ValueError):
            conv1d_flops(0, 2, 3, 5)

    def test_backbone_positive(self) -> None:
        self.assertGreater(backbone_forward_flops(), 1_000_000)

    def test_p0_wide_exceeds_p0(self) -> None:
        self.assertGreater(forward_flops("P0_WIDE"), forward_flops("P0"))

    def test_p2_exceeds_p1(self) -> None:
        self.assertGreater(forward_flops("P2"), forward_flops("P1"))

    def test_null_omits_peer_work(self) -> None:
        self.assertLess(forward_flops("P2_NULL"), forward_flops("P2"))

    def test_dann_exceeds_p0(self) -> None:
        self.assertGreater(forward_flops("DG_DANN"), forward_flops("P0"))

    def test_unknown_stage_rejected(self) -> None:
        with self.assertRaises(ValueError):
            forward_flops("UNKNOWN")

    def test_rx_norm_does_not_claim_support_backbone_encoding(self) -> None:
        source = Path(__file__).resolve().parents[3] / "src/openew/paper3/wisig_v2/compute_audit.py"
        text = source.read_text(encoding="utf-8")
        self.assertIn('if stage == "RX_NORM" else 0', text)
        self.assertIn('"support_statistics_ops_approx"', text)

    def test_support_backbone_packet_set_is_explicit(self) -> None:
        source = Path(__file__).resolve().parents[3] / "src/openew/paper3/wisig_v2/compute_audit.py"
        text = source.read_text(encoding="utf-8")
        self.assertIn('"P2_MISMATCHED_RX", "T3A"', text)
        self.assertNotIn("(target_support_used + donor_support_used) * backbone_forward_flops()", text)


if __name__ == "__main__":
    unittest.main()
