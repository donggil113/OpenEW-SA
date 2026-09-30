# Submission-facing data and code availability policy

This document separates available repository material from artifacts whose release has not been approved. It is an editorial/release policy, not a licence grant. No DOI, archival accession, or new public release URL has been assigned here.

## Proposed manuscript subsection

> **Data and Code Availability.** Source code, configurations, protocols, manuscript sources, and payload-absent analysis/figure-generation tools are prepared for release at HUMAN_RELEASE_URL_REQUIRED after author and institutional approval. The release package may include reviewed split/support hashes, reconstruction rules, and small derived receiver-level summaries; exact sample-level split/support manifests and opaque-ID mappings require separate provenance, linkage-risk, and rights review. The original WiSig RF payload must be obtained from its official provider under its applicable terms and is not redistributed with this work. Converted RF tensors, checkpoints, and sample-level prediction archives are not included in the proposed public package. The payload-absent materials support reconstruction of published tables and figures, but do not by themselves establish independent raw-data conversion, model retraining, or prediction reproduction.

Build rule: HUMAN_RELEASE_URL_REQUIRED belongs in editable metadata/release checklist, not a public-facing submission PDF. If the URL has not been approved, the PDF should use truthful journal-appropriate pending-release wording without a fabricated destination. The authors must approve final availability language and the actual release inventory before submission. No automated publication is authorized.

## Artifact distinctions

| Artifact | Present status | Release boundary |
|---|---|---|
| A. Source code | Git-tracked code and tests exist. | Candidate for public release after repository/IP/secret review. No promise of a separate archival DOI. |
| B. Configurations/protocols | Frozen method, split, and analysis rules are Git-tracked. | Candidate for public release after provenance review. Preserve freeze hashes and post-hoc design labels. |
| C. Split/support hashes | Hash ledgers and reconstruction rules are Git-tracked. | Candidate for public release. Exact sample-ID manifests are different artifacts and require linkage/rights review. |
| D. Derived summary artifacts | Small receiver-level/evidence summaries and figures exist. | Public only after licence, derivative, attribution, privacy/linkage, and institutional review. |
| E. Original WiSig RF payload | Official third-party material, subject to provider terms and CC BY-NC-SA 4.0; held externally. | Do not redistribute in this package. Research-use authorization is not derivative-release approval. |
| F. Checkpoints | External model artifacts, potentially derived from restricted material. | Not in proposed public package; separate rights review required before release. |
| G. Prediction archives | External sample-level artifacts; may reveal labels, identifiers, or derived signal information. | Not in proposed public package; separate rights and disclosure review required. |
| H. Opaque-ID mappings | Audit/provenance linkage can reveal source paths or target identity. | Do not release by default. Review exact contents and re-identification risk. |

The official WiSig data source is cited in the manuscript. Nothing here changes its licence or redistributes its payload. Third-party IEEE templates/fonts are obtained from IEEE and are not vendored. Shen RF data are outside this release and were not obtained for the study.

## Reproducibility claim boundary

- Level A: payload-absent regeneration of reviewed tables, figures, and PDFs from small tracked aggregates, subject to a successful final build/QA on the release commit.
- Level B: split/support reconstruction requires lawfully obtained official RF data and verified conversion/provenance; not established by Level A.
- Level C: model/checkpoint/prediction/analysis reproduction requires lawful data, frozen code/configurations, compatible execution environment, and a new isolated run; not established by Level A or by the proposed PDF package.

See [reproducibility levels](reproducibility_levels.md), [release inventory](release_inventory.md), and the historical [artifact release plan](../paper3_receiver_adaptation_manuscript/artifact_release_plan.md).
