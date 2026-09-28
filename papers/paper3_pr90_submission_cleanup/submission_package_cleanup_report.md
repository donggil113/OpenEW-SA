# PR #90 submission-package cleanup

This is a presentation and release-description edit, not a new scientific analysis. No receiver, seed, support budget, split, model result, numeric macro, composition-table cell, checkpoint, prediction, or unblinding artifact was changed. The PR remains a draft; these PDFs are submission candidates with unresolved human metadata, not submitted articles.

## Build separation

The canonical manuscript wrappers remain the internal-review source. The PDF builder's explicit --audience internal mode retains “OpenEW-SA Internal Review.” Its --audience submission mode copies the same scientific body, numbers, bibliography and tables to a new output tree, removes internal-review identity/history/footer text there, and replaces only figure presentation assets generated from the same hash-verified frozen exports. The author/affiliation/ORCID/corresponding-author fields remain placeholders; no person or institution was invented. The Access submission-stage footer removes the official class's example volume/year without modifying the third-party class.

In the final versioned external build, internal and submission staged copies have byte-identical shared/body.tex, numbers.tex, and tables/composition_oracle_journal.tex. Main Figure 2 retains the prior forest-style paired-delta asset. The supplement retains all 32 receivers in fixed identity order. Figure titles omit internal process wording only in the submission build; captions and supplement still identify post-hoc evidence.

Final external output root (UTC 2026-09-28 15:43:47):

    /mnt/d/openew_sa_data/paper3/pr90_submission_cleanup/20260928T154347Z/

| PDF | Pages | SHA-256 | Technical check |
|---|---:|---|---|
| Submission TMLCN main | 9 | 695e39183df95d223bc10d8ed16014e3d0faec25f8e352de89394d45b336f7ac | PASS |
| Submission IEEE Access main | 10 | 2450587d79154920b10cf558089196a5c5d3958340d44397d93fc80ae97afe10 | PASS |
| Submission supplement | 12 | 1052b019918472c24f25d8b2592b2cbe5e25aa144355372bff0f42d00c1361e5 | PASS |

All three submission PDFs have zero compile errors, undefined citations/references, overfull boxes and Type 3 fonts; all fonts are embedded. The builder's submission identity lint is PASS, including absence of “OpenEW-SA Internal Review” and the IEEE Access template's sample “VOLUME 11, 2023.” Internal-review builds remain separately available in the same root. Underfull warnings are 3 in TMLCN, 6 in Access and 0 in supplement; these are not overfull content loss.

Rendered-page inspection covered both main title/abstract pages, Table V, the main forest Figure 2, the support-budget and probability-quality figures, the Access footer, the full receiver-order supplementary plot, and reference-ending pages. No visible clipping or label collision was found at the inspected pages. Table V retains the frozen four conditions and 12 method values with its non-deployable, label-dependent oracle and common-query-universe caption. The SAR-GN row retains 293/320 reset qualification; SHOT-IM remains technically executable but outside the original source-training recipe.

## Disclosure and availability

The Acknowledgments now carries a concise draft distinguishing OpenAI Codex's software/figure/manuscript assistance from Claude's methodological/manuscript critique. It is not final until human authors verify exact systems/versions, affected sections and use level under the [IEEE Author Center policy](https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/). No AI system is assigned authorship. A separate [human-only checklist](submission_checklist.md) records the required approval.

The new Data and Code Availability subsection distinguishes repository code, split hashes/support reconstruction and exact manifests, small derived summaries, original official WiSig RF payload, externally held checkpoints/predictions, and licence/institutional release restrictions. It invents no DOI or RF payload URL.

The final reference check added only a directly relevant, publisher-verified unlabeled new-receiver adaptation antecedent, Yang et al. (2024), DOI 10.1109/JIOT.2024.3389491. No reference was removed; see [reference audit](reference_final_audit.md). Its bibliographic year/pages/DOI are not scientific-result changes.

## Numerical and test validation

The PR #90 journal numerical-lineage guard passed against the frozen evidence: 276 numeric macros, 12 compact composition F1 cells, 18 hashed evidence exports, and all tracked table numeric rows. The final report is external at 20260928T154347Z/numerical_guard.json. Scientific numerical changes: NONE. The presentation renderer checks the source export manifest before drawing and writes to a new directory; the builder also checks that manifest's SHA-256 before staging presentation figures. Canonical tracked figures and their manifest are unchanged.

With the repository's documented import mode and Python path, the full Paper 3 plus Paper 2 suite passed: 1,799 tests, 7 subtests, with six existing NumPy/scikit-learn warnings. Python compileall and git diff --check pass. No model training, held-out SAR rerun, SHOT-IM target experiment, or RF-data download occurred.

## Remaining gates

The submission candidates remain blocked on the [human-only checklist](submission_checklist.md): authorship/affiliations/ORCIDs/correspondence, funding and conflicts, final AI disclosure, target venue/title, and derivative-release approval. The single-dataset and constructed-support scientific limitations remain; PDF success does not resolve them. PR #90 must remain DRAFT and must not be merged or submitted automatically.
