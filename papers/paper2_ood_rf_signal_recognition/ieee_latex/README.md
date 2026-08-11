# Paper 2 IEEE LaTeX manuscript package

This directory is the IEEE journal-style LaTeX conversion of
../manuscript/paper2_full_manuscript_draft.md. It uses
\documentclass[journal]{IEEEtran}, section-level source files, four wide
tables, and the five verified publication-analysis PDF figures.

## Scientific status

- Prespecified primary method: ts_entropy_cosine_euclidean.
- Exploratory ablation: ts_entropy_cosine_euclidean_mahalanobis.
- DeepSense: negative result under the fixed higher-is-more-OOD orientation.
- DeepSense score negation: post-hoc diagnostic only.
- Detection accuracy: evaluation-descriptive because its threshold is selected
  on the evaluation sample.
- No experiment, score-generation stage, or bootstrap analysis is rerun by this
  manuscript package.

All R1--R17 citation gaps remain visible in main.tex. references.bib contains
comments only and deliberately contains no fabricated BibTeX metadata. The
temporary manual bibliography in main.tex keeps those gaps visible in a
compiled draft. Replace each placeholder only after verifying the source
requirements in ../manuscript/unresolved_reference_requirements.md.

## Verified analysis sources

For local reproducibility and numerical auditing, the verified analysis root is:

    /mnt/d/openew_sa_data/paper2/experiments/v3_publication_analysis_20260807

On the Windows host used for this conversion, the equivalent root is:

    D:\openew_sa_data\paper2\experiments\v3_publication_analysis_20260807

The manuscript reads values from the verified CSV tables and embeds byte-for-byte
copies of the five PDF figures. Absolute local paths are intentionally confined
to this README and do not appear in submission-facing .tex files.

## Build

Prerequisites are an existing TeX distribution containing IEEEtran, latexmk,
and the packages imported by main.tex. Do not install packages as part of the
manuscript build.

From this directory:

    make

or:

    ./build.sh

The included latexmkrc places generated files in build/. To clean auxiliary
files, run make clean; to remove all generated LaTeX output, run make
distclean.

## Package layout

- main.tex: IEEEtran entry point, abstract, author/declaration placeholders,
  and visible unresolved-reference register.
- sections/: complete manuscript body split by major section.
- tables/: the four manuscript tables.
- figures/: the five verified PDF figures.
- references.bib: R1--R17 comments only.
- submission_readiness_report.md: current validation and submission blockers.
- template_adaptation_notes.md: IEEE template decisions and deliberate
  deviations pending final metadata and bibliography.

## Submission blockers

Before submission, replace all author, affiliation, corresponding-author,
ORCID, funding, conflict-of-interest, data-availability, code-availability,
and acknowledgment placeholders. Resolve R1--R17 with verified bibliographic
metadata and direct claim support. Recompile with the target journal's TeX
environment and review every page, especially the wide tables and Figure 3 at
final size.
