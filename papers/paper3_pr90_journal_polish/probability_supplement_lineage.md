# Supplementary probability-table and provenance lineage

This journal-presentation update adds no target predictions, target fitting, metric recomputation, receiver selection, or new scientific result. The canonical PR #90 source is papers/paper3_reviewer_remediation/manuscript/supplementary.tex; the two added probability tables call the pre-existing LaTeX value macros in manuscript/numbers.tex.

## Frozen numeric source

| Role | File | SHA-256 |
|---|---|---|
| Full-precision small summary | papers/paper3_reviewer_remediation/evidence/primary_summary.csv | a7c0203a80c18ea27388eb99312eae5953cabc510f32fadc7f534af4f2a15c09 |
| TeX macros, six-decimal display | papers/paper3_reviewer_remediation/manuscript/numbers.tex | 7b4dc506bdcb7fa4c1b279a5c31426aea0462cfe0f3d6d294cd299e5a1443375 |
| Receiver-averaged frozen analysis | /mnt/d/openew_sa_data/paper3/reviewer_remediation/analysis/receiver_averaged_metrics.csv | c8b4cf3c5c5be7fe57098eb951d0d5633ac5250bbc73fc7f0032dfa38a2c7bc4 |
| Full receiver delta plot relocated to supplement | papers/paper3_reviewer_remediation/manuscript/figures/receiver_deltas.pdf | ef3121e68c8528484302653afc6e5430153eb266de9db9450e5638a76a0e3fa1 |

The evidence/source_manifest.json records analysis Git SHA 20613ae3107044162b865e3ce214ea8dddfe8562, analysis-package SHA b3989f7dad6b561957d7de887c100d7fe90f7baedf3119e5c7fb55c045568953, and the two source-file hashes. The export implementation is scripts/paper3/reviewer_remediation/export_report_evidence.py: it filters to primary-scope rows, averages five seeds within each receiver in the underlying analysis, then averages the 32 receiver rows equally for each method and probability variant. We checked that the five listed methods each have exactly 32 receiver rows for raw and 32 for source-temperature at support 128. The numeric keys printed in the new tables are:

- Methods: P0, T3A, P2, EMB_STD, SAR_GN.
- Variants: raw and source_temperature.
- Metrics: ece, adaptive_ece, nll, brier, mean_confidence, confidence_accuracy_gap.

The full-precision CSV contains all these fields without missing rows; the TeX macros display their already frozen six-decimal values. The supplement does **not** imply probability-calibration equivalence or a newly fitted target temperature. Positive source-validation-only temperature changes scores, not predicted classes. Mean correctness is identical across raw and temperature variants for each method; its value is the corresponding accuracy column in the same source summary. Adaptive ECE uses 15 equal-count top-label groups in stable confidence order, while ECE uses 15 equal-width bins. Multiclass Brier is a sum over the six classes.

## Repository chronology source

The supplementary chronology uses Git commit dates and messages, not reconstructed dates from manuscript memory:

| Event | Verified commit | Git date |
|---|---|---|
| Initial receiver-context study merge, PR #84 | 53bcf41471c11cdd7a96f949fcfcb24b117deccd | 2026-09-03 |
| Disjoint-support V2 study merge, PR #85 | 48cec06645736bd45c455a64841f3f50e0368b40 | 2026-09-05 |
| Receiver-adaptation benchmark preregistration | cdfc2d8 | 2026-09-05 |
| Benchmark merge, PR #88 | 7cc9a27a6cf049690c881068d9163b942c6a2110 | 2026-09-06 |
| Baseline-completeness addendum preregistration | f30b658ff40f4d8ec3770be4c7c2b4692e5814da | 2026-09-06 |

The later addendum was designed after the earlier target outcomes were known; its preregistration before its own execution does not make it independent confirmation.
