# Paper 3 audience and venue builds

The canonical manuscript under `papers/paper3_reviewer_remediation/manuscript/` is
the frozen scientific source. The builder copies it into a new, external build
directory. Only that staged copy receives submission identity, availability,
acknowledgment, and supplementary provenance edits. Numerical macros, tables,
figures, abstract, and the canonical shared body remain untouched.

Enter verified human information in the single source file
`papers/paper3_reviewer_remediation/manuscript/shared/submission_metadata.tex`.
Unfilled sentinel values are suppressed from staged PDFs rather than being
printed. Thus a successful build is a formatting candidate, **not** approval to
submit: its `build_manifest.json` records pending fields and
`ready_for_human_submission: false`. Authors must approve the disclosure,
funding/COI, release position, and venue package before journal submission.

Use the frozen presentation-only figures from the reviewed release package (or
regenerate them from the same frozen inputs). The builder verifies their
manifest and SHA256 hashes before staging. The IEEE Access class/font archive
must be obtained from the official IEEE source and match the checked SHA256.
Each `--output` must be a new, nonexistent directory outside Git. From the
repository root, set `BUILD_ROOT` to such a parent directory and run:

```sh
PYTHON=/home/user/venvs/openew-sa/bin/python
FIGURES=/mnt/d/openew_sa_data/paper3/pr90_submission_cleanup/20260928T154347Z/presentation/figures
ACCESS_TEMPLATE=/mnt/d/openew_sa_data/paper3/reviewer_remediation/literature/ACCESS_latex_template_20260513.zip

"$PYTHON" scripts/paper3/reviewer_remediation/build_pdfs.py --repository . \
  --audience internal --target tmlcn --output "$BUILD_ROOT/tmlcn_internal"
"$PYTHON" scripts/paper3/reviewer_remediation/build_pdfs.py --repository . \
  --audience submission --target tmlcn --submission-figures "$FIGURES" \
  --output "$BUILD_ROOT/tmlcn_submission"
"$PYTHON" scripts/paper3/reviewer_remediation/build_pdfs.py --repository . \
  --audience internal --target access --access-template "$ACCESS_TEMPLATE" \
  --output "$BUILD_ROOT/access_internal"
"$PYTHON" scripts/paper3/reviewer_remediation/build_pdfs.py --repository . \
  --audience submission --target access --access-template "$ACCESS_TEMPLATE" \
  --submission-figures "$FIGURES" --output "$BUILD_ROOT/access_submission"
"$PYTHON" scripts/paper3/reviewer_remediation/build_pdfs.py --repository . \
  --audience submission --target supplement --submission-figures "$FIGURES" \
  --output "$BUILD_ROOT/supplement_submission"
```

The internal build retains the `OpenEW-SA Internal Review` masthead. The
submission stage leaves unresolved author metadata blank, removes internal
mastheads and workflow chronology, and retains the scientifically necessary
post-hoc evidence distinction. The supplementary PDF uses the same frozen
tables and figures but has journal-facing provenance wording.
