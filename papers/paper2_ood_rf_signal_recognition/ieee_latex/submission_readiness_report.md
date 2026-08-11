# Paper 2 submission readiness report

Report date: 2026-08-11

## Overall status

The IEEEtran journal manuscript builds successfully and passes the structural,
layout, and PDF technical checks performed in this hardening pass. The package
is technically ready for author review, but it is not ready for journal
submission until the 17 unresolved references and all author/declaration
metadata placeholders are replaced with verified information.

## Compile status

- Status: **PASS**.
- Build environment: Linux/WSL, pdfTeX 1.40.25, TeX Live 2023/Debian, and
  latexmk 4.83.
- Clean-build command:

      latexmk -C main.tex
      latexmk -pdf -interaction=nonstopmode -halt-on-error \
        -file-line-error main.tex

- Output: `build/main.pdf`.
- Page count: 11.
- Paper size: US letter, 612 x 792 points (8.5 x 11 inches).
- PDF size: 546,023 bytes (approximately 533.2 KiB).
- Figures: 5 of 5 expected PDF figures included.
- Tables: 4 of 4 expected tables included.
- Compilation errors: 0.
- Undefined cross-references: 0.
- Undefined citations: 0.
- Missing figures or files: 0.
- Multiply-defined labels: 0.
- LaTeX warnings: 2, both the repeated notice that text page 7 contains only
  floats.
- Font warnings: 0.
- Overfull boxes: 0.
- Underfull boxes: 13 total: 9 `\hbox` and 4 `\vbox` warnings.

The remaining underfull warnings are harmless. Five horizontal warnings arise
from ordinary justified prose in narrow IEEE columns; one comes from long
monospaced reproducibility paths; three occur in the deliberately visible
reference-placeholder list. The four vertical warnings accompany float-heavy
pages. Scientifically correct prose was not rewritten merely to suppress these
warnings, and global `\sloppy` was not used.

## PDF and visual audit

- All 27 font objects reported by `pdffonts` are embedded and subset.
- Type 3 fonts: 0.
- PDF encryption: none.
- PDF version: 1.5.
- All 11 pages were rasterized at 120 dpi and inspected.
- Captions, table entries, axes, and figure legends are readable at final page
  size; no clipping or content collisions were observed.
- Figure 3 remains explicitly restricted to AUROC comparisons.
- Figure 5 is visibly marked **POST-HOC DIAGNOSTIC ONLY** in both the graphic
  and caption.
- Table IV remains complete with all 33 frozen v0--v3 rows and all four
  reported metrics.
- Page 7 is intentionally float-only and holds Figure 2 and Table III. Page 8
  holds Figures 3 and 4. This is dense but readable and avoids the prior
  overfull vertical boxes.

See `pdf_technical_audit.md` for the command-level PDF audit.

## Manuscript inventory

- Approximate word count: 4,652 words. This unchanged static estimate includes
  the title, abstract, body, and in-body figure captions; it excludes equations,
  table source files, declarations, and the unresolved manual bibliography.
  `texcount` is unavailable in the build environment.
- Figures: 5 PDF figures.
- Tables: 4 wide IEEE `table*`/`tabularx` tables.
- Internal labels: 28 unique equation, figure, table, and section labels.

## References

- Unresolved reference placeholders: R1--R17 (17 total).
- Compiler-level undefined citations: 0 because each placeholder is represented
  visibly in the temporary manual reference list.
- Every unresolved item remains visible at its claim location and in the
  reference list.
- `references.bib` contains placeholder comments only; no bibliographic
  metadata was fabricated.
- Submission blocker: replace all 17 placeholders with independently verified
  references and update the in-text citations/reference list.

## Required metadata and statements

All requested metadata fields remain explicit placeholders and therefore
require human completion:

| Item | Status |
|---|---|
| Authors | Placeholder; blocking |
| Affiliations | Placeholder; blocking |
| Corresponding author and email | Placeholder; blocking |
| ORCID identifiers | Placeholder; blocking |
| Funding agency/program/grant | Placeholder; blocking |
| Conflict of interest | Placeholder; blocking |
| Data availability and data license | Placeholder; blocking |
| Code availability, repository/version, and license | Placeholder; blocking |
| Acknowledgments | Placeholder; blocking |

## Scientific and repository integrity

- No numerical result, statistical conclusion, dataset definition, score
  orientation, experimental role, or primary/exploratory designation was
  changed.
- `ts_entropy_cosine_euclidean` remains the prespecified primary method.
- The Mahalanobis four-component method remains exploratory.
- DeepSense remains a negative fixed-orientation result.
- DeepSense score negation remains a post-hoc diagnostic only.
- Detection accuracy remains evaluation-descriptive.
- No experiment, score generation, or bootstrap analysis was rerun.
- No reference metadata was invented.
- Paper 1 and the frozen v0--v3 snapshot trees are unchanged; final command
  results are recorded in `overnight_latex_audit_report.md`.

## Unit-test execution

The requested discovery command was run in Linux/WSL with a temporary isolated
test environment under the ignored `build/` directory. The environment was
removed after the run:

```text
python -m unittest discover \
  -s papers/paper2_ood_rf_signal_recognition/tests -v
```

Result: **PASS, 17 of 17 tests** (`Ran 17 tests in 16.100s`, `OK`). The tests
used temporary synthetic fixtures; no publication experiment or bootstrap
analysis was rerun.

## Submission decision

**Technical build: PASS. Submission package: BLOCKED ON HUMAN METADATA AND
REFERENCES.** Complete the nine metadata/declaration items, resolve R1--R17
with verified bibliographic records, and perform a final author proof at 100%
zoom before submission.
