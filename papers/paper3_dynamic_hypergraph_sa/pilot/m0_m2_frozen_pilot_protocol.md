# Frozen Paper 3 Static-Relational M0--M2 Pilot Protocol

Status: **FROZEN BEFORE HELD-OUT EVALUATION**. This protocol may be changed only for a documented source-only stability, integrity, or resource failure. Held-out performance must never motivate a change.

## Scientific question and scope

Can deployment-available static equality relations improve RF situation assessment under the unchanged Paper 1 scenario, jammer-family, and sensor holdouts without target-domain label leakage?

The working direction is **Relational Domain Generalization for RF Situation Assessment**. This pilot does not implement or claim dynamic, temporal, uncertainty-gated, or neuro-symbolic reasoning.

## Frozen artifacts and holdouts

- JamShield: `/mnt/d/openew_sa_data/processed/jamshield`; Paper 1 scenario holdout and reactive-jammer-family holdout, including `data_benign_4` in each held-out evaluation partition.
- ElectroSense: `/mnt/d/openew_sa_data/processed/electrosense`; Paper 1 sensor holdout with `alcorcon1`, `bcn-L`, and `Geneva` held out.
- DeepSense: `/mnt/d/openew_sa_data/processed/deepsense`; Paper 1 day-1 to day-2 cross-day holdout, M0 only.

`domain_id` is split-only and never enters a model or relation constructor. The exact source artifacts and frozen Paper 1/Paper 2 trees are content-hashed before and after the suite.

## Source-only validation split

After applying the unchanged Paper 1 held-out predicate, each remaining source partition is subdivided into 80% training and 20% source validation. Within each source-domain/target-class stratum, samples are ordered by SHA-256 of `dataset | protocol | domain | symbolic target | sample_id | 20260901`; the first rounded 20%, with nonempty train and validation safeguards, form source validation. Target-class values are used only for this source-side stratification and supervised loss, never for relations. This split is identical for every model and seed.

## Frozen relation contract

```yaml
jamshield: [rx_id]
deepsense: []
electrosense: [rx_id, source_date_id]
```

Allowed relation types are:

- JamShield: `station` from equality of `rx_id`.
- ElectroSense M1: `receiver` from `rx_id` and `date` from `source_date_id`.
- ElectroSense M2: `receiver`, `date`, and joint `receiver_date`.
- DeepSense: no relation.

Frequency, capture/file/path, scenario, target, OOD, correctness, prediction, held-out performance, and split identifiers are forbidden relation sources. Relation values are equality operators only; no categorical value embedding is learned. An unseen receiver therefore requires no train-seen identity.

## Deployment context contract

A context episode is one deterministic relation-type equality-group chunk constructed independently inside train, source-validation, or held-out partitions. No episode crosses a partition. Raw equality groups are sorted by SHA-256 of `dataset | relation type | relation value | sample_id | seed` and divided into chunks of at most **64 observations**. The limit of 64 is frozen from pre-run group-size and memory profiling, not target performance: verified groups contain up to 24,823 JamShield observations and 15,000 ElectroSense observations, so uncapped equality contexts are not operationally defensible.

For nodes with multiple allowed relation types, M2 obtains one independently bounded message per relation type and combines relation-type transformations. Each individual episode remains at most 64 nodes. Held-out inference is explicitly contextual/transductive only within these bounded, acquisition-plausible equality episodes; the entire held-out set is never treated as one graph.

Groups larger than 64 are chunked by the stable hash rule. This avoids row-order or temporal assumptions. All sample IDs are preserved. Coverage, isolation, group sizes, and truncation are serialized for every run.

## Frozen models

### M0: independent-sample control

- JamShield: standardized 37-feature MLP, hidden width 128, ReLU, dropout 0.1, linear task head.
- ElectroSense: standardized 512-bin PSD MLP with the same hidden width, activation, dropout, and head pattern.
- DeepSense: the existing Paper 1 compact 1-D I/Q CNN family (`2 x 1024` input), M0 only.

The tabular/PSD node encoder follows the Paper 1 MLP capacity. Input BatchNorm is omitted uniformly from M0/M1/M2 because features are already standardized on source training rows and relation-composed minibatches would otherwise make BatchNorm a relation-dependent confound.

### M1: pairwise relation graph

M1 uses the identical node encoder and task head as M0. For each anchor, it computes the mean of other nodes in each bounded equality chunk without materializing pairwise edges. A learned transformation is specific to relation type, never relation value. The transformed messages are averaged and added residually to the anchor embedding.

### M2: static typed hypergraph

M2 uses the identical node encoder and task head. Node-to-hyperedge reduction is the mean of all retained incidences in a bounded typed hyperedge, including the anchor. Relation-type-specific transformations remain distinct, are averaged across available types, and update the node residually. Incidence/group reduction is implemented directly in PyTorch; no clique expansion or PyTorch Geometric dependency is used.

An equality chunk of size one is treated as isolated and contributes no relational update for both M1 and M2.

## Frozen optimization and seeds

- Seeds: `829`, `1829`, `2829`, `3829`, `4829` for Python, NumPy, Torch, and CUDA.
- Epochs: 10; source-validation macro-F1 selects the best epoch.
- Optimizer: AdamW, learning rate `0.001`, default weight decay `0.01`.
- Batch sizes: JamShield 64; ElectroSense 128; DeepSense 128.
- Standardization: mean and scale fitted on source-training rows only.
- Loss: balanced source-training class weights for JamShield; unweighted cross-entropy otherwise, matching the Paper 1 configs.
- Determinism: seeded loaders and context construction; deterministic algorithms enabled where supported; completed metadata records the device and runtime.

M0/M1/M2 receive the same encoder capacity, epoch count, learning rate, split, seeds, and anchor-example budget. Relational stages may process additional context-support nodes; that cost is measured rather than hidden.

## Target-label firewall

Held-out relation plans and probabilities are constructed without reading held-out targets. Predictions and class probabilities are atomically frozen first. Only then are held-out labels read for metrics and appended to the final prediction table. Any label-dependent relation incidence, partition crossing, source-hash mismatch, or forbidden-field request is a suite-stopping scientific integrity violation.

## Frozen primary and diagnostic matrix

- Primary: JamShield scenario M0/M1/M2; JamShield reactive M0/M1/M2; ElectroSense sensor M0/M1/M2; DeepSense cross-day M0, all five seeds (50 runs).
- Null control: M2 with independently shuffled relation values within each partition, preserving each relation type's group-size multiset, all five seeds for the three relational protocols.
- Corruption: M2 at 100%, 75%, 50%, 25%, and 0% deterministic label-independent incidence retention for the three relational protocols. The 100% condition reuses primary M2 and 0% is the relation-removed M2 control.
- Ablations: JamShield station/full versus no relation (already represented by 100%/0%); ElectroSense full, receiver only, date only, joint only, and no relation.

Equivalent configurations are executed once and reused in each applicable summary. The deduplicated full plan contains 140 runs.

## Metrics and reporting

Primary endpoint: held-out macro-F1. Secondary endpoints: balanced accuracy, accuracy, per-domain macro-F1, and 15-bin ECE. Reports include all five seeds plus mean, sample standard deviation, median, minimum, maximum, seed-matched descriptive deltas, relation diagnostics, wall time, throughput, parameter count, peak CUDA memory, and peak process resident memory where available. No significance claim or inferential test is planned.

## Predeclared protocol verdict rules

For each relational protocol:

1. **Validation support (A):** M2 minus M0 has positive mean source-validation macro-F1 and is positive for at least three of five paired seeds.
2. **Held-out non-degradation (B):** mean held-out M2 minus M0 is at least `-0.010000` absolute macro-F1.
3. **Meaningful structure (C):** actual M2 exceeds shuffled M2 by at least `0.005000` mean macro-F1 on both source validation and held-out evaluation. If the absolute gap reaches `0.005000` but signs differ, this criterion is heterogeneous rather than passed.
4. **Retention interpretability (D):** the five retention-level means are complete and the source-validation Spearman correlation between retention and macro-F1 is at least `0.5`, or full-minus-zero source-validation macro-F1 is at least `0.010000` with at least three of four adjacent retention changes nonnegative.

Protocol verdict:

- **GO:** A, B, C, and D pass.
- **CONDITIONAL GO:** B passes and at least two of A, C, and D pass; heterogeneous C counts as one conditional signal only when A also passes.
- **NO-GO:** all other cases.

Overall verdict:

- **GO:** all three relational protocols are GO.
- **CONDITIONAL GO:** at least one protocol is GO, or at least two are CONDITIONAL GO, with no integrity failure.
- **NO-GO:** otherwise.

Target-only gains cannot redesign this pilot. Regardless of outcome, M3/M4/M5 are not started automatically.

## Source-only smoke gate

Before this protocol/configuration is committed, seed 829 runs abbreviated source-only M0/M1/M2 smoke checks for JamShield and ElectroSense. Held-out metrics remain disabled. The smoke gate verifies finite forward/loss values, decreasing source training loss, checkpoint and prediction serialization, bounded contexts, and resume compatibility. Only source stability or resource limits may motivate a documented configuration adjustment.
