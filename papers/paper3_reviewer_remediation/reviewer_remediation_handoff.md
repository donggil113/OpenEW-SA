# Reviewer-remediation handoff
## VERIFIED RESULT
POST-HOC BASELINE-COMPLETENESS ADDENDUM, not independent confirmation.
Preregistration commit f30b658ff40f4d8ec3770be4c7c2b4692e5814da; scientific execution commit 028e4c770d65f25d8f85c913a267ad75788c0ba2.
Unblinding: 2026-09-06T00:43:28.133695+00:00; create-once.
All 2,400 records COMPLETE, zero failed: 480 reference-budget and 1,920 common-query budget records. No source model was retrained from scratch; frozen P0/P2 checkpoints were reused. Source-only oracle recipe simulation is separate from target evaluations. No P2 tuning, split replacement, receiver/seed deletion or RF download occurred.

| Method | Receiver-equal macro-F1 | Status |
|---|---:|---|
| P0 | 0.805679 | Frozen R0 |
| T3A | 0.833692 | Frozen R1 |
| P2 | 0.806726 | Frozen R1 |
| SAR-GN | 0.805684 | New bounded-support GN application |
| EMB-STD | 0.828490 | New simple source-aligned moment control |
| Head FT | 0.838081 | Frozen labeled diagnostic |
| Full FT | 0.921811 | New labeled diagnostic |

T3A remains the highest-mean unlabeled reference-budget method. SOURCE-NORM is the highest-mean source-only entry (0.805976); differences among source-only leaders are small and not a new inferential claim. EMB-STD improves all 32 receiver averages versus P0, mean delta 0.022812, interval [0.017466, 0.028406].
EMB-STD minus T3A is -0.005202; its narrow bootstrap interval excluding zero and exploratory sign-flip p=0.059369 are both retained. Do not select one to manufacture significance.

SAR is effectively P0: three positive, four negative, 25 equal receiver means. Its reference-budget execution has two steps, four SAM backward passes and average 1.83125 source recoveries; no empty reliable subset occurred. This qualifies the short-support application, not all SAR settings. SHOT is excluded for incompatible official source-training contract. Shen-GRL bridge is NO-GO, with no payload download.

## Probability quality
Raw T3A has ECE 0.102950, NLL 0.501963, Brier 0.236342, mean confidence 0.753708 and confidence-minus-accuracy -0.088751. Average underconfidence, not overconfidence, is the correct direction. ECE alone understated its better proper scores. Source-only temperature ECE is 0.047688, NLL 0.459254, Brier 0.223575. Argmax decisions are unchanged.

## INTERPRETATION
A simple feature-statistics control explains substantial available improvement, but it is not established as the causal explanation for every adaptation method. A much stronger labeled diagnostic invalidates the old near-ceiling wording. No new baseline rescues P2. Small support is a meaningful limitation for T3A; no budget is selected after results.

## Reproducibility and manuscript
New analysis package SHA256: b3989f7dad6b561957d7de887c100d7fe90f7baedf3119e5c7fb55c045568953. The portable evidence manifest maps every exported file to this immutable package. Thirty-one verified references, shared-source TMLCN/Access builds, all-receiver raw/scaled reliability and a payload-absent reproduction command are included. Official Access template dependencies remain external.
Timing-only replay covered all 32 receivers, seed 829, three repetitions for six methods; 576 records matched frozen probabilities. These are not new accuracy runs.

## UNRESOLVED
Single dataset, six-class task, constructed support rather than acquired episodes, overlapping LOSO source training, three hardware families, broader representation-changing baseline coverage, external data/license access, physical SDR validation, author/venue metadata and derivative release review remain open. Publication readiness remains CONDITIONAL.
