# Paper 2 submission readiness report

Report date: 2026-08-10

## Overall status

The IEEE-style source package is structurally complete, numerically traced, and
ready for compilation in a TeX environment that already provides IEEEtran and
latexmk. It is not submission-ready because the bibliography and required
author/declaration metadata remain unresolved, and this host has no LaTeX
engine.

## Compile status

- Status: not compiled; dependency unavailable.
- Windows host: latexmk, pdflatex, xelatex, lualatex, and tectonic are missing.
- WSL host: latexmk, pdflatex, xelatex, lualatex, bibtex, and texcount are
  missing.
- No TeX packages or tools were installed.
- Page count: unavailable because no LaTeX engine is installed.
- LaTeX warnings: unavailable because no compiler log could be produced.
- Overfull boxes: unavailable without compilation.
- Underfull boxes: unavailable without compilation.
- Static preflight found balanced braces/environments, resolved input and
  graphic targets, unique labels, and resolved internal references.
- Layout items for final compiled review: Tables 3 and 4 at IEEE two-column
  size, the dense labels in Figure 3, and the label/legend spacing in Figure 5.

## Manuscript inventory

- Approximate word count: 4,652 words. This static count includes the title,
  abstract, body, and in-body figure captions; it excludes equations, table
  source files, declarations, and the unresolved manual bibliography. texcount
  is unavailable.
- Figures: 5 PDF figures, each one page.
- Figure integrity: all 5 copied SHA256 hashes match the verified analysis
  assets.
- Figure visual QA: all 5 PDFs were rendered to PNG and inspected for readable
  axes, legends, labels, and scientific-role markings.
- Tables: 4 table* and tabularx tables.
- Table 4 coverage: all 33 verified v0--v3 rows and all four reported metrics.
- Internal labels: 28 unique equation, figure, table, and section labels.

## References

- Unresolved references: R1--R17 (17 total).
- Every unresolved item is visible at its claim location and in the temporary
  manual bibliography.
- references.bib contains comments only; no BibTeX metadata was fabricated.
- Submission is blocked until all 17 references are verified and replaced.

## Required metadata and statements

The following remain explicit placeholders and block submission:

- authors;
- affiliations;
- corresponding author and email;
- ORCID identifiers;
- funding agency/program/grant;
- conflict of interest;
- data availability and data license;
- code availability, repository/version, and code license;
- acknowledgments.

## Numerical and structural validation

- Verified LaTeX structure: passed.
- Table 1 sample counts: matched the prespecified-primary rows in the verified
  v0--v3 publication summary; each ID plus OOD count equals the total.
- Table 2 point estimates and interval bounds: all 12 metric rows matched the
  verified confidence-interval CSV at six-decimal formatting.
- Table 3 signs and includes/excludes-zero decisions: all 48 metric decisions
  matched the verified paired-differences CSV.
- Table 4 stage-wise metrics: all 33 rows matched the verified publication
  summary at six-decimal formatting.
- Submission-facing absolute local paths: none.
- Obvious typography audit: no WiFi, v0-v3, TheDeepSense, or non-ASCII dash
  forms remain in the TeX source.
- git diff --check: passed with no output.

## Unit-test execution

The requested discovery command was executed with the existing OpenEW-SA
evaluation virtual environment:

    python -m unittest discover -s papers/paper2_ood_rf_signal_recognition/tests -v

Result on the Windows host: 16 of 17 tests passed; one WSL-specific path
conversion assertion failed because the tested D: feature path exists natively
on Windows and therefore is not rewritten to /mnt/d. The failure is
environment-specific and unrelated to the new LaTeX-only files.

The suite was also attempted with WSL python3. That interpreter lacks NumPy, so
the three test modules could not be imported. No packages were installed. The
verified publication-analysis independent review records that all 17 tests pass
in the provisioned WSL target environment.

## Repository and frozen-artifact integrity

- Paper 1 changed paths: none.
- New repository paths are confined to
  papers/paper2_ood_rf_signal_recognition/ieee_latex/.
- The verified publication-analysis validation report records 17 of 17 checks
  passed, including no Paper 1 changes and unchanged frozen v0--v3 hashes.
- Current frozen snapshot inventory remains 265 files:
  - v0_ood_baselines: 44 files; tree SHA256
    22fa2e71b97b367e54a87eaa4bda3d5dedca5d2a42ba722884f33f9777d157cc.
  - v1_temperature_scaling_full: 65 files; tree SHA256
    c9b803a135d59b8952837f1069b57c752422fa5cd357bdfab1275af8f9ad63b6.
  - v2_distance_ood_scores: 51 files; tree SHA256
    e679c8b26640b493bc63eea7bb147ad5101b6f92e93d8448d350cd2f328cf600.
  - v3_uncertainty_distance_fusion: 105 files; tree SHA256
    6a81ad75e555883e29a4e6b0b729571865bbf96f1f1ba3146c4ba626a720857c.
- This manuscript task performed read-only access to the frozen snapshots and
  did not rerun experiments, scoring, or bootstrap analysis.

## Submission decision

Not ready for submission. Resolve R1--R17 and every metadata/declaration
placeholder, compile with IEEEtran and latexmk, inspect the resulting page
layout, record the page count and compiler warnings, and rerun the full unit
suite in the provisioned WSL environment before submission.
