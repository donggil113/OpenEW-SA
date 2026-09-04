# Reviewer-risk traceability for WiSig V2

Status: **FROZEN BEFORE TARGET-METRIC UNBLINDING**

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
