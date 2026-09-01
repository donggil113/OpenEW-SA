# Static relational M2 pilot: predeclared GO/NO-GO report

## Decision summary

**VERIFIED RESULT — Overall Paper 3 verdict: NO-GO for the tested static relational hypothesis.**

| Frozen protocol | Verdict | A: source-validation support | B: held-out non-degradation | C: actual over shuffled | D: interpretable retention |
|---|---|---:|---:|---:|---:|
| JamShield scenario holdout | NO-GO | Fail | Fail | Fail | Fail |
| JamShield reactive-family holdout | NO-GO | Fail | Fail | Fail | Fail |
| ElectroSense sensor holdout | CONDITIONAL GO | Pass | Pass | Fail | Pass |

The overall rule declared before target evaluation requires all protocols to be GO for an overall GO, or at least one GO/two CONDITIONAL GO verdicts for an overall CONDITIONAL GO. Two protocols are NO-GO and one is CONDITIONAL GO; the automatic classification is therefore **NO-GO**.

No significance claim is made. All differences below are descriptive, seed-matched results for seeds 829, 1829, 2829, 3829, and 4829.

## Frozen decision rules

The committed protocol defined four tests:

- **A — source-validation support:** mean M2 minus M0 source-validation macro-F1 must be positive in five paired seeds, with a positive difference in at least three seeds.
- **B — held-out non-degradation:** mean M2 minus M0 held-out macro-F1 must be at least -0.01.
- **C — relation specificity:** actual M2 must exceed shuffled M2 by at least 0.005 on both source validation and the held-out partition.
- **D — interpretable retention:** the source-validation relation-retention curve must meet the frozen rank/endpoint rule.

The held-out partitions were opened only after the design, context size, model budgets, seeds, controls, and automatic rule were committed in `bc68b079f3a1c51b449b82876f1e8f02ebe17105`.

## Protocol evidence

### JamShield scenario holdout — NO-GO

**VERIFIED RESULT.** M2 changed mean source-validation macro-F1 by **-0.003094** and held-out macro-F1 by **-0.078289** relative to M0. The mean held-out scores were M0 **0.555165**, M1 **0.480810**, and M2 **0.476876**. Thus M2 exceeded the allowed degradation by a wide margin.

Actual M2 was below shuffled M2 by **0.002616** on source validation and **0.018510** on the held-out partition. The source-validation retention Spearman coefficient was **-0.900000**, and full-minus-zero retention was **-0.002999**. All four rules failed.

**INTERPRETATION.** Station-equality aggregation did not provide reproducible relational value on this frozen protocol. Removing incidences performed better on average than retaining all incidences, and shuffled grouping was not worse than actual grouping.

### JamShield reactive-family holdout — NO-GO

**VERIFIED RESULT.** M2 changed mean source-validation macro-F1 by **-0.003336** and held-out macro-F1 by **-0.019267** relative to M0. Mean held-out scores were M0 **0.682252**, M1 **0.659341**, and M2 **0.662984**. Criterion B failed because degradation was greater than 0.01.

Actual M2 was below shuffled M2 by **0.001812** on source validation and **0.039320** on the held-out partition. The source-validation retention Spearman coefficient was **-1.000000**, and full-minus-zero retention was **-0.002627**. All four rules failed.

**INTERPRETATION.** Station grouping again behaved as a nuisance or confounded pooling structure rather than a useful invariant relation.

### ElectroSense sensor holdout — CONDITIONAL GO

**VERIFIED RESULT.** M2 changed mean source-validation macro-F1 by **+0.004292** and held-out macro-F1 by **-0.006714** relative to M0. Mean held-out scores were M0 **0.452858**, M1 **0.450970**, and M2 **0.446144**. Criteria A and B passed.

Actual M2 exceeded shuffled M2 by only **0.003605** on source validation and **0.001947** on the held-out partition, below the frozen 0.005 margins; criterion C failed. The source-validation retention Spearman coefficient was **+1.000000**, and full-minus-zero retention was **+0.004165**; criterion D passed.

**INTERPRETATION.** Receiver/date equality structure affected source fitting in an orderly way, but the pilot did not establish relation-specific held-out benefit. This is conditional mechanism evidence, not a basis for selecting a favorable relation component from target results.

## Null relation and corruption controls

**VERIFIED RESULT.** Mean shuffled-control held-out macro-F1 was **0.495386** for JamShield scenario, **0.702304** for JamShield reactive, and **0.444197** for ElectroSense. Actual full-relation M2 was lower by 0.018510 and 0.039320 on the two JamShield protocols, and higher by only 0.001947 on ElectroSense.

The held-out relation-retention curves were non-monotone. From 0%, 25%, 50%, 75%, to 100% retention, the mean scores were:

- JamShield scenario: 0.568432, 0.598605, 0.614393, 0.536988, 0.476876.
- JamShield reactive: 0.704566, 0.706112, 0.679284, 0.680369, 0.662984.
- ElectroSense: 0.450806, 0.458260, 0.442196, 0.465086, 0.446144.

These curves were not used to select a retention level.

## Scientific decision

**INTERPRETATION.** Static relational learning with the currently audited equality metadata is not supported as the central Paper 3 contribution. The negative result is driven by source-validation failures and null-control equivalence/adversity, not merely by an unfavorable target score.

**UNRESOLVED.** ElectroSense component-only target means vary, but they cannot be selected retrospectively. A separately designed experiment would require a new source-only rationale and freeze; the present pilot provides no authorization to do so.

## Next step

Do not start M3 dynamic modeling, M4 uncertainty gating, or M5 symbolic constraints. First establish a prospective acquisition protocol with non-target-derived session/order/channel metadata and enough within-partition relation diversity. Re-audit that metadata and freeze a new question before any further relational model training.
