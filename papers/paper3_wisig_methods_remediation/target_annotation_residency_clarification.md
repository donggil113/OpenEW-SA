# Target-annotation residency clarification

Status: **RECORDED BEFORE TARGET-METRIC UNBLINDING**

The converted WiSig artifact correctly stores acquisition metadata and transmitter annotations in separate tables. The shared `ManyRxBundle` loader joins those tables into one in-memory object because source training and source-validation checkpoint selection require transmitter labels.

Consequently, the precise V2 statement is:

> Held-out transmitter annotations are resident in the shared loaded bundle, but no blind target support-selection, context-construction, adaptation, normalization, or prediction path indexes or receives them. Held-out annotations are first indexed after prediction freeze for the one-time metric and composition audit.

The narrower record field `target_labels_loaded_for_metrics=false` means that held-out labels were not accessed for metric computation during a blind run; it does not claim that annotation bytes were absent from process memory. Final reporting must retain this distinction.

## Executable safeguards

- Support and query IDs depend only on seed, receiver ID, and opaque sample ID.
- Context peers depend only on the frozen support bank and the same label-free identifiers.
- RX-NORM uses target support features only.
- T3A uses source logits, embeddings, and pseudo-labels only.
- P2-SHUFFLED and P2-MISMATCHED-RX use source-validation donor features and metadata only.
- Direct tests permute every target transmitter label while holding features and acquisition metadata fixed, then require bit-identical query ordering and probabilities for P0, P1, P2, P2-SHUFFLED, P2-MISMATCHED-RX, P2-NULL, RX-NORM, and T3A.

This clarification does not relax the leakage rule. Any target-label-dependent change in blind predictions is a suite-stopping violation. The post-unblinding transmitter-pure, same-class-excluded, and same-class-only contexts remain explicitly labeled oracle diagnostics and are never deployable methods.
