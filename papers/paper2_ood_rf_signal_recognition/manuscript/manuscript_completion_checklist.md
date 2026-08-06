# Paper 2 Manuscript Completion Checklist

## Manuscript Integration

- [x] Preserved the title: *Uncertainty-Calibrated Multi-View RF Signal Recognition for Open-Set Electromagnetic Spectrum Monitoring*.
- [x] Added Abstract, Introduction, Related Work, Datasets and OOD Evaluation Protocols, Methods, Experimental Setup, Results, Discussion, Limitations, Conclusion, Reproducibility Statement, Figure Captions, Table Captions, and References Placeholder sections.
- [x] Integrated the existing methods, results, discussion, limitations, captions, outline, README, and reproducibility materials without editing those source drafts.
- [x] Used ElectroSense, DeepSense, and JamShield capitalization consistently.
- [x] Clarified that the current multi-view implementation fuses uncertainty and distance evidence over dataset-specific processed views rather than claiming simultaneous raw multimodal fusion.

## Scientific Guardrails

- [x] Identified `ts_entropy_cosine_euclidean` as the prespecified primary method.
- [x] Identified `ts_entropy_cosine_euclidean_mahalanobis` as an exploratory ablation.
- [x] Kept DeepSense as a negative result under the fixed higher-is-more-OOD orientation.
- [x] Labeled DeepSense score negation as post-hoc diagnostic only.
- [x] Preserved every primary point estimate and statistical conclusion.
- [x] Avoided claims of universal generalization or universal statistical significance.
- [x] Stated the interval-exclusion decision for every paired comparison and metric.
- [x] Documented the JamShield AUROC, AUPR-OOD, and FPR95 trade-off.
- [x] Labeled detection accuracy evaluation-descriptive.
- [x] Documented the stable-order AUPR-OOD tied-score implementation.
- [x] Preserved the higher-is-more-OOD score convention throughout.

## Figures And Tables

- [x] Mapped Figure 1 to `figure_ood_auroc_with_ci`.
- [x] Mapped Figure 2 to `figure_fpr95_with_ci`.
- [x] Mapped Figure 3 to `figure_primary_fusion_comparison` and stated that it reports AUROC only.
- [x] Mapped Figure 4 to `figure_score_distributions_by_dataset` and stated that score and density axes are dataset-specific.
- [x] Mapped Figure 5 to `figure_deepsense_inversion_diagnostic` with its post-hoc diagnostic label.
- [x] Mapped Table 1 to the dataset and OOD protocol summary.
- [x] Mapped Table 2 to bootstrap confidence intervals.
- [x] Mapped Table 3 to paired method differences.
- [x] Mapped Table 4 to the v0-v3 publication summary.

## Numerical And Reference Integrity

- [x] Transcribed empirical values only from the verified publication-analysis CSVs.
- [x] Added `numerical_traceability_matrix.md` with keyed source rows, metrics, and columns.
- [x] Added `[REFERENCE NEEDED: Rx]` placeholders instead of inventing citations.
- [x] Added `unresolved_reference_requirements.md` describing the evidence needed for every placeholder.
- [ ] Replace all reference placeholders with verified bibliography entries before submission.
- [ ] Add verified author, affiliation, corresponding-author, funding, conflict-of-interest, and data-license statements.

## Repository Validation

- [x] Programmatically compared all manuscript point estimates, interval bounds, and sample counts with the source CSVs.
- [x] Programmatically compared all paired signs and interval-exclusion decisions with the paired-differences CSV.
- [x] Audited primary, exploratory, fixed-orientation, post-hoc, and evaluation-descriptive terminology.
- [x] Ran the complete Paper 2 unit-test suite successfully in its WSL target environment.
- [x] Ran `git diff --check` and an untracked-file whitespace audit.
- [x] Confirmed that no Paper 1 path changed.
- [x] Confirmed all frozen v0-v3 snapshot hashes against the preserved pre-analysis SHA256 ledger.

## Submission-Stage Work

- [ ] Select a target journal and apply its article type, word limit, heading hierarchy, citation style, and figure/table placement rules.
- [ ] Decide whether the full confidence-interval and stage-wise tables belong in the main paper or supplement.
- [ ] Insert final figure and table assets in the journal's required format.
- [ ] Conduct domain-expert review of dataset descriptions and RF terminology.
- [ ] Conduct statistical review of multiplicity language and deployment-threshold interpretation.
- [ ] Perform final copyediting and accessibility review for figures and tables.
