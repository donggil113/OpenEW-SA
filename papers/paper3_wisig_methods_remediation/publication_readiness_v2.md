# WiSig V2 publication-readiness assessment

Status: **COMPLETE**

Verdict: **NOT_READY**

## Decision boundary

The readiness verdict is distinct from the frozen mechanism rule. That rule returned `CONDITIONAL_GO` because P2-minus-P0 was strictly positive and integrity/disjointness passed, despite three failed mechanism criteria. Publication readiness additionally considers effect magnitude, uncertainty, comparison with same-information TTA, deployment realism, and contribution strength.

## VERIFIED RESULT

| Domain | Evidence | Assessment |
|---|---|---|
| Novelty | Explicit separation of source-only DG, test-time receiver context, and TTA; disjoint support/query design | Methodological framing is useful but the P2 contribution is not yet strong |
| Effect size | P2 0.806726 versus P0 0.805679; delta +0.001047, bootstrap interval [-0.006660, 0.008857] | Too small and uncertain for a P2 performance claim |
| Receiver robustness | 15/32 receivers positive; family means positive only for X310 | Majority-receiver and multiple-family criteria failed |
| Capacity control | P2-minus-P0-WIDE +0.005191; interval [-0.003300, 0.013471] | Descriptively positive, uncertain |
| Mechanism specificity | P2-minus-shuffled +0.018364 and P2-minus-mismatched +0.019637 | Strong evidence that receiver-matched support matters to P2 |
| Same-information TTA | T3A 0.833692; P2-minus-T3A -0.026966, interval [-0.038002, -0.016769] | P2 is clearly inferior to the strongest preregistered TTA |
| Composition confounding | Same-class-excluded remained +0.020237 over P0; homogeneous oracle contexts were harmful | Benefit is not driven only by same-class exposure |
| Source-only baselines | P0 0.805679; DG-CORAL 0.805071; DG-DANN 0.800926; DG-GROUPDRO 0.761754 | Added source-DG methods did not improve P0 |
| Secondary robustness | Day: P2 0.876531 versus P0 0.869983; grouped: 0.732534 versus 0.730877 | Small descriptive advantages only; day is not temporal |
| Information fairness | P2 and T3A use the identical 128-packet unlabeled target-receiver bank | PASS |
| Compute fairness | Median standardized latency: P2 0.557081 s, P0 0.020513 s, T3A 0.024697 s | P2 has substantially higher test-time cost |
| Statistical rigor | Receiver is the unit; seeds averaged within receiver; fixed 10,000 bootstrap and 100,000 sign flips; fixed Holm family | PASS |
| Deployment realism | Support/query are bounded and disjoint, but WiSig has no verified calibration episode | Important residual limitation |
| License/reproducibility | Code, splits, and hashes are releasable; RF payload remains external under CC BY-NC-SA 4.0 | Manageable but constraining |
| Integrity | Paper 1/2, PR #80--#84, raw archive, conversions, and 2,520 blind records reverified | PASS |

## INTERPRETATION

V2 is a rigorous and useful negative/attenuation result, but the current evidence does not justify a manuscript centered on Attentive Receiver-Context Conditioning as the superior solution. T3A is both more accurate and far less expensive at test time, while P2's advantage over P0 is practically near zero and not supported across a receiver majority or multiple hardware families.

The context-control findings are scientifically informative and should be retained as a cautionary methods record. They may support a future paper only when combined with an independently collected or external dataset that has verified receiver-calibration episodes and a prospectively frozen comparison.

## Title gate

No Paper 3 manuscript title is recommended for submission from V2 alone. If a future independent study supplies the missing deployment evidence, an accurate provisional title is:

> Unlabeled Receiver Calibration for RF Fingerprinting Under Unseen-Receiver Shift: Context Conditioning Versus Test-Time Adaptation

No V2 manuscript outline is created because the readiness verdict is `NOT_READY`.

## Required next evidence

- Prospectively recorded, target-neutral receiver-calibration sessions with explicit episode boundaries.
- Independent evaluation of fixed P2 and T3A procedures without V2-driven tuning.
- Evidence that any revised context method improves both P0 and same-information TTA across receivers and hardware families.
- A release plan compatible with RF-payload licensing and reproducible split reconstruction.
