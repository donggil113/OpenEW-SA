# Pre-unblinding code and evidence-grain audit

Status: **COMPLETED WHILE V2 TARGET METRICS REMAINED BLIND**

This audit was performed while the primary LOSO suite serialized only target query IDs and probability vectors. Completed run records had `held_out_metrics=null` and `target_labels_loaded_for_metrics=false`. None of the changes below alters a split, support bank, model, checkpoint, prediction, eligible class, seed, or target metric.

## Corrections made before unblinding

1. **Table-generation name error.** The information-regime table referenced an undefined variable. It now derives the exact observed model set from the validated primary result table. SOURCE-NORM is retained in the TTA/DG/normalization baseline table.
2. **Day-holdout evidence grain.** The evidence ledger no longer treats a day-fold/seed aggregate as a receiver observation. It expands the serialized per-receiver macro-F1 values, averages repeated seeds/days inside receiver, and then summarizes 32 receivers.
3. **Source-only comparator selection.** The strongest TTA and source-DG comparators are selected from equal-weight per-receiver source-validation macro-F1. Pooled packet-weighted validation performance cannot choose the comparator.
4. **Normalization control.** A paired RX-NORM-minus-SOURCE-NORM descriptive comparison was added so receiver-specific test-time statistics can be distinguished from the same normalization computed on source training data.
5. **Context diagnostics.** The one-row-per-receiver/model/seed analysis now records support count, query count, overlap, isolation, attention entropy, effective peer count, inference time, and throughput when applicable. Non-applicable attention fields remain null rather than being fabricated for R0 or T3A methods.
6. **Composition diagnostic scope.** The label-dependent oracle conditions are evaluated with the frozen P2 checkpoint. P2-SHUFFLED is not a separately trained model: it reuses that same checkpoint and changes only inference support. The natural P2-versus-P2-SHUFFLED primary comparison therefore tests shuffled context directly; duplicating the same checkpoint under identical oracle support would not provide an additional comparison. Only full-coverage P2 same-class-excluded evidence can enter the existing GO rule.
7. **Quality gates.** The analysis validator now requires exact receiver/model/seed grains, exact sensitivity grids, exact oracle condition/model sets, bounded metrics, valid query/evaluable counts, complete compute rows, and disjoint P2 support/query diagnostics.
8. **PR #84 immutability.** An external SHA-256 manifest freezes all 54 files in PR #84's final-analysis tree. Final integrity validation requires exact path, size, and digest equality in addition to raw-archive, conversion-manifest, and Git-path checks.
9. **Exact primary grid.** The pre-unblinding gate independently requires every one of the 32 receiver × 13 method × 5 seed conditions exactly once, with the frozen raw-data, 128-support, `k=32`, full-retention, blind-prediction configuration. A duplicate cannot substitute for a missing condition.
10. **Checkpoint lineage.** All 1,280 trained primary checkpoints are hashed at the freeze. Each derived P2 control must match its receiver/seed P2 checkpoint, T3A must match P0, and RX-NORM must match SOURCE-NORM. The lineage gate fails on any missing or altered base checkpoint.
11. **Standardized inference benchmark.** A fixed seed-829, 32-receiver,
    13-method benchmark reloads every frozen checkpoint, excludes checkpoint
    load, includes support/adaptation work, and must reproduce each blind
    archive to absolute error at most `1e-5` without reading target labels.
12. **Bounded parallel scheduling.** An optional second worker is limited to
    the static receiver range 31 down to 20 and writes worker-specific state.
    It cannot rewrite the global plan/status and refuses a `RUNNING` collision.
    Two-process launch used about 5.0 GiB of 24.6 GiB GPU memory; no third
    process is permitted.
13. **Sensitivity checkpoint reuse.** The general training CLI can execute
    only the primary LOSO or coarse-day phases. Support-budget and context-`k`
    sensitivities must reload primary P2 checkpoints through the fixed
    post-unblinding diagnostic path; accidental redundant retraining now fails.
14. **Information/compute accounting.** The method registry and generated
    table distinguish target-receiver support from source-validation donor
    support. RX-NORM is charged raw I/Q-statistics operations rather than
    fictitious support CNN forwards; measured latency covers omitted prototype
    and normalization overhead.
15. **Secondary receiver completeness.** Every coarse-day model/seed row must
    contain the same complete set of 32 finite per-receiver scores. The report
    ledger also preserves receiver-averaged transmitter-pure prediction bias,
    so the confound report need not reopen packet-level outputs.

## Validation completed

- A partial archive preflight reconstructed frozen query IDs without annotations and verified SHA-256, six-class dimensions, finite probability simplexes, and zero support/query overlap for every completed record available at the audit checkpoint.
- All 246 V2 tests present before the additions passed; focused tests for every correction above also passed. Final counts are reported after the suite completes.
- The 19 static-relational, 84 prospective-metadata, 93 dataset-qualification, 152 PR #84 WiSig, and 17 Paper 2 regression tests passed.
- `git diff --check` passed.
- Paper 1, Paper 2, and prior Paper 3 Git paths remained unchanged relative to PR #84.

Final counts are re-run after all primary and secondary work. This file records timing and intent; it is not a substitute for the final quality, integrity, and scientific reports.

## Power-loss recovery confirmation before unblinding

The interrupted worktree was compared with the immutable recovery backup at `/mnt/d/openew_sa_data/paper3/wisig_v2/recovery/worktree_20260904_210457/`. Its HEAD, branch, eight tracked modifications, and 71 archived untracked files matched the live recovery state. A complete UTF-8/syntax audit read all 99 current V2 source, configuration, test, and report files; no empty file, merge marker, partial patch marker, parse error, or missing backup member was found. No V2 worker, pre-unblinding freeze, unblinding manifest, primary analysis table, or receiver-level inference output existed.

The label-free recovery reconciliation independently reconstructed frozen support/query membership from acquisition metadata only and verified every blind archive, configuration, split hash, data-manifest hash, execution commit, checkpoint/history requirement, and derived-checkpoint lineage. It passed for 2,080/2,080 primary, 260/260 day-secondary, and 180/180 grouped-secondary runs, with zero failed or incomplete records. The external evidence is `recovery/blinded_run_reconciliation_20260904.json`; its primary run-registry, prediction-manifest, checkpoint-manifest, and history-manifest SHA-256 values are respectively `b43e324f7d3de5b911638ad4ea10d8cf119c644710da6d7c7d646a19186a5ebf`, `9e80ed7a25ddcf3d9aa3365d0a687eb9549257cbf789040cdc71c20391c2e1f1`, `159a7c8df1a283addd7e713e48b7ee0d1afbaa8177324255cc9c51c7fca74bf6`, and `5e81b3c4844266be6128e4e86a0004f8b5545b5c4e4d5b0c9514220ef9d9a387`.

### Frozen-contract checklist

1. **Exact primary grid:** the gate requires exactly 32 receivers times 13 methods times five seeds, or 2,080 unique configurations.
2. **Exact query alignment:** every archive's opaque query-ID set is reconstructed from its frozen split and label-free support ranking; duplicate, missing, or additional IDs fail.
3. **Split-local class mapping:** each probability matrix must have the eligible class dimension recorded by its own frozen split summary; no global class index is substituted.
4. **Blind archive scope:** archives contain only `sample_ids` and `probabilities`; records retain null target metrics and `target_labels_loaded_for_metrics=false`.
5. **One explicit label boundary:** held-out transmitter annotations are indexed only by the one-time unblinding path after predictions are frozen.
6. **Source-only TTA selection:** the strongest same-information TTA is selected only from equal-weight source-validation receiver macro-F1; target metrics are unavailable to selection.
7. **Receiver inferential unit:** the held-out receiver, not the packet or seed, is the primary statistical unit.
8. **Seed averaging order:** the five paired seed differences are averaged inside each receiver before inference across 32 receiver values.
9. **Bootstrap fixed:** receiver resampling uses exactly 10,000 replicates and seed `20260903`.
10. **Sign flips fixed:** the two-sided receiver sign-flip analysis uses exactly 100,000 Monte Carlo permutations and seed `20260903`.
11. **Holm family fixed:** correction covers only P2 versus P0, P0-WIDE, P2-SHUFFLED, and the source-validation-selected same-information TTA.
12. **Sensitivity is checkpoint-only:** support-budget and context-`k` analyses reload frozen primary P2 checkpoints and cannot train or replace primary conditions.
13. **Oracle status explicit:** transmitter-pure, same-class-excluded, and same-class-only contexts require labels and remain nondeployable diagnostics.
14. **Secondary ordering enforced:** day, grouped-receiver, and equalized unblinding paths require the immutable primary unblinding manifest first.
15. **Create-once event:** both pre-unblinding and unblinding manifests fail if the destination already exists; a second target unblinding is prohibited.

The immutable pre-unblinding freeze also records its UTC creation time, clean analysis commit, original execution commit, primary run-registry hash, prediction and checkpoint manifests, split hash, preregistration hashes, data-manifest hash, and the complete V2 analysis-code-tree hash.
