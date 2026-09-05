# Receiver-adaptation benchmark results

Status: **VERIFIED RESULT — ONE-TIME UNBLINDING COMPLETE**

The benchmark answers a methods question, not a P2 rescue question: among frozen source-only and receiver-calibration methods, T3A is the strongest deployable method on WiSig V2. At the preregistered 128-packet information budget, T3A reaches receiver-equal macro-F1 0.833692 versus 0.805679 for P0. The paired gain is +0.028014 over 32 held-out physical receivers.

## Confirmatory result

Five seeds were averaged inside each receiver before inference. Receiver was the only inferential unit.

| Comparison | Mean delta | Median | Positive / negative receivers | 95% receiver bootstrap | Two-sided sign flip | Holm |
|---|---:|---:|---:|---:|---:|---:|
| T3A − P0 | +0.028014 | +0.024831 | 31 / 1 | [0.022011, 0.034661] | 0.000010 | 0.000010 |

The bootstrap used 10,000 receiver resamples. The fixed-seed Monte Carlo sign-flip used 100,000 permutations. The standardized mean paired difference is 1.502658.

## Receiver-equal primary table

| Method | Regime | Macro-F1 mean | Receiver SD | ECE | Interpretation |
|---|---|---:|---:|---:|---|
| SUP-FT-128 | R2 labeled oracle | 0.838081 | 0.081412 | 0.064833 | Diagnostic ceiling only |
| T3A | R1 unlabeled support | 0.833692 | 0.078929 | 0.102950 | Best deployable method |
| P2 | R1 unlabeled support | 0.806726 | 0.082039 | 0.108310 | Frozen benchmark entry; approximately P0 |
| P0 | R0 source only | 0.805679 | 0.084300 | 0.088851 | Independent ERM reference |
| DG-CORAL | R0 source only | 0.805071 | 0.082638 | 0.085345 | Approximately P0 |
| DG-DANN | R0 source only | 0.800926 | 0.084789 | 0.082895 | Below P0 |
| RX-NORM | R1 unlabeled support | 0.800769 | 0.086944 | 0.091891 | Below P0 at 128 |
| P0-WIDE | R0 source only | 0.801535 | 0.090017 | 0.099712 | Below P0 |
| DG-GroupDRO | R0 source only | 0.761754 | 0.078898 | 0.084448 | Materially below P0 |

SOURCE-NORM is the highest numerical source-only reference at 0.805976, only +0.000298 over P0 (16/32 receivers positive). This is a descriptive tie, not a new method claim.

The supervised oracle is +0.032402 over P0 and improves all 32 receivers. It is only +0.004388 above T3A and uses labels, so it is not a deployable comparator.

## Support-budget behavior

The query pool is common after reserving the maximum 256-sample support bank. The full prespecified curve is reported; no best budget is selected.

| Budget | P2 | T3A | RX-NORM |
|---:|---:|---:|---:|
| 0 | separate P2-NULL control | 0.805208 | SOURCE-NORM 0.805940 |
| 16 | 0.803529 | 0.719644 | 0.770090 |
| 32 | 0.806289 | 0.795558 | 0.788230 |
| 64 | 0.806618 | 0.822783 | 0.795680 |
| 128 | 0.806712 | 0.833617 | 0.800781 |
| 256 | 0.806788 | 0.838273 | 0.803270 |

T3A is harmful with only 16 packets and remains below the zero-support reference at 32. It becomes beneficial at 64, improves further at 128, and is highest descriptively at 256. P2 is nearly flat from 32 through 256. RX-NORM approaches but does not exceed SOURCE-NORM.

## Calibration and failure modes

Post-unblind probability diagnostics used frozen prediction archives; no inference was rerun.

| Method | NLL | Predictive entropy | ECE |
|---|---:|---:|---:|
| P0 | 0.630793 | 0.256117 | 0.088851 |
| P2 | 0.744285 | 0.197788 | 0.108310 |
| T3A | 0.501963 | 0.739732 | 0.102950 |
| SUP-FT-128 | 0.491053 | 0.258408 | 0.064833 |

T3A improves NLL and classification but has worse ECE than P0 and much higher predictive entropy. P2 is worse than P0 on NLL and ECE.

Catastrophic degradation was frozen as macro-F1 drop greater than 0.05 relative to matched P0. T3A and SUP-FT-128 have 0/160 receiver-seed catastrophic records. P2 has 22/160, RX-NORM 9/160, DG-CORAL 6/160, DG-DANN 7/160, and DG-GroupDRO 73/160.

## Hardware and receiver difficulty

T3A gains are positive in every descriptive hardware family: +0.032419 on B210 (7 receivers), +0.025349 on N210 (16), and +0.029325 on X310 (9). These three groups are too few for family-level generality claims.

The receiver-level T3A gain correlates 0.389 with P0 error; this post-hoc diagnostic suggests more difficult receivers often benefit more, but it is not causal evidence.

## Compute fairness

Frozen mean record times are 30.99 s for P0 source training, 98.30 s for P2 source training, 0.671 s for T3A support adaptation/evaluation, and 0.577 s for P2 context inference. SUP-FT-128 adapts only 390 classifier parameters and averages 0.689 s per receiver-seed record. P2 has 75,143 trainable parameters versus 64,774 for P0/T3A.

These measurements share hardware but represent different operations; training and test-time adaptation times must not be read as interchangeable latency benchmarks.

## Integrity

The create-once unblinding occurred at 2026-09-05T15:11:34.151668+00:00 from Git 3d523603d6558bcf7d9a8da5eb4d20b3528ae778. It consumed exactly 160 oracle and 160 budget records (1,280 new evaluations), all blind before joining labels. Frozen V2 hashes passed before execution. No P2, split, receiver, seed, or target-visible design changed.
