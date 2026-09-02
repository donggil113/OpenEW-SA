# Static receiver-context GO/NO-GO decision

Status: generated from the preregistered five-fold/five-seed receiver-holdout study. No target result changed the folds, class set, context definition, architecture, optimizer, seed list, controls, or decision criteria.

## Predeclared criteria

1. P2 must improve source-validation behavior reproducibly relative to P0.
2. Mean held-out receiver macro-F1 must not degrade by more than 0.01 absolute relative to P0.
3. P2 must show a reproducible advantage over label-independent P2-SHUFFLED.
4. P2 must show an advantage over capacity-matched P0-WIDE.
5. Benefit must not be confined to one receiver fold.
6. Every leakage and artifact-integrity gate must pass.

`GO` requires all six. `CONDITIONAL GO` is permitted only by the frozen executable rule when the leakage and non-degradation criteria pass and at least four total criteria pass. Otherwise the result is `NO-GO`.

## Verified criterion audit

| Criterion | Result | Frozen evidence |
|---|---|---|
| Source-validation reproducibility | PASS | P2 minus P0 mean `+0.021490`; fold means `+0.022784`, `+0.033941`, `+0.000558`, `+0.020796`, `+0.029373` |
| Held-out non-degradation | PASS | P2 `0.792544` versus P0 `0.770749`; mean delta `+0.021795` |
| Mechanism specificity | PASS | P2 minus P2-SHUFFLED mean `+0.011210`; positive in four of five folds |
| Capacity control | PASS | P2 minus P0-WIDE mean `+0.018610`; P2/P0-WIDE parameter difference `0.0212%` |
| Not confined to one fold | PASS | P2 minus P0 positive in all five receiver folds |
| Leakage and integrity | PASS | Acquisition/annotation separation, receiver-only relation, target-proxy gate, split isolation, raw/conversion hashes, and 530-run registry all passed |

## Descriptive uncertainty

| Paired comparison | Mean delta | Receiver-fold clustered 95% interval |
|---|---:|---:|
| P1 minus P0 | +0.006393 | [-0.000037, 0.011687] |
| P2 minus P0 | +0.021795 | [0.015220, 0.027729] |
| P2 minus P0-WIDE | +0.018610 | [0.010992, 0.026280] |
| P2 minus P1 | +0.015402 | [0.008399, 0.021558] |
| P2 minus P2-NULL | +0.005083 | [-0.000648, 0.010575] |
| P2 minus P2-SHUFFLED | +0.011210 | [0.004172, 0.017231] |

The 2,000-replicate interval resamples receiver folds as top-level clusters and preserves paired seed/model deltas inside each sampled fold. It does not treat packets as independent experimental units and is not used for a statistical-significance claim.

## Final verdict

**GO for the bounded static receiver-context hypothesis on WiSig ManyRx compact.** All six executable preregistered criteria passed without changing the target folds, class set, model family, context size, retention level, seeds, or decision rule.

This GO does not authorize a temporal, dynamic, hypergraph, uncertainty-gating, or neuro-symbolic stage. It supports proceeding to manuscript development and an independent static receiver-context replication. The claim must retain three negative/limiting observations: P2 did not beat shuffled context in receiver fold 2, retention was non-monotonic, and the combined receiver-plus-day stress protocol showed no P2 advantage over shuffled context.

Day holdout, receiver-plus-day stress, retention, and context-size results are secondary. They cannot reverse a primary receiver-context NO-GO or redefine the primary 32-sample/100%-retention condition.
