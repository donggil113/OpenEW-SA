# Paper 2 overnight LaTeX audit report

Audit date: 2026-08-11

## Outcome

The Paper 2 IEEEtran manuscript passes a clean Linux/WSL build and PDF technical
audit. The final manuscript is 11 US-letter pages with five figures and four
tables. There are no compilation errors, undefined internal references,
missing files, multiply-defined labels, overfull boxes, font warnings, or Type
3 fonts.

## Files modified or added

- `.gitignore` (added)
- `main.tex`
- `sections/experimental_setup.tex`
- `sections/introduction.tex`
- `sections/methods.tex`
- `sections/reproducibility.tex`
- `sections/results.tex`
- `tables/table4_stagewise_summary.tex`
- `pdf_technical_audit.md` (added)
- `submission_readiness_report.md`
- `overnight_latex_audit_report.md` (added)

All changes are confined to
`papers/paper2_ood_rf_signal_recognition/ieee_latex/`.

## Fixes made

- Added IEEE-safe discretionary break points and compact formatting for long
  monospaced score-method identifiers.
- Used compact formatting for long artifact field/file identifiers where they
  caused severe column justification.
- Adjusted the widths of Figures 2 and 3 to improve float-page balance without
  changing either source PDF.
- Converted Table IV from a custom fractional font size to the standard IEEE
  `\scriptsize`, tightened spacing conservatively, and made its note
  ragged-right. All 33 rows and numerical values remain unchanged.
- Normalized declaration placeholders to readable sentence-case placeholder
  text without filling in any metadata.
- Added `.gitignore` rules for generated build artifacts only; source TeX and
  source PDFs remain tracked.
- Updated the readiness report from its obsolete no-engine status to the actual
  successful WSL build status.

No scientific prose was rewritten solely to silence harmless underfull-box
warnings, and global `\sloppy` was not introduced.

## Build result

Clean build command:

```text
latexmk -C main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
```

- Result: PASS.
- Engine: pdfTeX 1.40.25, TeX Live 2023/Debian.
- Build driver: latexmk 4.83.
- Output: `build/main.pdf`.
- Pages: 11.
- PDF size: 546,023 bytes.
- Figures: 5.
- Tables: 4.

## Remaining warnings

- Overfull boxes: 0.
- Underfull boxes: 13 (9 horizontal and 4 vertical).
- LaTeX warnings: 2, both reporting that page 7 contains only floats.
- Font warnings: 0.

The remaining underfull warnings are harmless: ordinary IEEE column
justification, a long monospaced reproducibility path, visible reference
placeholders, and float-heavy pages. Page 7 contains Figure 2 and Table III;
page 8 contains Figures 3 and 4. Both pages were inspected and are readable.

## PDF technical audit

- Paper size: US letter, 612 x 792 points.
- All 27 font objects embedded and subset: PASS.
- Type 3 fonts: 0.
- Undefined cross-references: 0.
- Undefined citations: 0.
- Multiply-defined labels: 0.
- Missing figures/files: 0.
- Expected figures included: 5 of 5.
- Full-page visual review: 11 of 11 pages inspected at 120 dpi.

Detailed results are in `pdf_technical_audit.md`.

## Scientific safeguards and integrity

- No numerical value or statistical conclusion was changed.
- `ts_entropy_cosine_euclidean` remains prespecified primary.
- The Mahalanobis four-component method remains exploratory.
- DeepSense remains a negative fixed-orientation result.
- Score negation remains post-hoc diagnostic only and does not replace the
  primary DeepSense result.
- Detection accuracy remains evaluation-descriptive.
- No experiment, scoring, or bootstrap analysis was rerun.
- No bibliographic metadata was invented.
- The supplementary package was not created: the complete stage-wise results,
  reproducibility information, provenance description, and methodological
  safeguards already remain in the main manuscript, and no essential result
  was moved out of it.

## Remaining submission blockers

1. Resolve all 17 reference placeholders R1--R17 using verified sources.
2. Replace the author, affiliation, corresponding-author, ORCID, funding,
   conflict-of-interest, data-availability, code-availability, and
   acknowledgments placeholders.
3. Have the authors approve the final proof and journal-specific declaration
   wording.

## Items requiring human visual review

- Confirm journal preference for the float-only page containing Figure 2 and
  Table III.
- Review Table III and the 33-row Table IV at 100% zoom and in print.
- Confirm Figure 3 labels are sufficiently large for the target journal's
  production workflow; it remains explicitly AUROC-only.
- Confirm the Figure 5 post-hoc diagnostic marking remains prominent after any
  publisher-side scaling.
- Proofread all completed author metadata, declarations, and references after
  the placeholders are replaced.

## Final validation record

- Paper 2 unit tests: **PASS, 17 of 17** (`Ran 17 tests in 16.100s`, `OK`).
- `git diff --check`: **PASS**, no whitespace errors. Git emitted only the
  host's informational LF-to-CRLF working-copy notices.
- Untracked-file trailing-whitespace/final-newline audit: **PASS**.
- Changed or untracked paths outside `ieee_latex/`: **none**.
- Paper 1 tracked, untracked, or staged changes: **none**.
- Frozen snapshot integrity: **PASS**, 265 of 265 files, with current tree
  digests matching the recorded pre-pass values:
  - `v0_ood_baselines`: 44 files,
    `22fa2e71b97b367e54a87eaa4bda3d5dedca5d2a42ba722884f33f9777d157cc`.
  - `v1_temperature_scaling_full`: 65 files,
    `c9b803a135d59b8952837f1069b57c752422fa5cd357bdfab1275af8f9ad63b6`.
  - `v2_distance_ood_scores`: 51 files,
    `e679c8b26640b493bc63eea7bb147ad5101b6f92e93d8448d350cd2f328cf600`.
  - `v3_uncertainty_distance_fusion`: 105 files,
    `6a81ad75e555883e29a4e6b0b729571865bbf96f1f1ba3146c4ba626a720857c`.
- Experiment/bootstrap reruns: **none**. Test execution used only temporary
  synthetic fixtures.
- Reference metadata invented: **none**.
- Commits, pushes, merges, or pull requests: **none**.
