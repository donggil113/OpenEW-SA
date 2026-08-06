# Paper 2 Unresolved Reference Requirements

## Purpose

The full manuscript deliberately uses `[REFERENCE NEEDED: Rx]` tokens instead of guessed citations. This register defines the evidence needed for each token. A reference should be added only after its bibliographic metadata and support for the associated claim have been verified.

| ID | Manuscript section(s) | Claim requiring support | Preferred source |
| --- | --- | --- | --- |
| R1 | Introduction | Operational RF monitors encounter changing emitters, receivers, sites, propagation conditions, and interference regimes. | Authoritative RF spectrum-monitoring review, standards document, or primary field study. |
| R2 | Introduction | Closed-set classifiers can be overconfident under distribution shift, and calibration differs from OOD separability. | Foundational or peer-reviewed OOD/calibration study. |
| R3 | Introduction | OOD orientation, normalization, model selection, and thresholds should be fixed without target-test labels to avoid leakage. | Peer-reviewed evaluation-protocol or model-selection guidance for OOD/open-set work. |
| R4 | Related Work | Definition and scope of open-set recognition. | Foundational open-set recognition paper or authoritative survey. |
| R5 | Related Work | RF-specific relevance of class, sensor, day, channel, and interference shifts. | RF OOD/domain-generalization survey or multiple primary RF studies. |
| R6 | Related Work | Maximum softmax probability and predictive entropy as confidence/OOD baselines. | Original method papers or authoritative OOD benchmark study. |
| R7 | Related Work; Methods; Discussion | Scalar temperature scaling as an ID-validation-fitted post-hoc calibration method and its distinction from OOD detection. | Original temperature-scaling/calibration paper plus, if needed, an OOD-calibration study. |
| R8 | Related Work | Logit energy as an OOD score. | Original energy-based OOD detection paper. |
| R9 | Related Work | Prototype, nearest-centroid, and feature-distance approaches for novelty detection. | Foundational prototype/open-set or feature-distance OOD work. |
| R10 | Related Work; Methods | Shared-covariance Mahalanobis distance for OOD scoring and the rationale for regularization. | Original or canonical Mahalanobis OOD paper and a numerical-method source if required. |
| R11 | Related Work; Methods | Interpretation of AUROC, AUPR-OOD, and FPR95 for OOD evaluation. | Authoritative OOD benchmark paper or metric-methodology reference. |
| R12 | Related Work; Methods | Paired stratified bootstrap intervals for methods evaluated on the same observations. | Statistical bootstrap reference and, if available, paired-model-comparison guidance. |
| R13 | Dataset section | ElectroSense dataset provenance, collection design, and signal-technology labels. | Primary ElectroSense dataset publication and official dataset record. |
| R14 | Dataset section | DeepSense dataset provenance, I/Q acquisition design, occupancy codes, and acquisition-day domains. | Primary DeepSense dataset publication and official dataset record. |
| R15 | Dataset section | JamShield dataset provenance, telemetry features, jammer scenarios, and benign conditions. | Primary JamShield dataset publication and official dataset record. |
| R16 | Discussion | Selective-prediction or risk-coverage evaluation as a complement to calibration and OOD detection. | Foundational selective-classification/risk-coverage reference. |
| R17 | Discussion | Two-sided tail, density, or typicality scoring as candidate responses to domain-shift inversion. | Peer-reviewed typicality, density-based OOD, or two-sided anomaly-detection work. |

## Verification Checklist For Each Added Reference

- Confirm title, author list, venue, year, pages or article identifier, and DOI/URL from a primary bibliographic source.
- Read the source passage that supports the manuscript claim; do not cite from title or abstract alone when the claim is more specific.
- Prefer original method and dataset papers over secondary summaries.
- Avoid using one reference to support claims it does not directly make.
- Record the final citation key and replacement location for every `Rx` token.
- Re-run a repository search to confirm no `[REFERENCE NEEDED` token remains before submission.

## Deliberately Unsupported Claims

No numerical result depends on a literature citation. Numerical provenance is handled separately in `numerical_traceability_matrix.md`. The reference gaps concern background, method lineage, metric interpretation, dataset provenance, and future-work framing only.
