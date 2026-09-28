# Frozen SAR-GN execution audit

Evidence status: **read-only forensic reconciliation of the PR90 post-hoc addendum**. The original official-default SAR-GN records, checkpoints, predictions, analysis manifest, split and support/query IDs remain unchanged. This audit does not evaluate new held-out queries.

## Source, grain and checks

The grain is one receiver_loso_XX × seed × SAR_GN × primary × support128 record. The 160 rows come from the frozen run.json files under the external paper3/reviewer_remediation/experiments root. We joined each row to its saved adapted checkpoint and blind prediction archive, the matched frozen V2 P0 checkpoint/prediction archive, and the immutable raw receiver-seed metrics in paper3/reviewer_remediation/analysis/receiver_seed_metrics.csv.

The audit tool is scripts/paper3/pr90_closure/audit_sar_original.py. It checked completeness and uniqueness of all 32 × 5 keys, exact support/query ID hashes, checkpoint and prediction file SHA256s, then independently replayed **support adaptation only** from each frozen P0 checkpoint. The replay never computed a new held-out prediction or metric. Its final model tensors matched all 160 saved adapted checkpoints exactly. This verifies the reconstructed per-minibatch filter counts and reset trace for the frozen local algorithm. The original run.json does not contain reliable-subset counts; those numbers are reconstructed from support only, not claimed as pre-existing instrumentation.

The external small evidence is sar/original/sar_original_primary160.csv (SHA256 8812abac4395789beb94b8151a0728e7b16789dae4d34545918117d4710d9838) and sar/original/sar_original_summary.json in the new PR90 closure output root. The CSV lists each of the 160 original record/checkpoint hashes, original-versus-source and replay-versus-original tensor comparisons, and matched P0 prediction/metric comparisons. The saved P0 and SAR blind archives are compared without reopening label annotations.

## Recomputed facts

| Check | Actual |
| --- | ---: |
| Receiver × seed records | 32 × 5 = 160, no duplicate/missing key |
| Attempted support minibatch updates | 320 |
| Completed optimizer updates | 320 |
| Resets after updates | 293 / 320 |
| Records with both updates reset | 146 / 160 |
| First-filter retained samples, summed across updates | 17,463 |
| Second-filter retained samples, summed across updates | 16,264 |
| Empty first / second filter | 0 / 0 |
| Support replay versus frozen adapted state, exact tensors | 160 / 160 |
| Final adapted state exactly equals source P0 state | 147 / 160 |
| SAR probability array exactly equals matched P0 | 147 / 160 |
| SAR argmax array exactly equals matched P0 | 147 / 160 |
| SAR macro-F1 exactly equals matched P0, receiver-seed | 147 / 160 |
| Receiver mean SAR minus P0 positive / negative / tied | 3 / 4 / 25 |
| Maximum source-to-final tensor difference | 0.0005850792 |
| Maximum SAR-to-P0 probability difference | 0.05003780 |

The remaining 13 receiver-seed records have different final model tensors, blind probability arrays, argmax arrays and macro-F1 values. A tied receiver mean need not mean identical per-seed predictions. Metric equality, prediction equality and model-state equality were tested independently. The 147 exact equalities here are an observed property of this frozen execution, not an inference from rounded mean macro-F1.

The two-minibatch support run means 320 attempted updates. Reset count 293 follows directly from the reconstructed trace and agrees with each original recoveries field. Specifically, 146 runs reset on both updates, one reset once, and 13 never reset. The latter 13 are the only cases with final weights changed from source; the one-reset case ends at source weights because its last update resets.

## Bounded interpretation

The original near-P0 aggregate result describes **this 128-support, two-minibatch, recovery-heavy local SAR-GN execution**. It does not establish that SAR generally fails, that gradient adaptation cannot work, or that another reset policy would win. The original source checkpoint, selection rule and target results remain frozen. A new source-only sensitivity grid and a possible later held-out evaluation have separate evidence status and cannot replace the official-default row.
