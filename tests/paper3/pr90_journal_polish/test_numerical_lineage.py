"""Focused failures for the PR90 journal-only numerical lineage guard."""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/paper3/pr90_journal_polish/check_numerical_lineage.py"
SPEC = importlib.util.spec_from_file_location("pr90_numerical_lineage", SCRIPT)
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)

SUMMARY = Path(
    "/mnt/d/openew_sa_data/paper3/pr90_closure/20260928T110826Z/"
    "composition/composition_receiver_equal_summary.csv"
)


def sample_summary():
    rows = []
    for method in guard.METHODS:
        for condition in guard.CONDITIONS.values():
            rows.append({
                "method": method,
                "condition": condition,
                "receiver_count": "32",
                "seed_count": "5",
                "query_records": "738015",
                "evaluable_query_records": "738015",
                "query_coverage": "1.0",
                "receiver_equal_macro_f1": {
                    "T3A": "0.8336922428107418",
                    "P2": "0.8067258003498431",
                    "RX-NORM": "0.8007688420666816",
                }[method],
            })
    return rows


def write_summary(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def compact_table():
    return r"""
\begin{tabular}{lrrrc}
Condition & T3A & P2 & RX-NORM & Label-dependent\\
Natural & 0.8337 & 0.8067 & 0.8008 & No\\
Same-class excluded & 0.8337 & 0.8067 & 0.8008 & Yes\\
Same-class only & 0.8337 & 0.8067 & 0.8008 & Yes\\
Transmitter pure & 0.8337 & 0.8067 & 0.8008 & Yes\\
\multicolumn{5}{l}{EMB-STD and SAR-GN: NOT EVALUATED}\\
\end{tabular}
"""


def test_macro_parser_detects_duplicate():
    text = r"\expandafter\def\csname vP0macro_f1raw\endcsname{0.805679}"
    assert guard.macros(text) == {"vP0macro_f1raw": "0.805679"}
    with pytest.raises(ValueError, match="duplicate"):
        guard.macros(text + "\n" + text)


def tabular(body):
    return "\\midrule\n" + body + "\\bottomrule\n"


def test_table_number_inventory_ignores_footnote_and_markup():
    before = tabular(
        "P0 & 0.8057 & 0.8188 \\\\\nSAR-GN & 0.8057 & 0.8188 \\\\\n"
    )
    after = tabular(
        "P0 & 0.8057 & 0.8188 \\\\\n"
        "SAR-GN$^\\\\dagger$ & 0.8057 & 0.8188 \\\\\n"
        "\\\\multicolumn{3}{l}{293/320 resets}\\\n"
    )
    assert guard.table_numbers(before) == guard.table_numbers(after)
    assert guard.table_numbers(before) == Counter({"0.8057": 2, "0.8188": 2})
    assert guard.table_numeric_rows(before) == guard.table_numeric_rows(after)


def test_table_changed_result_detectable():
    old = guard.table_numbers(tabular("P0 & 0.8057 & 0.8188 \\\\\n"))
    new = guard.table_numbers(tabular("P0 & 0.8157 & 0.8188 \\\\\n"))
    assert old - new == Counter({"0.8057": 1})
    assert new - old == Counter({"0.8157": 1})


def test_row_reassociation_detectable_even_when_multiset_equal():
    old = tabular("P0 & 0.8057 \\\\\nT3A & 0.8337 \\\\\n")
    swapped = tabular("P0 & 0.8337 \\\\\nT3A & 0.8057 \\\\\n")
    assert guard.table_numbers(old) == guard.table_numbers(swapped)
    assert guard.table_numeric_rows(old) != guard.table_numeric_rows(swapped)


def test_compact_composition_parser_accepts_four_rows():
    rows = guard.composition_rows(compact_table())
    assert len(rows) == 4
    assert rows["Natural"] == (("0.8337", "0.8067", "0.8008"), "No")
    assert rows["Same-class only"][1] == "Yes"


def test_journal_caption_and_actual_input_path_are_required():
    body = (
        r"\input{tables/benchmark_journal} "
        r"\input{tables/composition_oracle_journal} "
        r"POST-HOC ORACLE COMPOSITION DIAGNOSTIC; NOT EVALUATED; "
        r"five seeds; 32 receivers; same frozen query universe; "
        r"100\% coverage; 128-packet bank; at most 32 peers; non-deployable"
    )
    guard.require_journal_inputs(body)
    with pytest.raises(ValueError, match="input"):
        guard.require_journal_inputs(
            body.replace("composition_oracle_journal", "composition_oracle")
        )
    with pytest.raises(ValueError, match="caption"):
        guard.require_journal_inputs(body.replace("NOT EVALUATED", "pending"))


def test_compact_composition_rejects_duplicate_row():
    modified = compact_table().replace(
        "Natural & 0.8337 & 0.8067 & 0.8008 & No\\\\",
        "Natural & 0.8337 & 0.8067 & 0.8008 & No\\\\\n"
        "Natural & 0.8337 & 0.8067 & 0.8008 & No\\\\",
    )
    with pytest.raises(ValueError, match="duplicate"):
        guard.composition_rows(modified)


def test_composition_f1_is_source_checked(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    table = repo / guard.MANUSCRIPT / "tables/composition_oracle_journal.tex"
    table.parent.mkdir(parents=True)
    table.write_text(compact_table(), encoding="utf-8")
    summary = tmp_path / "summary.csv"
    write_summary(summary, sample_summary())
    monkeypatch.setattr(guard, "COMPOSITION_SHA256", hashlib.sha256(
        summary.read_bytes()
    ).hexdigest())
    result = guard.verify_composition(repo, summary)
    assert result["checked_f1_cells"] == 12
    table.write_text(compact_table().replace("0.8337 & 0.8067", "0.8338 & 0.8067", 1))
    with pytest.raises(ValueError, match="composition F1 differs"):
        guard.verify_composition(repo, summary)


def test_composition_rejects_query_coverage_drift(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    table = repo / guard.MANUSCRIPT / "tables/composition_oracle_journal.tex"
    table.parent.mkdir(parents=True)
    table.write_text(compact_table())
    summary = tmp_path / "summary.csv"
    rows = sample_summary()
    rows[0]["evaluable_query_records"] = "738014"
    write_summary(summary, rows)
    monkeypatch.setattr(guard, "COMPOSITION_SHA256", hashlib.sha256(
        summary.read_bytes()
    ).hexdigest())
    with pytest.raises(ValueError, match="coverage"):
        guard.verify_composition(repo, summary)


def test_committed_macro_export_lineage():
    actual = guard.source_macros(ROOT)
    assert len(actual) == 276
    assert actual["vP0macro_f1raw"] == "0.805679"
    assert actual["vT3Amacro_f1raw"] == "0.833692"
    assert actual["vSAR_GNmacro_f1raw"] == "0.805684"


def test_journal_benchmark_cell_tamper_is_rejected(tmp_path, monkeypatch):
    baseline = guard.git_file(
        ROOT, guard.BASELINE_REF, guard.MANUSCRIPT / "tables/benchmark.tex"
    )
    monkeypatch.setattr(guard, "git_file", lambda *_: baseline)
    repo = tmp_path / "repo"
    body_path = repo / guard.MANUSCRIPT / "shared/body.tex"
    body_path.parent.mkdir(parents=True)
    body_path.write_text(
        r"\input{tables/benchmark_journal} "
        r"\input{tables/composition_oracle_journal} "
        r"POST-HOC ORACLE COMPOSITION DIAGNOSTIC; NOT EVALUATED; "
        r"five seeds; 32 receivers; same frozen query universe; "
        r"100\% coverage; 128-packet bank; at most 32 peers; non-deployable; "
        r"293 of 320",
        encoding="utf-8",
    )
    journal = repo / guard.MANUSCRIPT / "tables/benchmark_journal.tex"
    journal.parent.mkdir(parents=True)
    journal.write_text(
        baseline.decode("utf-8").replace("SAR-GN &", r"SAR-GN$^\dagger$ &")
    )
    assert guard.verify_journal_tables(repo, guard.BASELINE_REF)["benchmark_rows"] == 12
    journal.write_text(journal.read_text().replace("0.8337", "0.8338", 1))
    with pytest.raises(ValueError, match="numeric rows"):
        guard.verify_journal_tables(repo, guard.BASELINE_REF)


def test_delta_figure_values_are_frozen(tmp_path):
    import json
    import shutil

    repo = tmp_path / "repo"
    for relative in (
        guard.EVIDENCE / "prior_receiver_inference.json",
        guard.EVIDENCE / "receiver_inference.json",
        Path("configs/paper3/pr90_journal_polish/frozen_p2_receiver_delta.json"),
        guard.MANUSCRIPT / "figures/receiver_delta_summary.provenance.json",
        guard.MANUSCRIPT / "figures/receiver_delta_summary.pdf",
        guard.MANUSCRIPT / "figures/receiver_delta_summary.png",
    ):
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    body = repo / guard.MANUSCRIPT / "shared/body.tex"
    body.parent.mkdir(parents=True, exist_ok=True)
    body.write_text(r"\includegraphics{receiver_delta_summary}")
    assert guard.verify_journal_delta_figure(repo)["checked_source_rows"] == 4
    manifest = repo / guard.MANUSCRIPT / "figures/receiver_delta_summary.provenance.json"
    data = json.loads(manifest.read_text())
    data["rows"][0]["mean"] += 0.001
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="plotted values"):
        guard.verify_journal_delta_figure(repo)


def test_live_pr90_guard_when_frozen_small_summary_available():
    if not SUMMARY.exists():
        pytest.skip("external frozen composition summary absent")
    report = guard.audit(ROOT, SUMMARY)
    assert report["status"] == "PASS"
    assert report["numeric_macros"] == 276
    assert report["composition"]["checked_f1_cells"] == 12
