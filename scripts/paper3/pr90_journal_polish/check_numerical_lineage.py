#!/usr/bin/env python3
"""Fail-closed numeric lineage guard for PR90 journal-only edits.

No RF payload, prediction archive, or target metric is loaded. A figure's PDF
bytes may change for typography; the frozen plot-input exports may not.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

BASELINE_REF = "bafa40ea9366da2bb425f8f3cbdf72381eb1ed05"
P2_SNAPSHOT_SHA256 = "a5d21be336afc3db304866c8cd3c0dc02f3b1928c7d6cb5059d85202075a24ec"
MANUSCRIPT = Path("papers/paper3_reviewer_remediation/manuscript")
EVIDENCE = Path("papers/paper3_reviewer_remediation/evidence")
COMPOSITION_SHA256 = "34feb7b860f69616749a33a5d4fab1169cec318f3052ff832a405fee04c3eacc"
METHODS = ("T3A", "P2", "RX-NORM")
CONDITIONS = {
    "Natural": "NATURAL",
    "Same-class excluded": "SAME_CLASS_EXCLUDED_ORACLE",
    "Same-class only": "SAME_CLASS_ONLY_ORACLE",
    "Transmitter pure": "TRANSMITTER_PURE_ORACLE",
}
MACRO_RE = re.compile(r"\\expandafter\\def\\csname\s+([vd][^\s\\]+)\\endcsname\{([^{}]+)\}")
NUMBER_RE = re.compile(r"(?<![A-Za-z0-9])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?![A-Za-z0-9])")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_file(repo: Path, ref: str, relative: Path) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{relative.as_posix()}"],
        check=True, capture_output=True,
    ).stdout


def baseline_tables(repo: Path, ref: str) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", ref, "--",
         str(MANUSCRIPT / "tables")],
        check=True, capture_output=True, text=True,
    )
    paths = [Path(line) for line in result.stdout.splitlines() if line.endswith(".tex")]
    if len(paths) < 7 or MANUSCRIPT / "tables/composition_oracle.tex" not in paths:
        raise ValueError("baseline table inventory incomplete")
    return paths


def macros(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for key, value in MACRO_RE.findall(text):
        if key in found:
            raise ValueError(f"duplicate numeric macro {key}")
        found[key] = value
    if not found:
        raise ValueError("no numeric macros")
    return found


def table_numeric_rows(text: str) -> list[tuple[str, ...]]:
    """Ordered numeric data cells, excluding headings, prose, and footnotes."""
    rows: list[tuple[str, ...]] = []
    in_body = False
    for line in text.splitlines():
        stripped = line.strip()
        if r"\midrule" in stripped:
            in_body = True
            continue
        if r"\bottomrule" in stripped:
            break
        if not in_body or "&" not in stripped or not stripped.endswith(r"\\"):
            continue
        if r"\multicolumn" in stripped:
            continue
        cells = stripped[:-2].split("&")
        values = tuple(token for cell in cells[1:]
                       for token in NUMBER_RE.findall(cell))
        if values:
            rows.append(values)
    return rows


def table_numbers(text: str) -> Counter[str]:
    return Counter(value for row in table_numeric_rows(text) for value in row)


def table_row_labels(text: str) -> list[str]:
    labels: list[str] = []
    in_body = False
    for line in text.splitlines():
        stripped = line.strip()
        if r"\midrule" in stripped:
            in_body = True
            continue
        if r"\bottomrule" in stripped:
            break
        if not in_body or "&" not in stripped or not stripped.endswith(r"\\"):
            continue
        if r"\multicolumn" in stripped:
            continue
        cells = stripped[:-2].split("&")
        if any(NUMBER_RE.findall(cell) for cell in cells[1:]):
            labels.append(cells[0].replace(r"$^\dagger$", "").strip())
    return labels


def compare_tables(repo: Path, ref: str) -> dict[str, Any]:
    checked: dict[str, Any] = {}
    for relative in baseline_tables(repo, ref):
        if relative.name == "composition_oracle.tex":
            continue
        original_rows = table_numeric_rows(
            git_file(repo, ref, relative).decode("utf-8")
        )
        current_rows = table_numeric_rows(
            (repo / relative).read_text(encoding="utf-8")
        )
        if not original_rows:
            raise ValueError(f"baseline table lacks numeric body cells: {relative}")
        if original_rows != current_rows:
            original = table_numbers(git_file(repo, ref, relative).decode("utf-8"))
            current = table_numbers((repo / relative).read_text(encoding="utf-8"))
            raise ValueError(
                f"frozen numeric rows changed in {relative}: "
                f"removed={dict(original - current)}, added={dict(current - original)}"
            )
        checked[relative.name] = {
            "numeric_cells": sum(map(len, original_rows)),
            "numeric_rows": len(original_rows),
        }
    return checked


def require_journal_inputs(body: str) -> None:
    required = (
        r"\input{tables/benchmark_journal}",
        r"\input{tables/composition_oracle_journal}",
        "POST-HOC ORACLE COMPOSITION DIAGNOSTIC",
        "NOT EVALUATED",
        "five seeds",
        "32 receivers",
        "same frozen query universe",
        r"100\% coverage",
        "128-packet bank",
        "at most 32 peers",
        "non-deployable",
    )
    missing = [phrase for phrase in required if phrase not in body]
    if missing:
        raise ValueError(f"journal table input or composition caption missing: {missing}")


def verify_journal_tables(repo: Path, ref: str) -> dict[str, Any]:
    body = (repo / MANUSCRIPT / "shared/body.tex").read_text(encoding="utf-8")
    require_journal_inputs(body)
    original = git_file(repo, ref, MANUSCRIPT / "tables/benchmark.tex").decode("utf-8")
    updated = (repo / MANUSCRIPT / "tables/benchmark_journal.tex").read_text(
        encoding="utf-8"
    )
    if table_numeric_rows(original) != table_numeric_rows(updated):
        raise ValueError("journal benchmark numeric rows differ from frozen benchmark")
    if table_row_labels(original) != table_row_labels(updated):
        raise ValueError("journal benchmark methods/reassociation differ from frozen benchmark")
    if r"SAR-GN$^\dagger$" not in updated or "293 of 320" not in body:
        raise ValueError("bounded SAR-GN marker/caption is missing")
    return {
        "benchmark_rows": len(table_numeric_rows(original)),
        "benchmark_numeric_cells": sum(map(len, table_numeric_rows(original))),
        "composition_input": "tables/composition_oracle_journal",
        "sar_bounded_marker": True,
    }


def source_macros(repo: Path) -> dict[str, str]:
    evidence = repo / EVIDENCE
    rows = list(csv.DictReader((evidence / "primary_summary.csv").open(
        encoding="utf-8", newline=""
    )))
    if not rows:
        raise ValueError("primary summary empty")
    expected: dict[str, str] = {}
    for row in rows:
        if not row["method"] or not row["probability_variant"]:
            raise ValueError("missing method/probability variant")
        for metric, value in row.items():
            if metric in ("method", "probability_variant"):
                continue
            expected["v" + row["method"] + metric + row["probability_variant"]] = (
                f"{float(value):.6f}"
            )
    inference = json.loads((evidence / "receiver_inference.json").read_text(
        encoding="utf-8"
    ))
    prior = json.loads((evidence / "prior_receiver_inference.json").read_text(
        encoding="utf-8"
    ))
    inference["T3A_MINUS_P0"] = prior["T3A_MINUS_P0"]
    for key, record in inference.items():
        fields = {
            **record["bootstrap"],
            "p_value": record["sign_flip"]["p_value"],
            "positive": record.get("positive", record.get("positive_receivers")),
        }
        for field, value in fields.items():
            if value is None:
                raise ValueError(f"missing inference value {key}/{field}")
            expected["d" + key + field] = (
                str(value) if isinstance(value, int) else f"{float(value):.6f}"
            )
    return expected


def verify_evidence(repo: Path, ref: str) -> dict[str, Any]:
    relative = EVIDENCE / "source_manifest.json"
    baseline = git_file(repo, ref, relative)
    current = (repo / relative).read_bytes()
    if current != baseline:
        raise ValueError("frozen source_manifest.json changed")
    manifest = json.loads(current)
    checked = {}
    for name, expected in manifest["exports"].items():
        path = repo / EVIDENCE / name
        actual = sha256(path.read_bytes())
        if actual != expected:
            raise ValueError(f"frozen evidence changed: {name}")
        checked[name] = actual
    return {
        "source_manifest_sha256": sha256(current),
        "analysis_sha256": manifest["analysis_sha256"],
        "checked_exports": len(checked),
    }


def verify_figures(repo: Path, ref: str, analysis_sha: str) -> dict[str, Any]:
    relative = MANUSCRIPT / "figure_manifest.json"
    old = json.loads(git_file(repo, ref, relative))
    new = json.loads((repo / relative).read_text(encoding="utf-8"))
    if old["analysis_sha256"] != analysis_sha or new["analysis_sha256"] != analysis_sha:
        raise ValueError("figure analysis SHA differs from frozen evidence")
    if sorted(old["figures"]) != sorted(new["figures"]):
        raise ValueError("figure inventory differs from PR90 baseline")
    changed = []
    for name in old["figures"]:
        path = repo / MANUSCRIPT / "figures" / (name + ".pdf")
        actual = sha256(path.read_bytes())
        if new["pdf_sha256"].get(name) != actual:
            raise ValueError(f"figure manifest stale or PDF missing: {name}")
        if old["pdf_sha256"].get(name) != actual:
            changed.append(name)
    return {
        "figure_count": len(old["figures"]),
        "layout_changed_figures": changed,
        "numeric_input_lineage": "same SHA-verified frozen evidence exports",
    }


def verify_journal_delta_figure(repo: Path) -> dict[str, Any]:
    body = (repo / MANUSCRIPT / "shared/body.tex").read_text(encoding="utf-8")
    if "{receiver_delta_summary}" not in body:
        raise ValueError("journal receiver-delta figure is not used in the main manuscript")
    figure_dir = repo / MANUSCRIPT / "figures"
    provenance = json.loads((figure_dir / "receiver_delta_summary.provenance.json").read_text(
        encoding="utf-8"
    ))
    if provenance.get("fixed_method_order") != ["T3A", "P2", "EMB-STD", "SAR-GN"]:
        raise ValueError("journal receiver-delta method order changed")
    if provenance.get("external_v2_original_verified") is not True:
        raise ValueError("frozen V2 P2 origin was not verified by renderer")
    source_hash = provenance["source_sha256"]
    evidence = repo / EVIDENCE
    for key, filename in (
        ("PR90_prior_receiver_inference.json", "prior_receiver_inference.json"),
        ("PR90_receiver_inference.json", "receiver_inference.json"),
    ):
        if sha256((evidence / filename).read_bytes()) != source_hash[key]:
            raise ValueError(f"journal delta source hash changed: {key}")
    snapshot_path = repo / "configs/paper3/pr90_journal_polish/frozen_p2_receiver_delta.json"
    if sha256(snapshot_path.read_bytes()) != P2_SNAPSHOT_SHA256:
        raise ValueError("frozen P2 delta snapshot changed")
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if (
        snapshot["source_sha256"] != source_hash["V2_receiver_level_inference.json"]
        or source_hash["frozen_p2_receiver_delta.json"] != P2_SNAPSHOT_SHA256
        or snapshot["comparison"] != "P2_MINUS_P0"
    ):
        raise ValueError("journal delta P2 source lineage mismatch")
    prior = json.loads((evidence / "prior_receiver_inference.json").read_text(
        encoding="utf-8"
    ))
    posthoc = json.loads((evidence / "receiver_inference.json").read_text(
        encoding="utf-8"
    ))
    records = (
        ("T3A", prior["T3A_MINUS_P0"], "earlier frozen analysis"),
        ("P2", snapshot, "earlier frozen analysis"),
        ("EMB-STD", posthoc["EMB_STD_MINUS_P0"], "post-hoc addendum"),
        ("SAR-GN", posthoc["SAR_GN_MINUS_P0"], "post-hoc addendum"),
    )
    expected = []
    for method, record, origin in records:
        bootstrap = record["bootstrap"]
        if bootstrap["receiver_count"] != 32 or bootstrap["replicates"] != 10000:
            raise ValueError(f"wrong receiver/bootstrap unit in delta figure: {method}")
        expected.append({
            "method": method,
            "mean": float(bootstrap["mean_difference"]),
            "lower": float(bootstrap["ci95_lower"]),
            "upper": float(bootstrap["ci95_upper"]),
            "receivers": 32,
            "replicates": 10000,
            "origin": origin,
        })
    if provenance["rows"] != expected:
        raise ValueError("journal receiver-delta plotted values differ from frozen sources")
    for kind in ("pdf", "png"):
        path = figure_dir / f"receiver_delta_summary.{kind}"
        if sha256(path.read_bytes()) != provenance["output_sha256"][kind]:
            raise ValueError(f"journal delta {kind} differs from provenance manifest")
    return {
        "methods": [row["method"] for row in expected],
        "checked_source_rows": len(expected),
        "pdf_sha256": provenance["output_sha256"]["pdf"],
        "png_sha256": provenance["output_sha256"]["png"],
    }


def composition_rows(table: str) -> dict[str, tuple[tuple[str, str, str], str]]:
    rows = {}
    for line in table.splitlines():
        if "&" not in line or not line.strip().endswith(r"\\"):
            continue
        cells = [cell.strip() for cell in line.strip()[:-2].split("&")]
        for label in CONDITIONS:
            if label.casefold() not in cells[0].casefold():
                continue
            if len(cells) < 5:
                raise ValueError(f"composition row has fewer than five cells: {label}")
            if label in rows:
                raise ValueError(f"duplicate composition row: {label}")
            values = []
            for cell in cells[1:4]:
                matches = NUMBER_RE.findall(cell)
                if len(matches) != 1:
                    raise ValueError(f"composition method cell not singular: {cell}")
                values.append(matches[0])
            state = cells[-1]
            if state not in ("Yes", "No"):
                raise ValueError(f"unrecognized label-dependence cell: {state}")
            rows[label] = (tuple(values), state)
    if set(rows) != set(CONDITIONS):
        raise ValueError(f"composition rows missing/extra: {sorted(rows)}")
    return rows


def verify_composition(repo: Path, summary_path: Path) -> dict[str, Any]:
    data = summary_path.read_bytes()
    if sha256(data) != COMPOSITION_SHA256:
        raise ValueError("composition summary differs from frozen PR90 closure summary")
    summary = list(csv.DictReader(data.decode("utf-8").splitlines()))
    indexed = {(r["method"], r["condition"]): r for r in summary}
    wanted = {(method, condition) for method in METHODS
              for condition in CONDITIONS.values()}
    if len(summary) != 12 or set(indexed) != wanted:
        raise ValueError("composition summary does not have exact 4x3 grid")
    for record in summary:
        if (
            int(record["receiver_count"]) != 32
            or int(record["seed_count"]) != 5
            or int(record["query_records"]) != 738015
            or int(record["evaluable_query_records"]) != 738015
            or float(record["query_coverage"]) != 1.0
        ):
            raise ValueError("composition grain/coverage changed")
    table = (repo / MANUSCRIPT / "tables/composition_oracle_journal.tex").read_text(
        encoding="utf-8"
    )
    rows = composition_rows(table)
    for label, condition in CONDITIONS.items():
        values, state = rows[label]
        if state != ("No" if condition == "NATURAL" else "Yes"):
            raise ValueError(f"wrong oracle/deployable label: {label}")
        for method, shown in zip(METHODS, values, strict=True):
            source = float(indexed[(method, condition)]["receiver_equal_macro_f1"])
            if shown != f"{source:.4f}":
                raise ValueError(
                    f"composition F1 differs: {label}/{method}: {shown} vs {source:.4f}"
                )
    return {
        "summary_sha256": COMPOSITION_SHA256,
        "checked_f1_cells": 12,
        "receiver_count": 32,
        "seed_count": 5,
        "query_records_per_condition": 738015,
    }


def audit(repo: Path, summary_path: Path, ref: str = BASELINE_REF) -> dict[str, Any]:
    repo = repo.resolve()
    if not (repo / ".git").exists():
        raise ValueError(f"not canonical git repository: {repo}")
    evidence = verify_evidence(repo, ref)
    relative = MANUSCRIPT / "numbers.tex"
    original = macros(git_file(repo, ref, relative).decode("utf-8"))
    current = macros((repo / relative).read_text(encoding="utf-8"))
    if current != original:
        missing = sorted(original.keys() - current.keys())
        added = sorted(current.keys() - original.keys())
        changed = sorted(key for key in original.keys() & current.keys()
                         if original[key] != current[key])
        raise ValueError(
            f"original numeric macros changed: missing={missing}, "
            f"added={added}, changed={changed}"
        )
    derived = source_macros(repo)
    if current != derived:
        differing = sorted(key for key in current.keys() | derived.keys()
                           if current.get(key) != derived.get(key))
        raise ValueError(f"numeric macros disagree with frozen exports: {differing}")
    return {
        "status": "PASS",
        "baseline_git_sha": ref,
        "numeric_macros": len(current),
        "tables": compare_tables(repo, ref),
        "journal_tables": verify_journal_tables(repo, ref),
        "figure_lineage": verify_figures(repo, ref, evidence["analysis_sha256"]),
        "journal_delta_figure": verify_journal_delta_figure(repo),
        "composition": verify_composition(repo, summary_path),
        "frozen_evidence": evidence,
        "limitations": (
            "Figure layout bytes may change; frozen plot-input export hashes are "
            "checked, but this guard does not inspect plotted vector coordinates."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--composition-summary", type=Path, required=True)
    parser.add_argument("--baseline-ref", default=BASELINE_REF)
    parser.add_argument("--output", type=Path, help="optional create-once JSON report")
    args = parser.parse_args()
    report = audit(args.repository, args.composition_summary, args.baseline_ref)
    text = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(text)
    print(text, end="")


if __name__ == "__main__":
    main()
