#!/usr/bin/env python
"""Inspect raw JamShield CSV files before conversion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


def inspect_raw_jamshield(raw_dir: str | Path) -> list[dict[str, Any]]:
    """Collect shape, columns, missing counts, and row previews for JamShield CSV files."""

    root = Path(raw_dir).expanduser()
    if not root.exists():
        raise FileNotFoundError(f"Raw JamShield directory does not exist: {root}")

    rows: list[dict[str, Any]] = []
    for csv_path in sorted(root.rglob("*.csv")):
        frame = pd.read_csv(csv_path)
        rows.append(
            {
                "relative_path": str(csv_path.relative_to(root)),
                "num_rows": len(frame),
                "num_columns": len(frame.columns),
                "column_names": list(frame.columns),
                "missing_value_count_per_column": {column: int(count) for column, count in frame.isna().sum().items()},
                "first_3_rows": frame.head(3).to_dict(orient="records"),
            }
        )
    return rows


def write_reports(rows: list[dict[str, Any]], output: str | Path) -> tuple[Path, Path]:
    """Write a readable text report and a CSV summary table."""

    output_path = Path(output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".csv":
        csv_path = output_path
        text_path = output_path.with_suffix(".txt")
    else:
        text_path = output_path
        csv_path = output_path.with_suffix(".csv")

    report = format_text_report(rows)
    text_path.write_text(report, encoding="utf-8")
    pd.DataFrame([_flatten_row(row) for row in rows]).to_csv(csv_path, index=False)
    return text_path, csv_path


def format_text_report(rows: list[dict[str, Any]]) -> str:
    lines = ["JamShield raw CSV inspection", ""]
    if not rows:
        lines.append("No CSV files found.")
        return "\n".join(lines)

    for row in rows:
        lines.extend(
            [
                f"File: {row['relative_path']}",
                f"Rows: {row['num_rows']}",
                f"Columns: {row['num_columns']}",
                f"Column names: {', '.join(row['column_names'])}",
                "Missing values per column:",
            ]
        )
        missing_counts = row["missing_value_count_per_column"]
        if missing_counts:
            lines.extend(f"  {column}: {count}" for column, count in missing_counts.items())
        else:
            lines.append("  <none>")
        lines.append("First 3 rows:")
        lines.append(pd.DataFrame(row["first_3_rows"]).to_string(index=False) if row["first_3_rows"] else "  <empty>")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _flatten_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "relative_path": row["relative_path"],
        "num_rows": row["num_rows"],
        "num_columns": row["num_columns"],
        "column_names": json.dumps(row["column_names"]),
        "missing_value_count_per_column": json.dumps(row["missing_value_count_per_column"]),
        "first_3_rows": json.dumps(row["first_3_rows"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect raw JamShield CSV files.")
    parser.add_argument("--raw-dir", required=True, help="Raw JamShield directory to scan recursively.")
    parser.add_argument(
        "--output",
        default="tables/jamshield_raw_inspection.txt",
        help="Readable text report path, or .csv path for the CSV summary.",
    )
    args = parser.parse_args()

    rows = inspect_raw_jamshield(args.raw_dir)
    report = format_text_report(rows)
    print(report)
    text_path, csv_path = write_reports(rows, args.output)
    print(f"Wrote text report: {text_path}")
    print(f"Wrote CSV summary: {csv_path}")


if __name__ == "__main__":
    main()
