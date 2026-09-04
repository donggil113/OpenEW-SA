"""Technical checks for the nine publication-oriented V2 PNG/PDF figures."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .hashing import canonical_json_bytes, sha256_file


EXPECTED_FIGURES = (
    "per_receiver_p2_minus_p0",
    "p2_vs_controls_and_tta",
    "context_composition_vs_gain",
    "support_budget_curve",
    "context_k_curve",
    "hardware_stratified_receiver_results",
    "day_holdout_secondary",
    "information_budget_diagram",
    "compute_latency_comparison",
)


def parse_pdffonts(output: str) -> dict[str, int | bool]:
    lines = [line for line in output.splitlines()[2:] if line.strip()]
    type3 = sum("Type 3" in line or "Type3" in line for line in lines)
    unembedded = 0
    for line in lines:
        values = line.split()
        if len(values) >= 5 and values[-5].lower() == "no":
            unembedded += 1
    return {"font_rows": len(lines), "type3_fonts": type3, "unembedded_fonts": unembedded, "all_embedded": unembedded == 0}


def audit_figure_exports(root: str | Path, destination: str | Path) -> dict[str, Any]:
    root = Path(root); rows: list[dict[str, Any]] = []; failures: list[str] = []
    for name in EXPECTED_FIGURES:
        png, pdf = root / f"{name}.png", root / f"{name}.pdf"
        if not png.is_file() or not pdf.is_file() or not png.stat().st_size or not pdf.stat().st_size:
            failures.append(f"missing_or_empty:{name}")
            continue
        info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
        fonts = parse_pdffonts(subprocess.check_output(["pdffonts", str(pdf)], text=True))
        pages = next((int(line.split(":", 1)[1]) for line in info.splitlines() if line.startswith("Pages:")), 0)
        if pages != 1:
            failures.append(f"wrong_page_count:{name}:{pages}")
        if not fonts["all_embedded"]:
            failures.append(f"unembedded_font:{name}")
        if fonts["type3_fonts"]:
            failures.append(f"type3_font:{name}")
        if fonts["font_rows"] == 0:
            failures.append(f"no_font_rows:{name}")
        rows.append(
            {
                "figure": name,
                "png_size_bytes": png.stat().st_size,
                "pdf_size_bytes": pdf.stat().st_size,
                "png_sha256": sha256_file(png),
                "pdf_sha256": sha256_file(pdf),
                "pdf_pages": pages,
                **fonts,
            }
        )
    payload = {"status": "PASS" if not failures and len(rows) == len(EXPECTED_FIGURES) else "FAIL", "expected_figure_count": len(EXPECTED_FIGURES), "validated_figure_count": len(rows), "failures": failures, "figures": rows}
    destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(canonical_json_bytes(payload))
    if payload["status"] != "PASS":
        raise RuntimeError(f"V2 figure technical audit failed: {failures}")
    return payload
