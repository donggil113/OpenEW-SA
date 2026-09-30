"""Build venue PDFs from shared science, with separate review/submission identities.

The canonical manuscript remains the internal-review source. Submission identity
changes are applied only to a fresh staging copy, never to scientific text,
tables, figures, or author metadata awaiting human completion.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path, PurePosixPath


ACCESS_TEMPLATE_SHA256 = (
    "60c7efc9db8ac9e8bdb31c550ad4e03cb6f258a878ececc0bc690b6203e45a67"
)
SUBMISSION_FIGURES = {
    "benchmark.pdf",
    "compute.pdf",
    "probability_quality.pdf",
    "reliability_aggregate.pdf",
    "support_budget.pdf",
    "receiver_deltas.pdf",
    "reliability_raw_1.pdf",
    "reliability_raw_2.pdf",
    "reliability_raw_3.pdf",
    "reliability_raw_4.pdf",
    "reliability_source_temperature_1.pdf",
    "reliability_source_temperature_2.pdf",
    "reliability_source_temperature_3.pdf",
    "reliability_source_temperature_4.pdf",
}


def replace_once(path: Path, old: str, new: str) -> None:
    """Fail closed if the identity wrapper has drifted since review."""
    source = path.read_text()
    if source.count(old) != 1:
        raise RuntimeError(f"expected one identity marker in {path}: {old!r}")
    path.write_text(source.replace(old, new))


def prepare_submission_stage(stage: Path, figures: Path, evidence_manifest: Path) -> None:
    """Remove internal-review identity from staged sources only."""
    if not figures.is_dir():
        raise RuntimeError(f"submission figure directory is missing: {figures}")
    found = {p.name for p in figures.glob("*.pdf")}
    if found != SUBMISSION_FIGURES:
        raise RuntimeError(
            f"submission figure set differs: missing={sorted(SUBMISSION_FIGURES-found)}, "
            f"unexpected={sorted(found-SUBMISSION_FIGURES)}"
        )
    figure_manifest = figures.parent / "figure_manifest.json"
    if not figure_manifest.is_file():
        raise RuntimeError(f"presentation figure manifest is missing: {figure_manifest}")
    presentation = json.loads(figure_manifest.read_text())
    canonical = json.loads((stage / "figure_manifest.json").read_text())
    frozen_input_sha256 = hashlib.sha256(evidence_manifest.read_bytes()).hexdigest()
    stems = {name.removesuffix(".pdf") for name in SUBMISSION_FIGURES}
    if (
        set(presentation.get("figures", [])) != stems
        or set(presentation.get("pdf_sha256", {})) != stems
        or presentation.get("analysis_sha256") != canonical.get("analysis_sha256")
        or presentation.get("evidence") != canonical.get("evidence")
        or presentation.get("receiver_count") != canonical.get("receiver_count")
        or presentation.get("render_variant") != "PRESENTATION_TITLES_ONLY"
        or presentation.get("frozen_plot_input_manifest_sha256") != frozen_input_sha256
    ):
        raise RuntimeError("presentation figure manifest differs from frozen evidence")
    for stem in stems:
        if hashlib.sha256((figures / (stem + ".pdf")).read_bytes()).hexdigest() != (
            presentation["pdf_sha256"][stem]
        ):
            raise RuntimeError(f"presentation figure hash mismatch: {stem}")

    replace_once(
        stage / "main_tmlcn.tex",
        r"\author{OpenEW-SA Internal Review\\Authors, affiliations, ORCIDs and corresponding author require human confirmation}",
        r"\author{Authors, affiliations, ORCIDs and corresponding author require human confirmation}",
    )
    access = stage / "main_access.tex"
    replace_once(access, r"\input{shared/access_draft_layout}", r"\input{shared/access_submission_layout}")
    replace_once(access, r"\history{Internal-review draft only. Not accepted or published.}", "")
    replace_once(
        access,
        r"\author{\uppercase{OpenEW-SA Internal Review}}",
        r"\author{\uppercase{Authors require human confirmation}}",
    )
    replace_once(access, r"\tfootnote{\draftnotice}", "")
    replace_once(
        access,
        r"\markboth{OpenEW-SA: Receiver Adaptation Internal Review}{OpenEW-SA: Receiver Adaptation Internal Review}",
        r"\markboth{OpenEW-SA: Receiver Adaptation}{OpenEW-SA: Receiver Adaptation}",
    )
    replace_once(
        stage / "supplementary.tex",
        r"\author{OpenEW-SA Internal Review}",
        r"\author{Authors require human confirmation}",
    )
    replace_once(
        stage / "shared" / "preamble.tex",
        r"\newcommand{\draftnotice}{Internal-review title proposal (human approval pending); post-hoc analyses; not submission-ready}",
        r"\newcommand{\draftnotice}{}",
    )
    (stage / "shared" / "access_draft_layout.tex").unlink()

    for name in sorted(SUBMISSION_FIGURES):
        shutil.copyfile(figures / name, stage / "figures" / name)
    shutil.copyfile(figure_manifest, stage / "figure_manifest.json")

    for wrapper in ("main_tmlcn.tex", "main_access.tex", "supplementary.tex"):
        text = (stage / wrapper).read_text()
        if "OpenEW-SA Internal Review" in text or "Internal-review" in text:
            raise RuntimeError(f"internal-review identity remains in {wrapper}")


def install_access_template(template: Path, stage: Path) -> None:
    if hashlib.sha256(template.read_bytes()).hexdigest() != ACCESS_TEMPLATE_SHA256:
        raise RuntimeError("unverified IEEE template")
    with zipfile.ZipFile(template) as archive:
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            if (
                path.is_absolute()
                or ".." in path.parts
                or (info.external_attr >> 16) & 0o170000 == 0o120000
            ):
                raise RuntimeError("unsafe template member")
            if path.suffix in (".cls", ".sty", ".map", ".fd", ".pfb", ".tfm") or path.name in (
                "logo.png",
                "notaglinelogo.png",
                "bullet.png",
            ):
                (stage / path.name).write_bytes(archive.read(info))


def build(args: argparse.Namespace) -> dict:
    doc = args.repository / "papers/paper3_reviewer_remediation"
    stage = args.output / "source"
    if args.audience == "submission" and args.submission_figures is None:
        raise RuntimeError("--submission-figures is required for submission builds")
    if args.audience == "internal" and args.submission_figures is not None:
        raise RuntimeError("--submission-figures is only valid for submission builds")
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(doc / "manuscript", stage)
    shutil.copyfile(doc / "references_verified.bib", stage / "references.bib")
    if args.audience == "submission":
        prepare_submission_stage(stage, args.submission_figures, doc / "evidence" / "source_manifest.json")

    targets = ["main_tmlcn", "supplementary"]
    if args.access_template:
        install_access_template(args.access_template, stage)
        targets.append("main_access")
    for target in targets:
        result = subprocess.run(
            ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", target + ".tex"],
            cwd=stage,
            capture_output=True,
            text=True,
        )
        (args.output / (target + "_build.log")).write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError("LaTeX failed: " + target + "; inspect build log")
        shutil.copyfile(stage / (target + ".pdf"), args.output / (target + ".pdf"))
        if args.audience == "submission":
            if shutil.which("pdftotext") is None:
                raise RuntimeError("pdftotext is required for submission identity lint")
            extracted = subprocess.run(
                ["pdftotext", str(args.output / (target + ".pdf")), "-"],
                capture_output=True,
                text=True,
            )
            if extracted.returncode:
                raise RuntimeError("could not inspect submission PDF text: " + target)
            lower = extracted.stdout.casefold()
            if "openew-sa internal review" in lower or "internal-review" in lower:
                raise RuntimeError("internal-review identity leaked into submission PDF: " + target)
            if target == "main_access" and "volume 11, 2023" in lower:
                raise RuntimeError("example Access publication metadata leaked into submission PDF")
    manifest = {
        "status": "BUILT",
        "audience": args.audience,
        "targets": targets,
        "access_template_vendored": False,
        "canonical_manuscript_unchanged": True,
        "submission_identity_lint": "PASS" if args.audience == "submission" else "NOT_APPLICABLE",
        "submission_figure_replacements": sorted(SUBMISSION_FIGURES)
        if args.audience == "submission"
        else [],
    }
    (args.output / "build_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--access-template", type=Path)
    parser.add_argument("--audience", choices=("internal", "submission"), default="internal")
    parser.add_argument("--submission-figures", type=Path)
    print(json.dumps(build(parser.parse_args())))


if __name__ == "__main__":
    main()
