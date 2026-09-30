"""Technical and language lint for staged, non-submitted Paper 3 PDFs."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

FORBIDDEN = {
    "internal review": re.compile(r"OpenEW-SA\s+Internal\s+Review", re.I),
    "pull-request number": re.compile(r"\bPR\s*\\?#\s*\d+\b", re.I),
    "closure": re.compile(r"\bclosure\b", re.I),
    "legacy": re.compile(r"\blegacy\b", re.I),
    "reviewer-remediation": re.compile(r"reviewer[- ]remediation", re.I),
    "Unix private path": re.compile(r"/(?:mnt|home)/[^\s]+", re.I),
    "Windows private path": re.compile(r"\b[A-Z]:\\[^\s]+", re.I),
    "TODO": re.compile(r"\bTODO\b", re.I),
    "HUMAN_REQUIRED": re.compile(r"HUMAN[_ -]?REQUIRED", re.I),
    "placeholder": re.compile(r"\bplaceholder\b", re.I),
    "draft only": re.compile(r"\bdraft\s+only\b", re.I),
    "not submitted": re.compile(r"\bnot\s+submitted\b", re.I),
}


def command(*args: str) -> str:
    process = subprocess.run(args, capture_output=True, text=True, check=True)
    return process.stdout


def text_violations(text: str) -> list[str]:
    return [label for label, pattern in FORBIDDEN.items() if pattern.search(text)]


def font_violations(pdffonts_text: str) -> list[str]:
    errors = []
    for line in pdffonts_text.splitlines()[2:]:
        if not line.strip():
            continue
        # pdffonts' table has fixed columns: name, type, encoding, emb, sub, uni, object.
        fields = line.split()
        if len(fields) < 7:
            errors.append("unparseable font row: " + line)
            continue
        if "Type 3" in line:
            errors.append("Type 3 font: " + fields[0])
        # The final five fields are emb/sub/uni/object-ID + generation.
        if fields[-5].lower() != "yes":
            errors.append("font not embedded: " + fields[0])
    return errors


def log_violations(log: str) -> list[str]:
    checks = {
        "undefined reference/citation": r"(?:undefined references|Citation .* undefined|Reference .* undefined)",
        "overfull box": r"Overfull \\[hv]box",
        "LaTeX error": r"^! ",
    }
    return [name for name, pattern in checks.items() if re.search(pattern, log, re.I | re.M)]


def audit_pdf(pdf: Path, log: Path) -> dict:
    if not log.is_file():
        raise RuntimeError(f"missing builder log: {log}")
    info = command("pdfinfo", str(pdf))
    pages_match = re.search(r"^Pages:\s+(\d+)", info, re.M)
    size_match = re.search(r"^Page size:\s+(.+)$", info, re.M)
    if pages_match is None:
        raise RuntimeError(f"pdfinfo did not report page count: {pdf}")
    extracted = command("pdftotext", "-layout", str(pdf), "-")
    # latexmk's outer stdout contains unresolved-citation messages from its
    # initial pass even when the final pass resolves them. Inspect the final
    # TeX .log, while the builder already requires latexmk's exit code zero.
    final_log = pdf.parent / "source" / f"{pdf.stem}.log"
    if not final_log.is_file():
        raise RuntimeError(f"missing final TeX log: {final_log}")
    errors = (
        text_violations(extracted)
        + font_violations(command("pdffonts", str(pdf)))
        + log_violations(final_log.read_text())
    )
    return {
        "pdf": str(pdf),
        "pages": int(pages_match.group(1)),
        "page_size": size_match.group(1) if size_match else "UNKNOWN",
        "font_rows": max(0, len(command("pdffonts", str(pdf)).splitlines()) - 2),
        "issues": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", type=Path)
    parser.add_argument("--tmlcn-build", type=Path)
    parser.add_argument("--access-build", type=Path)
    parser.add_argument("--supplement-build", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    names = ("main_tmlcn", "main_access", "supplementary")
    if args.build_dir is not None:
        if any((args.tmlcn_build, args.access_build, args.supplement_build)):
            parser.error("--build-dir cannot be combined with per-target build roots")
        build_roots = (args.build_dir,) * 3
    else:
        build_roots = (args.tmlcn_build, args.access_build, args.supplement_build)
        if any(root is None for root in build_roots):
            parser.error("provide --build-dir or all three per-target build roots")
    reports = [
        audit_pdf(root / f"{name}.pdf", root / f"{name}_build.log")
        for name, root in zip(names, build_roots, strict=True)
    ]
    result = {"status": "PASS" if all(r["status"] == "PASS" for r in reports) else "FAIL", "pdfs": reports}
    if args.out.exists():
        raise RuntimeError(f"refusing to overwrite audit: {args.out}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
