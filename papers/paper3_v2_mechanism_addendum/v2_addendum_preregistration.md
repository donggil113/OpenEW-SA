# WiSig V2 post-hoc mechanism-addendum preregistration

Status: **POST-HOC MECHANISTIC ADDENDUM; FROZEN BEFORE ADDENDUM EXECUTION; NOT PART OF THE V2 PRIMARY DECISION**

## Immutable prior result

PR #85 merge `48cec06645736bd45c455a64841f3f50e0368b40` is prior,
immutable evidence. Receiver-level macro-F1 was P0 `0.805679`, P2 `0.806726`,
and T3A `0.833692`; P2-P0 was `+0.001047` with receiver bootstrap
`[-0.006660, 0.008857]`, sign-flip approximately `p=0.79`, and 15/32 positive
receivers. P2-shuffled was `+0.018364`, P2-mismatched was `+0.019637`, and
P2-T3A was `-0.026966`. Publication readiness remains `NOT_READY`.

The addendum cannot change splits, classes, seeds, architectures, trained V2
checkpoints, primary P2 settings, V2 inferential family, or that verdict.
Results are receiver-level exploratory summaries, not confirmatory evidence.

## A. Query-coupling diagnostic

Reuse frozen V2 P2 checkpoints for all 32 LOSO receivers and five seeds; do not
retrain. Compare:

- A1, frozen disjoint support/query reference (128 support, k=32);
- A2, PR #84-style query-coupled deterministic receiver chunks, width 33
  (anchor plus at most 32 peers), allowing query packets to provide unlabeled
  context to other queries; and
- A3, full receiver-partition upper diagnostic, with every available same-
  receiver support/query packet eligible as unordered context and attention
  evaluated from cached embeddings to avoid quadratic materialization.

No label selects context. A2/A3 are nondeployment information-access
diagnostics. Primary quantity: receiver-averaged macro-F1 delta from A1.

## B. Shuffled-context source training

Train one new P2 source model per 32 LOSO receiver and five seeds using the
exact frozen V2 architecture, optimizer, epochs, patience, source-validation
selection, and splits. The only declared change is label-free deterministic
shuffling of source context donors across source receivers within the training
partition. Evaluate each checkpoint with natural matched receiver support,
shuffled support, and null support. No target result selects a checkpoint or
configuration. This is post-hoc mechanism evidence, not a replacement model.

## C. Composition/TTA stress

Reuse frozen P2/P0 checkpoints and adapters. Evaluate P2, T3A, and RX-NORM on
the same query IDs under natural support plus same-class-excluded, same-class-
only, and transmitter-pure support. The final three use annotations and are
**ORACLE DIAGNOSTIC ONLY / NONDEPLOYABLE**. T3A `filter_K` stays the original
source-validation choice. Report whether composition sensitivity is unique to
P2 and whether T3A remains strongest; do not optimize from these results.

## D. Equalized sample-intersection gate

First recompute the exact opaque sample-ID intersection between raw V2 and both
equalized conversion passes. Report intersection and side-only counts, per-
receiver/class coverage, and LOSO split coverage. Run the matched-intersection
P0/T3A/P2 diagnostic only if all 32 receivers, all six frozen classes, each
test support bank of 128, and at least 80% of every receiver's raw eligible
queries survive, both equalized passes agree, and no proxy/integrity check
fails. Otherwise report `INELIGIBLE`; never replace V2 primary results.

## E. Support-budget efficiency

Using frozen checkpoints, compare T3A and P2 at complete bank sizes
16, 32, 64, 128, and 256 for all 32 receivers and five seeds. P2 k is
`min(32, budget)`; T3A uses the same bank. Budget 128 remains the reference.
Do not select or recommend a best target budget from this curve.

## F. Receiver hardware families

Use only verified V2 hardware-family metadata. Summarize receiver-level P2-P0,
T3A-P0, and P2-T3A by family. Three families are descriptive and cannot support
primary family-level inference. Hardware identity is never a model feature.

## Statistics and reporting

Seeds are exactly `829,1829,2829,3829,4829`. Average seed-matched deltas within
each receiver. Report equal-weight receiver mean, 10,000 fixed-seed receiver
bootstrap interval, and receiver-positive count. No new confirmatory p-value
family is introduced; any optional p-value is explicitly exploratory. Packets
are never bootstrap units. No receiver/seed/condition is removed for outcome.

Every output is tagged one of:

- `DEPLOYABLE_METHOD`: A1/natural label-free support;
- `LABEL_FREE_CONTROL`: A2/A3, shuffled, mismatched, null, or budget changes;
- `ORACLE_DIAGNOSTIC`: label-dependent composition conditions.

Generated outputs are create-once or hash-manifested in
`/mnt/d/openew_sa_data/paper3/v2_addendum/`; frozen V2 files are read-only
inputs and must hash identically before and after execution.
