# WiSig V2 scientific reframing

Status: **FROZEN BEFORE V2 TARGET-METRIC UNBLINDING**

## Primary question

Does conditioning a fixed RF-fingerprinting model on a bounded set of unlabeled packets from an unseen receiver improve transmitter identification beyond capacity-matched ERM, source-only domain-generalization methods, and test-time adaptation methods given the same unlabeled receiver support?

## Secondary mechanism question

Does any advantage survive shuffled-receiver, mismatched-receiver, null-context, and class-composition stress controls?

## Terminology correction

The leave-one-receiver-out protocol evaluates an unseen receiver/domain shift. P0, P0-WIDE, CORAL-style source alignment, GroupDRO, and DANN are source-only methods in regime R0. P1 and P2 consume unlabeled observations from the held-out receiver and are therefore **test-time receiver-context conditioning** methods in regime R1, not pure domain-generalization methods. T3A is a test-time adaptation method in regime R2.

No V2 claim uses *dynamic*, *temporal reasoning*, *hypergraph*, or *neuro-symbolic*. WiSig supplies no validated deployment timestamp or session sequence. A V2 support bank is a bounded calibration set, not a verified acquisition episode.

## What changed after adversarial review

V2 was designed after criticism of V1. It replaces mutual test-partition context with a fixed, label-free, 128-packet support bank and a disjoint query bank for each receiver and seed. A query is never support for another query. The receiver, not the packet or five-fold bundle, is the inferential unit. V2 also adds information-matched normalization/T3A comparisons, source-only DANN, receiver-level inference, and label-dependent diagnostic stress tests that are kept out of the deployable-method table.

## What did not change

PR #84 remains immutable prior evidence. V2 does not edit its data, splits, checkpoints, predictions, summaries, or interpretation. V2 is a methodological remediation on the same WiSig ManyRx compact dataset, not an independent-dataset replication.
