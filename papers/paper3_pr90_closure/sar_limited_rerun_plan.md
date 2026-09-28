# Limited future SAR operational-sensitivity target evaluation — plan only

Status: **NOT AUTHORIZED FOR EXECUTION IN THIS PR**. Evidence class if separately approved: POST-HOC OPERATIONAL-SENSITIVITY ADDENDUM. This is a plan for independent review after the new source-validation-only diagnostic and its manifest are frozen. It does not replace the original official-default SAR-GN row or the original PR90 analysis manifest.

## Fixed scope

- Exactly the original 32 receiver LOSO folds and five seeds: 829, 1829, 2829, 3829, 4829.
- At most 160 new held-out receiver evaluation records: one selected SAR recipe for each fold × seed. A source-only selection may differ across fold-seed records, but each fold's target receiver must be absent from the three receiver validation simulations that select its recipe.
- Support budget 128, the original label-free support IDs and query IDs, the same frozen six-class split-local mapping and P0 source checkpoint.
- Candidate source-only policies A: reset 0.2 (official hard-coded default) and B: 0.2 log(C)/log(1000) (post-hoc normalized-threshold hypothesis); repeated support passes 1, 5 or 20. Learning rate and every other SAR term remain at the original PR90 values. B is not described as official SAR.
- Source recipe selection: highest equal-receiver macro-F1 on the fold's three source-validation receivers, with frozen candidate-order tie break A1,A5,A20,B1,B5,B20. The source-only performance/quality results, code/config hashes, selected recipe mapping and audit must be independently reviewed before any future target evaluation.
- Original P0, T3A, P2, EMB-STD and official-default SAR are not retrained or overwritten. Existing predictions/checkpoints are read-only.
- Each new target record would be blind; it would use support only for adaptation, save disjoint query predictions, record all 160 statuses and hashes, then undergo one new create-once unblinding event after completeness and code integrity. It would live in a new output root distinct from the original PR90 root and from this closure's source-only root.
- Receiver is the inference unit. Five seed differences are averaged within receiver; 10,000 receiver bootstrap replicates and 100,000 receiver sign flips may be reported as **exploratory post-hoc**, with no insertion into the old confirmatory Holm family. Report all 32 receivers, all seeds, unfavorable outcomes and catastrophic degradations.

The machine-readable create-once plan is externally stored at sar/sar_limited_rerun_plan.json under the new PR90 closure root. Its SHA256 is **7996202d35c604f76291b0126ac8615318e1986d2a82fcdd83b97f1653e431d5**. It enumerates all 160 fold-seed keys, their source-selected recipes, source P0 checkpoint SHA256s, split/data hashes, and the frozen support/query ID hashes; its execution authorization flag is false.

The execution authorizer must see source-only freeze SHA **a50e7f1076ce6f887e8a1a97a4d1c81c4e8dadb2ee2d30f43f98a27891c2a3c6**, source-only summary SHA **684f3c94adfebdb547bbb9f6fb9fb3ede0d1e6057c1769247eb782dcd38a8518**, selected CSV SHA **fab8a987791edb3c1c3a96b8847a07c6966b480555011838a736e4f2b9e0a918**, the fidelity deviations, and the machine-plan SHA above. Approval is a separate human decision. This PR performs **zero** new held-out SAR evaluation records.
