# WiSig methods-remediation preregistration V2

Status: **FROZEN BEFORE NEW TARGET-METRIC UNBLINDING**

## Study identity

V2 is a post-review robustness study on the same official WiSig ManyRx compact dataset used in PR #84. It is not an independent-dataset replication. The primary question and terminology are frozen in `scientific_reframing.md`; the complete 32-receiver mapping and six-class support-feasible target set are frozen in `split_freeze_v2.md`.

## Information regimes

- **R0, pure inductive:** each query uses the trained source model and its own packet only. P0, P0-WIDE, SOURCE-NORM, DG-CORAL, DG-GROUPDRO, and DG-DANN.
- **R1, unlabeled receiver calibration/context:** a fixed, bounded unlabeled support bank from the target receiver is available before disjoint query prediction. P1, P2, and RX-NORM. P2 controls alter or remove context as declared.
- **R2, test-time adaptation:** T3A updates classifier prototypes from the identical unlabeled target-receiver support bank. No target label or query packet is available to adaptation.

AdaBN and Tent are not applicable because the frozen shared RF backbone has GroupNorm and zero BatchNorm modules. No BatchNorm layer will be retrofitted.

## Support/query contract

For each LOSO receiver and seed, stable SHA-256 ranking of `(seed, receiver_id, sample_id)` selects the first 128 eligible packets as support. Remaining eligible packets are queries. Labels, predictions, correctness, file paths, and target metrics are absent from this API. Support/query IDs are fixed before prediction, disjoint, and partition-local. No query is support for another query.

All methods are scored on the same query IDs within a receiver/seed pair. R0 methods ignore the frozen support bank. P1/P2 may use no more than `k=32` packets from the 128-packet bank per query, chosen by a stable hash of seed, receiver, query sample ID, and support sample ID. The anchor is not a peer. P1 averages support embeddings; P2 uses permutation-invariant attention without position, day, receiver-value, or transmitter embeddings.

The primary support budget is 128 and primary `k` is 32. Secondary support budgets are 16, 32, 64, 128, and 256; when the bank has 16 packets, `k=16`, otherwise `k=32`. Secondary context sizes are 8, 16, 32, and 64 with the bank fixed at 128. The primary settings remain 128/32 regardless of target results.

## Controls

- **P2-SHUFFLED:** 128 unlabeled packets mixed across non-test receivers, selected without labels and approximately day-matched. This deliberately breaks receiver identity. Because a LOSO test partition has only one receiver, donors come from the source-validation partition; this conservative mismatch is disclosed.
- **P2-MISMATCHED-RX:** 128 unlabeled packets from one stable-hash-selected source-validation receiver, approximately day-matched.
- **P2-NULL:** the trained P2 architecture receives no peer embedding.
- **Transmitter-pure support, same-class-excluded support, and same-class-only support:** label-dependent oracle diagnostics performed only after support pools and primary predictions are frozen. They are nondeployable and excluded from the primary method table.

Support composition (class count, entropy, largest/minimum proportion, effective class count, same-class presence) is audited after the support IDs are immutable. It cannot alter a support bank, class set, model, or split.

## Models and training

The PR #84 compact 1-D residual RF backbone and per-packet RMS preprocessing are reused unchanged for P0, P0-WIDE, DG-CORAL, DG-GROUPDRO, DG-DANN, P1, and P2. P0/P1/P2 share the same backbone. P0-WIDE remains the capacity control. P1/P2 train on source receiver episodes only; all source packets may be anchors, while other members of a deterministic source receiver chunk are unlabeled peers. Test queries are strictly disjoint from target support even though source training can reuse source packets in different training roles.

Fixed optimizer budget: AdamW, learning rate `5e-4`, weight decay `1e-4`, maximum 30 epochs, early-stopping patience 8, packet batch 1,024, context node budget 1,056. Source-validation macro-F1 selects checkpoints. CORAL weight `0.1`, GroupDRO eta `0.01`, and DANN gradient-reversal coefficient `0.1` are frozen before target metrics. Seeds are exactly 829, 1829, 2829, 3829, and 4829.

SOURCE-NORM trains with source-training I/Q mean and residual RMS. RX-NORM resets that checkpoint for every receiver and substitutes statistics estimated from the identical 128-packet target support bank. T3A resets P0 for every receiver; `filter_K` is selected separately using source-validation receiver support/query simulations from `{1,5,20,50,100,-1}`, then fixed for that target receiver run.

## Primary and secondary execution

Primary: 32 LOSO receivers × 13 executable conditions × 5 seeds = **2,080 condition records**. Only eight stages train new checkpoints (P0, P0-WIDE, DG-CORAL, DG-GROUPDRO, DG-DANN, SOURCE-NORM, P1, P2); controls and adaptations reuse the relevant frozen source checkpoint.

Secondary: four leave-one-day-out protocols; P2 support-budget sweep; P2 `k` sweep; label-dependent composition diagnostics; hardware stratification; and the separate official equalized-signal comparison. If projected runtime exceeds 48 hours, order is primary LOSO, shuffled/null/mismatched controls, TTA, support budget, composition stress, `k` sensitivity, then repeated grouped receiver holdout. Omitted lower-priority work is reported, not replaced by favorable subsets.

## Target blinding

The full runner saves only sample IDs and class-probability vectors for target queries. It must not print, serialize, or rank target macro-F1, accuracy, balanced accuracy, or ECE. Target annotations are joined once, after every primary record is complete, by an explicit unblinding command. The command writes an immutable timestamp, preregistration hash, frozen-plan hash, and prediction-manifest hash and refuses a second unblinding event.

## Outcomes and inference

Primary outcome: macro-F1 for each held-out receiver, with every receiver equally weighted. Secondary outcomes: accuracy, balanced accuracy, ECE, per-day macro-F1, source-validation behavior, compute, support composition, and attention entropy/effective peer count. Packets are never bootstrap units.

For primary inference, five seed-matched differences are first averaged inside each receiver. Ten thousand paired receiver bootstrap replicates use fixed seed `20260903`. Two-sided receiver-level sign-flip tests use 100,000 Monte Carlo permutations with the same seed (exact enumeration is infeasible for 32 receivers). Holm correction covers only P2 versus P0, P0-WIDE, P2-SHUFFLED, and the strongest same-information TTA selected by mean source-validation receiver macro-F1 before target unblinding. Hardware-family clustered sensitivity is secondary because only three hardware families exist.

## Confirmatory comparisons

P2 minus P0, P0-WIDE, P1, P2-SHUFFLED, P2-NULL, P2-MISMATCHED-RX, RX-NORM, strongest predeclared TTA, and strongest source-DG baseline are paired by receiver and seed. Seed variability is reported separately. No packet-level significance test is permitted.

## GO rule

GO requires: P2 improves receiver-level outcome versus P0 and P0-WIDE; improves versus shuffled and mismatched support; remains competitive with the strongest same-information TTA; is not driven only by same-class support; occurs across multiple receivers/hardware families; passes every leakage/integrity gate; and survives the disjoint support/query design. Otherwise the result is CONDITIONAL GO or NO-GO. Poor results, bad seeds, and bad receivers remain in the analysis.

## Immutable exclusions

No target-driven method addition, architecture change, split change, support rebalance, receiver removal, seed removal, best-budget selection, or post-hoc class inclusion is allowed. Day is split/diagnostic metadata only. Packet order is not time. The study makes no dynamic, temporal, graph, hypergraph, or neuro-symbolic claim.
