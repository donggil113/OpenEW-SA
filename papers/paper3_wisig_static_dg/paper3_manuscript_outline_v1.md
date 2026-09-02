# Paper 3 manuscript outline v1

Working title: **Receiver-Context Domain Generalization for RF Fingerprinting**

Alternative title: **Context-Aware RF Fingerprinting Under Receiver and Acquisition-Day Shift**

The title and primary claim deliberately exclude dynamic, temporal-reasoning, hypergraph, neuro-symbolic, and uncertainty-gating language.

## Scientific question

Can target-neutral, unordered same-receiver context improve RF transmitter recognition under prespecified unseen-receiver domain shift, beyond independent encoders, capacity controls, generic pooled-context controls, and source-domain-generalization baselines?

## Contribution boundary

1. A leakage-audited adoption and conversion pipeline for the official WiSig ManyRx compact dataset, with opaque model-visible identifiers and strict acquisition/annotation separation.
2. Five frozen receiver-domain folds and four secondary acquisition-day folds, with receiver identity used only as an equality relation and day identity used only for splitting.
3. A shared compact RF encoder evaluated as independent P0, capacity-matched P0-WIDE, pooled receiver context P1, and permutation-invariant receiver-context attention P2.
4. Mandatory shuffled-context, null-context, retention, context-size, source-domain DG, and combined-shift controls.
5. Five-seed, five-fold reporting with receiver-fold clustered descriptive uncertainty and no best-run reporting.
6. A transparent contrast with the frozen PR #81 static-relational NO-GO result.

## Proposed structure

### 1. Introduction

- Receiver-induced domain shift in RF fingerprinting.
- Why independently classified packets omit deployment-available acquisition context.
- Why context must be audited for target leakage before modeling.
- Bounded contribution statement and explicit exclusion of temporal/dynamic claims.

### 2. Related work

- RF fingerprinting under receiver/channel shift.
- Source-domain generalization: CORAL and GroupDRO families.
- Set and context aggregation without receiver-value embeddings.
- Leakage and target-proxy risks in acquisition metadata.

### 3. Dataset qualification and protocol

- Official ManyRx compact provenance and CC BY-NC-SA 4.0 constraints.
- Ten-transmitter, 32-receiver, four-day compact subset.
- Deterministic two-pass conversion and full-sample QA.
- Receiver proxy audit and source-path quarantine.
- Five receiver folds, four leave-one-day-out folds, and secondary combined stress split.

### 4. Methods

- Shared residual 1-D CNN encoder and per-packet RMS normalization.
- P0 and capacity-matched P0-WIDE.
- DG-CORAL and DG-GroupDRO.
- P1 unordered same-receiver mean context.
- P2 permutation-invariant same-receiver attention.
- P2-SHUFFLED and P2-NULL.
- Fixed context-size and deterministic peer sampling contract.

### 5. Evaluation

- Primary unseen-receiver macro-F1; secondary accuracy, balanced accuracy, ECE, and per-domain metrics.
- Frozen seeds, source-validation checkpointing, and fail-closed run registry.
- Paired fold/seed comparisons and 2,000-replicate receiver-fold clustered descriptive bootstrap.
- Retention, size, mechanism, support, and compute diagnostics.

### 6. Results

- Primary P2 held-out macro-F1 `0.792544 +/- 0.045838` versus P0 `0.770749 +/- 0.048519`.
- P2-minus-P0 paired mean `+0.021795`, positive in all five receiver folds.
- P2-minus-P0-WIDE `+0.018610` and P2-minus-P2-SHUFFLED `+0.011210`.
- Secondary day result and neutral receiver-plus-day stress result.
- Non-monotonic retention and modest context-size sensitivity.
- Computational overhead and context diagnostics.

### 7. Discussion

- Evidence consistent with a bounded receiver-context advantage.
- Why the shuffled and capacity controls matter.
- Why the result does not imply causality, monotonic relation dependence, or universal receiver benefit.
- PR #81 as a disclosed cautionary contrast, not a hidden failed preliminary study.
- Distinction from Paper 1 benchmark construction and Paper 2 OOD scoring.

### 8. Limitations

- Official compact payload covers ten of 174 indexed transmitters and 32 of 41 indexed receivers.
- No validated timestamps and no temporal claim.
- P2 did not beat shuffled context in one fold.
- Combined receiver-plus-day stress result was neutral.
- Retention response was non-monotonic.
- Raw and converted payloads cannot be redistributed under the study policy without separate review.

### 9. Conclusion

- Static same-receiver context passed the preregistered bounded GO rule on ManyRx compact.
- The next scientific step is independent static replication, not a temporal/dynamic extension.

## Planned main displays

- Table 1: dataset and split summary.
- Table 2: primary receiver-holdout results.
- Table 3: DG and relational baselines.
- Table 4: paired receiver-context comparisons.
- Table 5: context controls.
- Figure 1: receiver-holdout macro-F1.
- Figure 2: P2-minus-P0 by receiver fold.
- Figure 3: P2 versus shuffled context.
- Figure 4: context-retention curve.
- Figure 5: secondary day-holdout results.
- Supplement: all fold/seed results, per-receiver results, support diagnostics, context-size sensitivity, and compute cost.
