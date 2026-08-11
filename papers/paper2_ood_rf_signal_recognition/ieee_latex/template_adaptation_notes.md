# IEEE template adaptation notes

## Template and structure

- The manuscript uses \documentclass[journal]{IEEEtran} exactly as requested.
- The Markdown heading hierarchy maps to IEEE \section and \subsection
  commands. The abstract and IEEE keywords remain in main.tex.
- Methods equations use numbered equation or align environments with labels
  and \eqref cross-references.
- The four wide result/protocol tables use table* and tabularx.
- All five verified PDF figures use figure*, stable labels, and manuscript
  captions. No figure values or graphics were regenerated.

## Scientific guardrails retained

- ts_entropy_cosine_euclidean remains the prespecified primary method.
- The Mahalanobis four-component method remains exploratory.
- DeepSense remains a negative fixed-orientation result.
- DeepSense score negation remains post-hoc and diagnostic only.
- Detection accuracy remains evaluation-descriptive.
- The JamShield AUROC, AUPR-OOD, and FPR95 trade-off and the limits of
  pointwise, unadjusted intervals remain explicit.

## Typography

- Mathematical variables are typeset in math mode.
- Plain-text version ranges are rendered as v0--v3.
- Wi-Fi uses its standard hyphenation.
- Numeric differences use mathematical minus signs where a sign is displayed.
- Submission-facing .tex files contain no absolute local filesystem paths.

## Bibliography handling

No reference metadata was invented. R1--R17 remain visible both at their claim
locations and in the temporary manual bibliography. references.bib contains
placeholder comments only. After verified references are selected, replace the
manual items with valid BibTeX entries and the journal's standard IEEE
bibliography workflow.

## Metadata and declarations

IEEE author footnotes contain explicit placeholders for authors, affiliations,
corresponding author, ORCID identifiers, and funding. Separate end-matter
placeholders cover conflict of interest, data availability, code availability,
and acknowledgments. These are submission blockers, not inferred statements.

## Build environment

The conversion environment was checked for existing LaTeX tools. Build results
and any unavailable dependency are recorded in
submission_readiness_report.md. No TeX packages were installed.
