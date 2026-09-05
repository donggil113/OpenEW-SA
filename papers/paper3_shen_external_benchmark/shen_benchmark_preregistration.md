# Conditional Shen bounded receiver-support benchmark preregistration

Status: **FROZEN DESIGN, EXECUTION NOT AUTHORIZED**

This protocol becomes executable only after licence/access (Q0), deterministic
conversion (Q1), target-proxy safety (Q3), receiver/class support and split
integrity (Q4), frozen method transfer (Q5), and analysis/blinding (Q6) pass in
a clean committed review. The dataset does not satisfy the PR #86 acquired-
calibration-episode gate; this protocol makes no such claim.

## Question and information regime

Can a bounded, label-free support bank from an unseen physical receiver improve
transmitter identification on an independent LoRa corpus, and does the frozen
P2 attentive receiver-context method outperform the frozen same-information
T3A method? The support bank is a benchmark partition of released receiver
data, not a verified deployment episode.

## Eligibility and conversion

Use every verified physical receiver and transmitter class satisfying
pre-model completeness and support thresholds. Eligibility depends only on
physical receiver provenance, conversion integrity, and class support; no
receiver, class, or seed may be removed after target prediction. Conversion
must map a documented packet to exactly 256 consecutive complex samples by one
fixed target-independent crop/resample rule. Two passes must be numerically
identical. Exact source paths stay quarantined; model manifests use opaque IDs.

Acquisition metadata and annotations are separate. `receiver_id` is split and
support-addressing metadata only. `transmitter_id` is annotation-only. Day,
packet order, target-bearing paths, predictions, correctness, and receiver-
value embeddings are forbidden model/context inputs.

## LOSO splits and support/query rule

Every eligible physical receiver serves once as test. Three source-validation
receivers are chosen by a deterministic receiver-ID/hardware/support rule;
remaining receivers train the source model. Within the test receiver and seed,
rank eligible packets with the frozen V2 stable SHA-256 support primitive and
select 128 as support. All other eligible records are query. Support and query
are disjoint, and a query is never support for another query. P2 uses at most
32 support packets per query. Labels are absent from construction; permuting
labels must leave every ID unchanged.

## Frozen methods and controls

Transfer the merged V2 implementations and optimization exactly:

- P0 independent ERM;
- T3A with source-validation-only `filter_K` selection from
  `{1,5,20,50,100,-1}`;
- P2 attentive receiver-context conditioning;
- P2-SHUFFLED, breaking receiver correspondence without labels;
- P0-WIDE, P2-NULL, and P2-MISMATCHED-RX controls.

The only permitted classifier change is output dimension for the frozen
eligible transmitter count. Architecture, AdamW settings, 30-epoch maximum,
patience 8, support 128, context k 32, and seeds
`829,1829,2829,3829,4829` do not change. Source-only smoke may validate I/O,
loss, and checkpoints but cannot display target metrics.

## Blinding and inference

Target runs save blind predictions and cannot print/rank target metrics.
Unblinding occurs once after the complete receiver x seven-condition x five-
seed grid, immutable manifests, clean committed analysis code, and integrity
checks. Receiver is the inferential unit. Five seed differences are averaged
inside receiver before 10,000 receiver bootstrap replicates and 100,000 two-
sided sign flips. Holm correction covers exactly T3A-P0, P2-P0, P2-T3A, and
the optional mechanism comparison P2-P2-SHUFFLED.

## Predeclared decision

Receiver-support information is GO only if T3A or P2 has positive mean versus
P0, bootstrap lower bound above zero, Holm-adjusted sign-flip below 0.05,
positive difference on a receiver majority, and integrity PASS. P2 mechanism
GO additionally requires P2 above T3A under the same criteria. These thresholds
cannot be weakened after results.
