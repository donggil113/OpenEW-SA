"""Tests for the publication-only receiver delta figure."""
from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest


REPOSITORY = Path(__file__).resolve().parents[3]
SCRIPT = REPOSITORY / "scripts/paper3/pr90_journal_polish/render_delta_summary.py"
SPEC = importlib.util.spec_from_file_location("render_delta_summary", SCRIPT)
assert SPEC and SPEC.loader
FIGURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIGURE)


def test_fixed_source_and_provenance_order() -> None:
    rows, evidence = FIGURE.load_frozen_rows(REPOSITORY)
    assert tuple(row["method"] for row in rows) == FIGURE.FIXED_ORDER
    assert [row["origin"] for row in rows] == [
        "earlier frozen analysis",
        "earlier frozen analysis",
        "post-hoc addendum",
        "post-hoc addendum",
    ]
    assert all(row["receivers"] == 32 and row["replicates"] == 10000 for row in rows)
    assert evidence["external_v2_original_verified"] is False


def test_exact_frozen_estimates_are_not_recomputed() -> None:
    rows, _ = FIGURE.load_frozen_rows(REPOSITORY)
    actual = {row["method"]: (row["mean"], row["lower"], row["upper"]) for row in rows}
    assert actual == {
        "T3A": (
            0.028013737907748887,
            0.022010842840553903,
            0.034661295520003,
        ),
        "P2": (
            0.0010472954468500459,
            -0.006660153577247822,
            0.00885749025574811,
        ),
        "EMB-STD": (
            0.022811516470818638,
            0.01746640135077357,
            0.028405899251059415,
        ),
        "SAR-GN": (
            5.631621270527076e-06,
            -1.2680630590365671e-05,
            2.76832082433392e-05,
        ),
    }
    assert FIGURE._format_row(rows[-1]).startswith("+0.000006")


def test_p2_snapshot_change_fails_closed(tmp_path: Path) -> None:
    for relative in (
        "papers/paper3_reviewer_remediation/evidence/prior_receiver_inference.json",
        "papers/paper3_reviewer_remediation/evidence/receiver_inference.json",
        str(FIGURE.SNAPSHOT_RELATIVE),
    ):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY / relative, destination)
    path = tmp_path / FIGURE.SNAPSHOT_RELATIVE
    changed = json.loads(path.read_text())
    changed["bootstrap"]["mean_difference"] = 0.5
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="Frozen evidence hash mismatch"):
        FIGURE.load_frozen_rows(tmp_path)


def test_forest_render_is_create_once_and_does_not_sort_by_performance(tmp_path: Path) -> None:
    rows, _ = FIGURE.load_frozen_rows(REPOSITORY)
    pdf, png = tmp_path / "delta.pdf", tmp_path / "delta.png"
    FIGURE.render(rows, pdf, png)
    assert pdf.stat().st_size > 10000
    assert png.stat().st_size > 10000
    with pytest.raises(FileExistsError):
        FIGURE.render(rows, pdf, png)
    with pytest.raises(ValueError, match="prespecified source/provenance order"):
        FIGURE.render(list(reversed(rows)), tmp_path / "other.pdf", tmp_path / "other.png")


def test_snapshot_matches_frozen_external_original_when_available() -> None:
    external = Path("/mnt/d/openew_sa_data")
    origin = external / (
        "paper3/wisig_v2/analysis/confirmatory_v2/receiver_level_inference.json"
    )
    if not origin.exists():
        pytest.skip("Frozen external V2 analysis is unavailable in this environment")
    _, evidence = FIGURE.load_frozen_rows(REPOSITORY, external)
    assert evidence["external_v2_original_verified"] is True
