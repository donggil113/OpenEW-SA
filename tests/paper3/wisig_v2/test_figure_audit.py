from __future__ import annotations

import unittest

from openew.paper3.wisig_v2.figure_audit import EXPECTED_FIGURES, parse_pdffonts


class FigureAuditTests(unittest.TestCase):
    def test_nine_expected_figures(self) -> None:
        self.assertEqual(len(EXPECTED_FIGURES), 9)

    def test_embedded_truetype_passes(self) -> None:
        output = "name type encoding emb sub uni object ID\n-----------------------------------------------\nAAAA DejaVuSans CID TrueType Identity-H yes yes yes 15 0\n"
        result = parse_pdffonts(output)
        self.assertTrue(result["all_embedded"])
        self.assertEqual(result["type3_fonts"], 0)

    def test_type3_is_counted(self) -> None:
        output = "name type encoding emb sub uni object ID\n-----------------------------------------------\nAAAA Type 3 Custom yes no no 15 0\n"
        self.assertEqual(parse_pdffonts(output)["type3_fonts"], 1)

    def test_unembedded_is_counted(self) -> None:
        output = "name type encoding emb sub uni object ID\n-----------------------------------------------\nAAAA TrueType WinAnsi no no no 15 0\n"
        result = parse_pdffonts(output)
        self.assertFalse(result["all_embedded"])
        self.assertEqual(result["unembedded_fonts"], 1)

    def test_embedded_unsubsetted_font_is_not_unembedded(self) -> None:
        output = "name type encoding emb sub uni object ID\n-----------------------------------------------\nAAAA TrueType WinAnsi yes no yes 15 0\n"
        self.assertTrue(parse_pdffonts(output)["all_embedded"])


if __name__ == "__main__":
    unittest.main()
