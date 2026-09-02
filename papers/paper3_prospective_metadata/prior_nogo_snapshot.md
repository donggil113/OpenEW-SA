# Frozen Paper 3 static-relational NO-GO snapshot

## Status and immutability boundary

**VERIFIED FACT.** The relational-metadata feasibility audit was merged as PR #80 at commit `3b2159c897b58b538c05b01de2feb23c34fa8fac`. The static-relational M0–M2 pilot was merged as PR #81 at commit `b2b59d54515f601e5f88156a0d4adc38bbf77016`.

The completed pilot is frozen. **The next workstream is not a continuation or optimization of M0-M2.** It does not authorize a different context size, seed subset, relation combination, retention level, graph aggregator, target split, or M3/M4/M5 experiment.

## Exact scientific conclusions

- JamShield scenario holdout: **NO-GO**.
- JamShield reactive-family holdout: **NO-GO**.
- ElectroSense sensor holdout: **CONDITIONAL GO at most**.
- Overall static relational hypothesis: **NO-GO**.
- The shuffled-relation criterion failed for every protocol.
- Relation-retention behavior did not establish a reliable relational mechanism.
- Dynamic modeling remains **NO-GO**.
- Uncertainty-aware gating and neuro-symbolic extensions remain **PREMATURE** and were not started.

## Frozen headline macro-F1 results

Values are five-seed held-out means ± sample standard deviation.

| Frozen protocol | M0 | M1 | M2 |
|---|---:|---:|---:|
| JamShield scenario | 0.555165 ± 0.075781 | 0.480810 ± 0.028689 | 0.476876 ± 0.040576 |
| JamShield reactive family | 0.682252 ± 0.043125 | 0.659341 ± 0.040645 | 0.662984 ± 0.040606 |
| ElectroSense sensor | 0.452858 ± 0.033506 | 0.450970 ± 0.028290 | 0.446144 ± 0.045065 |
| DeepSense cross-day | 0.217815 ± 0.000767 | not eligible | not eligible |

Mean paired M2-minus-M0 held-out changes were -0.078289, -0.019267, and -0.006714 for JamShield scenario, JamShield reactive, and ElectroSense, respectively.

## Null and corruption controls

Actual-minus-shuffled M2 held-out differences were -0.018510 for JamShield scenario, -0.039320 for JamShield reactive, and +0.001947 for ElectroSense. None met the frozen requirement that actual relations exceed shuffled relations by at least 0.005 on both source validation and held-out data.

The held-out 0% to 100% relation-retention endpoint changed from 0.568432 to 0.476876 for JamShield scenario, from 0.704566 to 0.662984 for JamShield reactive, and from 0.450806 to 0.446144 for ElectroSense. Intermediate points were non-monotonic on held-out data and were not used to select a condition.

## Integrity status

**VERIFIED FACT.** The 140-run suite completed 140/140 runs with no failures. All 140 held-out prediction archives reconciled exactly to frozen sample IDs and recorded metrics. The Paper 1, Paper 2, and processed JamShield, DeepSense, and ElectroSense tree hashes matched before and after the pilot. Repository diffs for Paper 1 and Paper 2 were empty.

## New workstream question

The prospective workstream asks only:

> Can leakage-safe acquisition context be prospectively recorded and validated strongly enough to support a future relational or temporal RF domain-generalization experiment?

No result in this workstream may be used to reinterpret, tune, or rerun the completed M0–M2 pilot.
