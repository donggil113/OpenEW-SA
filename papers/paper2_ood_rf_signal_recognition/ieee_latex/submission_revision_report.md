# Paper 2 Submission Revision Report

Report date: 2026-08-13

## Outcome

The scientific/editorial submission revision passes the requested LaTeX, citation, PDF, test, and integrity checks. The title was not changed. No experiment, score-generation, model-training, or bootstrap analysis was rerun.

## Exact files changed

1. papers/paper2_ood_rf_signal_recognition/manuscript/paper2_full_manuscript_draft.md
2. papers/paper2_ood_rf_signal_recognition/manuscript/numerical_traceability_matrix.md
3. papers/paper2_ood_rf_signal_recognition/manuscript/title_review.md
4. papers/paper2_ood_rf_signal_recognition/ieee_latex/main.tex
5. papers/paper2_ood_rf_signal_recognition/ieee_latex/references.bib
6. papers/paper2_ood_rf_signal_recognition/ieee_latex/sections/introduction.tex
7. papers/paper2_ood_rf_signal_recognition/ieee_latex/sections/related_work.tex
8. papers/paper2_ood_rf_signal_recognition/ieee_latex/sections/datasets.tex
9. papers/paper2_ood_rf_signal_recognition/ieee_latex/sections/methods.tex
10. papers/paper2_ood_rf_signal_recognition/ieee_latex/sections/results.tex
11. papers/paper2_ood_rf_signal_recognition/ieee_latex/sections/discussion.tex
12. papers/paper2_ood_rf_signal_recognition/ieee_latex/tables/table3_paired_comparisons.tex
13. papers/paper2_ood_rf_signal_recognition/ieee_latex/supplementary/supplementary.tex
14. papers/paper2_ood_rf_signal_recognition/ieee_latex/supplementary/tables/table_s1_stagewise_summary.tex
15. papers/paper2_ood_rf_signal_recognition/ieee_latex/submission_revision_report.md

No Paper 1 file, frozen experiment output, bootstrap output, source CSV, or source figure was modified.

## Verified citations applied

The temporary R1--R17 submission placeholders were removed from the submission-facing Markdown and TeX and replaced with independently verified records from manuscript/reference_verification/references_verified.bib. The IEEE manuscript now uses standard BibTeX:

    \bibliographystyle{IEEEtran}
    \bibliography{references}

The applied evidence groups are:

- spectrum monitoring and ElectroSense infrastructure: ITU and Rajendran et al.;
- confidence under shift, OOD, and open-set protocol framing: Ovadia et al., Nguyen et al., Shafaei et al., Yang et al., Scheirer et al., and Geng et al.;
- RF domain-shift context: Al-Shawabka et al. and Hanna et al.;
- MSP, predictive uncertainty, calibration, and energy scoring: Hendrycks and Gimpel, Ovadia et al., Guo et al., and Liu et al.;
- prototype and feature-distance scoring: Snell et al., Sun et al., and Lee et al.;
- OOD metrics: Hendrycks and Gimpel and Liang et al.;
- bootstrap and paired-comparison underpinnings: Efron and Tibshirani and Dietterich;
- ElectroSense, DeepSense, and JamShield provenance: the independently verified publication, framework, and dataset records;
- selective prediction: El-Yaniv and Wiener and Geifman and El-Yaniv; and
- likelihood/typicality inversion context: Nalisnick et al. and Ren et al.

No bibliographic metadata was invented or repaired from memory. The reference-verification audit retains 30 approved records, while the submission bibliography now contains the 29 records actually cited and rendered. The unused optional `davis2006prroc` entry was removed from `ieee_latex/references.bib`; no citation was added merely to retain it.

## Bounded citation treatments

### Bootstrap and paired comparison

Efron and Tibshirani and Dietterich are cited only as methodological underpinnings. The manuscript explicitly states that neither source prescribes the exact composite procedure. The exact procedure is identified as this study's analysis design: ID and OOD groups were resampled separately at their original counts, and identical sampled indices were reused across methods within each dataset and replicate.

### ElectroSense taxonomy

The DAB/DVB-T/FM/LTE/GSM/TETRA taxonomy is explicitly scoped to the converted OpenEW-SA subset. The text does not attribute the exact six-class construction to the Zenodo record. It acknowledges the upstream framework's unkn label and states that the analyzed frozen manifest and split artifacts exclude it; read-only artifact inspection found only the six named technology labels.

These bounded treatments resolve the submission placeholders without claiming that the cited bootstrap sources prescribe the study-specific resampling design or that the Zenodo record enumerates the exact analyzed taxonomy. Human author sign-off on this bounded wording remains advisable.

### Additional attribution safeguards

- Predictive entropy is not presented as an original contribution of Hendrycks and Gimpel.
- The Mahalanobis covariance regularizer is identified as an implementation detail of this study, not as a prescription from Lee et al.
- JamShield cites the verified IEEE ICC 2025 publication rather than an arXiv-only version.

## DeepSense no-skill context

Results and Discussion now state that DeepSense contains 3,200 ID and 16,000 OOD observations among 19,200 evaluation rows, yielding OOD prevalence 0.833333. Consequently, both the no-skill AUPR-OOD baseline and the all-OOD trivial detection-accuracy baseline are 0.833333. The primary AUPR-OOD of 0.737936 is below that prevalence baseline, and the evaluation-descriptive detection accuracy of 0.833490 is only marginally above the trivial baseline.

The text treats these values as descriptive anchors, not new statistical tests. They reinforce the negative fixed-orientation interpretation, and detection accuracy remains evaluation-descriptive. The two derived baselines were added to the numerical traceability matrix as N017 and N018.

## Comparator scope

Discussion now states that temperature-scaled entropy, cosine distance, and Euclidean distance were prespecified constituent comparators. The comparison demonstrates complementarity relative to those evidence sources, not superiority over the complete OOD literature. The v0--v2 baselines remain contextual and were not retrospectively selected as primary competitors. No external comparator was added post hoc.

## Title review

The current manuscript title remains unchanged. manuscript/title_review.md evaluates all four requested alternatives and recommends:

> Uncertainty and Feature-Distance Fusion for Open-Set RF Signal Recognition

This recommendation minimizes the risk of implying simultaneous raw multimodal fusion while retaining clear RF/open-set scope. Final title selection remains a human author decision.

## Final table-only readability pass

### Table III redesign

Table III now uses compact, single-line mathematical notation in all 48 decision cells: `CI > 0` for a complete paired left-minus-right interval above zero, `CI < 0` for an interval below zero, and `0 in CI` for an interval containing zero. The caption defines each symbol, reiterates that smaller FPR95 is favorable, and states explicitly that the entries are interval-location summaries rather than significance tests. No color-dependent meaning was introduced. A row-by-row equivalence check confirms that all 48 prior positive, negative, and includes-zero decisions are preserved exactly.

### Table IV supplementary relocation

The main manuscript no longer renders the dense 33-row Table IV. The Results section instead points readers to Supplementary Table S1. The complete 33-row v0--v3 table was copied without pruning or method selection to `supplementary/tables/table_s1_stagewise_summary.tex`; every data row is byte-equivalent to the corresponding row in the former main-text table source. The original `tables/table4_stagewise_summary.tex` source remains unchanged and unrendered for traceability.

### File-mode hygiene

`submission_revision_report.md` and `manuscript/title_review.md` now have filesystem mode `0644`, recorded by Git as a pending mode change from `100755` to `100644`. No executable script mode was changed.

## IEEE build and PDF audit

- Clean build command: latexmk -C main.tex, followed by latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
- Compile result: **PASS**
- Compile errors: 0
- Main PDF pages: 11
- Main PDF size: 554,661 bytes
- Paper size: letter, 612 x 792 points
- Figures present: 5 of 5
- Main-text tables present: 3 of 3
- Undefined citations: 0
- Undefined references: 0
- Multiply defined labels: 0
- Overfull boxes: 0
- Underfull hboxes: 12
- Underfull vboxes: 2
- LaTeX warnings: 0
- Font embedding: all fonts embedded
- Type 3 fonts: 0

The supplementary manuscript also compiles successfully from clean source. Its final PDF has 1 page and is 41,187 bytes, with zero undefined references or citations, zero overfull or underfull boxes, all fonts embedded, and zero Type 3 fonts. Supplementary Table S1 contains all 33 frozen stage-wise rows.

The remaining main-manuscript underfull boxes are non-clipping justification or float effects, including long verified URLs and monospaced provenance filenames. They were left intact rather than changing verified metadata or scientifically correct prose. Visual review of all 11 main pages and the complete supplementary page found no clipped table text or unreadable captions/legends. Table III is readable at 100% zoom; Figure 3 remains explicitly AUROC-only; and Figure 5 remains explicitly **POST-HOC DIAGNOSTIC ONLY**.

## Validation and integrity

- Paper 2 tests: **17/17 PASS**
- git diff --check: PASS
- Paper 1: unchanged
- Scientific numerical values: unchanged from HEAD
- Table III paired decisions: 48/48 preserved; notation only redesigned
- Supplementary Table S1: all 33 former Table IV data rows preserved byte-for-byte
- IEEE source figures: unchanged from HEAD
- TeX equation blocks: byte-equivalent to HEAD
- Markdown equation blocks: byte-equivalent to HEAD
- Existing Markdown table rows: byte-equivalent to HEAD
- Frozen v0 snapshot: 44 files, SHA-256 tree digest 22fa2e71b97b367e54a87eaa4bda3d5dedca5d2a42ba722884f33f9777d157cc
- Frozen v1 snapshot: 65 files, SHA-256 tree digest c9b803a135d59b8952837f1069b57c752422fa5cd357bdfab1275af8f9ad63b6
- Frozen v2 snapshot: 51 files, SHA-256 tree digest e679c8b26640b493bc63eea7bb147ad5101b6f92e93d8448d350cd2f328cf600
- Frozen v3 snapshot: 105 files, SHA-256 tree digest 6a81ad75e555883e29a4e6b0b729571865bbf96f1f1ba3146c4ba626a720857c
- Primary/exploratory/post-hoc roles: unchanged
- Scientific numerical results: unchanged
- Experiments rerun: no
- Bootstrap analysis rerun: no

## Remaining submission blockers

The following human-supplied metadata placeholders remain:

- author names;
- affiliations;
- corresponding author and email;
- author ORCID identifiers;
- funding agency, program, and grant number;
- conflict-of-interest statement;
- data-availability statement;
- code-availability/repository/version/license statement; and
- acknowledgments.

Data availability also remains blocked on human confirmation of redistribution terms under the ElectroSense custom dataset license and on JamShield dataset licensing, because the verified public JamShield records do not state an explicit dataset license.

## Remaining human-review items

1. Select the final title after considering manuscript/title_review.md.
2. Supply and approve all author, affiliation, declaration, funding, availability, and acknowledgment metadata.
3. Confirm ElectroSense redistribution terms and obtain or document JamShield dataset-license guidance.
4. Approve the deliberately bounded bootstrap and ElectroSense provenance wording.
5. Perform the journal's final submission-portal and PDF visual check after replacing placeholders.
