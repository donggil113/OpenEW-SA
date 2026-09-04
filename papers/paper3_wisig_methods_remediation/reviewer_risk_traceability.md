# Reviewer-risk traceability for WiSig V2

Status: **COMPLETE — DESIGN FROZEN BEFORE TARGET-METRIC UNBLINDING**

This matrix records how V2 addresses the adversarial methods review of PR #84. It is a design trace, not a claim that the eventual result is positive.

| Review issue | V2 remediation | Auditable evidence | Residual limitation |
|---|---|---|---|
| P1/P2 were described too broadly as domain-generalization methods even though target-receiver packets were available at prediction time. | Separate R0 pure-inductive, R1 unlabeled receiver calibration/context, and R2 test-time adaptation. Scientific names are Mean Receiver-Context Conditioning and Attentive Receiver-Context Conditioning. | `scientific_reframing.md`, `information_budget_matrix.md`, frozen run-plan model registry | The unseen-receiver holdout is a domain-shift evaluation; P1/P2 remain test-time context methods, not pure DG. |
| PR #84 allowed queries to provide context for other queries. | Freeze 128 unlabeled support packets per receiver and seed by label-free sample-ID hash; evaluate only the disjoint remainder. No query-query interaction is permitted. | split manifests; blind-archive query-ID preflight; `context_receiver_seed_diagnostics.csv`; support/query overlap tests | WiSig has no verified deployment session. The bounded support bank is a calibration abstraction, not an observed episode. |
| Transmitter-specific source captures could confound context benefit with target composition. | Audit natural support composition after support IDs freeze; add transmitter-pure, same-class-excluded, and same-class-only oracle diagnostics. | `support_composition_audit.csv`, `composition_oracle_results.csv`, `target_proxy_postaudit_summary.json` | Oracle conditions use labels and are diagnostic-only. They cannot establish deployable performance. |
| Context methods were not compared with methods receiving equivalent unlabeled target information. | Compare P2 with RX-NORM and T3A using the identical 128 target-receiver support bank. Keep SOURCE-NORM as the paired normalization control. | `information_budget_matrix.md`; paired P2-minus-RX-NORM, P2-minus-T3A, and RX-NORM-minus-SOURCE-NORM rows | AdaBN and Tent are not applicable because the frozen backbone has no BatchNorm. Shuffled/mismatched controls use disclosed source-validation donors and are not exact same-target-information methods. |
| Five grouped folds were too coarse an inferential unit for unseen-receiver claims. | Use 32 leave-one-receiver-out protocols. Average five seeds inside each receiver, then bootstrap and sign-flip the 32 receiver differences. | `primary_receiver_averaged_results.csv`, `receiver_level_inference.json`, 10,000 receiver bootstrap replicates, 100,000 two-sided receiver sign flips | Hardware-family sensitivity has only three clusters and is secondary. Packet-level inference is prohibited. |

## Fail-closed gates

- Target annotations cannot enter support selection, context construction, model input, source checkpoint selection, or target-metric-blind execution.
- The shared bundle keeps annotations resident for source training, but executable target-label permutation tests require every blind prediction path to be invariant; `target_annotation_residency_clarification.md` defines the exact boundary.
- Every blind prediction archive must match its frozen query IDs, SHA-256, class dimension, and probability simplex before annotations are opened.
- Source-only selection of the strongest TTA and source-DG comparators uses equal-weight source-validation receiver macro-F1.
- Target unblinding requires all 2,080 primary records, one execution Git SHA, a clean committed worktree, and an immutable pre-unblinding manifest.
- GO/CONDITIONAL GO/NO-GO uses the rule frozen in `go_rule_operationalization.md`; target results cannot change a method, split, support budget, context size, class set, seed set, or receiver set.

## Interpretation boundary

Regardless of performance, V2 supports no temporal, dynamic, graph, hypergraph, or neuro-symbolic claim. A positive result would concern bounded test-time receiver-context conditioning under unseen-receiver shift. A negative or attenuated result remains valid evidence about PR #84's sensitivity to test-time information and support composition.

## Post-unblinding disposition

| Review issue | Verified V2 outcome | Residual reviewer risk |
|---|---|---|
| Information-regime conflation | R0, R1, and R2 remained separate in code, tables, and reporting. P2 is described only as test-time receiver-context conditioning. | The unseen-receiver protocol is a domain-shift evaluation, not evidence that P2 is a source-only DG method. |
| Query-query coupling | All 2,080 primary records passed disjoint 128-support/query verification; no query entered another query's support. | The support pool is still a constructed calibration abstraction rather than a verified acquisition episode. |
| Target-composition confounding | All natural banks contained six classes; same-class-excluded support retained full coverage and exceeded P0 by +0.020237, while same-class-only and transmitter-pure support were harmful. | Oracle conditions are label-dependent, post-hoc, and nondeployable. |
| Missing same-information TTA | T3A used the identical support bank and reached 0.833692 macro-F1 versus P2 at 0.806726. | No faithful additional RF-specific baseline was implemented where source/code details were insufficient. |
| Packet-level inference | Five seeds were averaged within each of 32 receivers before the fixed receiver bootstrap/sign flip. | Hardware-family sensitivity has only three clusters and remains secondary. |

The frozen decision returned `CONDITIONAL_GO`, but publication readiness is `NOT_READY`: P2-minus-P0 was +0.001047 with an interval crossing zero, only 15/32 receiver differences were positive, only one hardware-family mean was positive, and P2 was 0.026966 below T3A.

## Recovery trace

The power-loss recovery did not rerun any blinded condition. A final read-only reconciliation reproduced the pre-unblinding primary, day, and grouped prediction/checkpoint/history manifest hashes. The immutable pre-unblinding freeze was created from clean commit `da07219a018d4c10eb365e9cd2a847fe59520eda`, followed by one primary unblinding event at `2026-09-04T12:49:29.489216+00:00`.
