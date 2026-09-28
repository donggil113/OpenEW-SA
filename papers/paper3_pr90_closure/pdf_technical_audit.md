# PR #90 closure PDF technical and visual audit

Status: **PASS for payload-absent reporting build**, not for full scientific reproduction or submission. The versioned create-once reporting snapshot is papers/paper3_pr90_closure/reporting_snapshot_manifest.json (SHA256 e5ff9adf329aeb6bee002aca9c1b45a60f19bd1931df196baf130f3ee5999f6e). The canonical shared PR #90 source and the official Access ZIP were copied to a **new** external stage; the old PR #90 release/source checksums were not rewritten. Frozen figure and table regeneration in that stage matched the snapshot bytes.

| PDF | Pages | SHA256 | Composition table | Technical check |
|---|---:|---|---|---|
| TMLCN main | 9 | 12af5e41366078a8809104e00a366443e3349b2030df33f8764bce154383b5fd | Table V, page **6** | embedded fonts; Type 3 = 0; undefined citation/reference = 0; overfull = 0 |
| IEEE Access main | 10 | f82cb162857724342fad1d57f7881fe55fd234144cd7282492081a54f67e5b2a | Table 5, page **6** | same checks pass |
| Supplement | 11 | ac7d455cbde5dfac92e65334bd894c285f1f8537116064584bd9948283db9f07 | detailed source/limitations on page **2** | same checks pass |

External final output: /mnt/d/openew_sa_data/paper3/pr90_closure/20260928T110826Z/reporting_final_v1/. Its report.json records all PDF checks and the snapshot hash. Regenerated figures/tables were checked against the frozen source registry before PDF build. This stage did not load RF payload, run training, create target predictions or unblind any result.

## Direct visual checks

At 150 dpi, both main PDFs' page 6 and supplement pages 1--2 were rendered and inspected, not inferred solely from LaTeX source. The composition table is actually visible in the Results float, contains four conditions (natural, same-class excluded, same-class only, transmitter pure), T3A/P2/RX-NORM columns, 32 receivers, five seeds, bank/peer size, query coverage, same-query indication and label-dependence. EMB-STD/SAR-GN are marked NOT EVALUATED. The table is legible with no observed clipping or text overlap. The caption explicitly calls it POST-HOC ORACLE COMPOSITION DIAGNOSTIC. The supplement page 2 explains label-dependent selection, missing archived oracle per-query IDs and the natural-versus-oracle peer-count confound.

The title/abstract use source-only P0 and constructed packet-disjoint support language. PDF text extraction confirms 293 resets, same-class diagnostics, the matched-query P0 value, source-only temperature fitting and the draft Acknowledgments. The support-budget figure uses its frozen values; the new matched-query comparison is interpretive prose, not a modified figure. The manuscript is still an internal-review draft with placeholder authorship and unapproved title/AI disclosure.

No final human proofread of all numerical claims or venue compliance has occurred. Exact code/data execution fidelity is documented separately. **SAFE FOR SUBMISSION: NO.**
