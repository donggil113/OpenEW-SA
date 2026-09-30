from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/paper3/submission_finalization/audit_pdf_package.py"
SPEC = importlib.util.spec_from_file_location("audit_pdf_package", SCRIPT)
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_submission_text_lint_rejects_internal_artifacts():
    sample = "OpenEW-SA Internal Review; PR #90; /mnt/d/private; HUMAN_REQUIRED; draft only"
    found = audit.text_violations(sample)
    for required in ("internal review", "pull-request number", "Unix private path", "HUMAN_REQUIRED", "draft only"):
        assert required in found


def test_scientifically_necessary_posthoc_wording_is_allowed():
    assert audit.text_violations("These post-hoc comparisons are exploratory.") == []


def test_embedded_fonts_and_type_three_detection():
    header = "name type encoding emb sub uni object ID\n" + "-" * 70 + "\n"
    good = "ABC+CMR10 Type 1 Builtin yes yes yes 12 0\n"
    bad = "XYZ Type 3 Custom no no no 13 0\n"
    assert audit.font_violations(header + good) == []
    assert len(audit.font_violations(header + bad)) == 2


def test_latex_log_lint():
    assert audit.log_violations("Output written on main.pdf (9 pages).") == []
    found = audit.log_violations("Overfull \\hbox\nLaTeX Warning: Citation x undefined.\n! Error")
    assert set(found) == {"undefined reference/citation", "overfull box", "LaTeX error"}
