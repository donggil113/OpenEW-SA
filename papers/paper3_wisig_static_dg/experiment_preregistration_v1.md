# WiSig static receiver-context experiment preregistration v1

This protocol is frozen after conversion/QA and before any held-out receiver or day metric is computed.

## Question and scope

Does target-neutral same-receiver context improve RF transmitter recognition under unseen-receiver and unseen-day domain shift beyond independent RF encoders and source-only domain-generalization baselines?

This is static receiver-context domain generalization. It makes no temporal, dynamic, hypergraph, neuro-symbolic, or uncertainty-gating claim. Packet order is target-nested and forbidden as temporal context. Day is split-only.

## Data and primary endpoint

- Official ManyRx compact subset, non-equalized I/Q variant, 249,666 packets, ten transmitter targets, 32 receivers, four days.
- Primary protocols: five frozen unseen-receiver folds.
- Secondary protocols: four leave-one-day-out folds and one receiver+day intersection stress fold if compute permits.
- Primary endpoint: held-out receiver macro-F1.
- Secondary endpoints: accuracy, balanced accuracy, ECE, per-receiver macro-F1, per-day macro-F1.
- Checkpoint selection: source-validation macro-F1 only.

Target annotations are not loaded by context construction. Target metrics remain closed until the model configuration freeze commit.

## Frozen models

- **P0:** independent-sample compact 1-D RF CNN.
- **P0-WIDE:** capacity control within ±5% of P2 parameters.
- **DG-CORAL:** P0 plus source-receiver pairwise covariance alignment; no held-out data.
- **DG-GROUPDRO:** P0 with receiver-group robust source loss; no held-out data.
- **P1:** shared backbone; anchor embedding fused with the mean embedding of an unordered same-receiver context.
- **P2:** shared backbone; permutation-invariant attention over an unordered same-receiver context.
- **P2-SHUFFLED:** P2 with deterministic label-independent partition-local random groups of matched size.
- **P2-NULL:** P2 architecture with no peer information.

No receiver-value embedding is allowed. Models learn relation type behavior, not identities. P0/P1/P2 share the exact backbone. Only the context module differs.

## Context contract

- Relation whitelist: `receiver_id` only.
- Episode: unordered samples from the same receiver and the same train/validation/test partition.
- Primary size: 32, comprising the anchor plus up to 31 deterministic peers.
- Peer selection hash inputs: seed, opaque sample ID, and receiver ID. Labels, transmitter identity, packet order, day, and model outputs are absent.
- No context crosses split roles.
- No same-transmitter or same-class context.
- No positional or time encoding.
- Primary retention: 100%. Prespecified sensitivity: 75%, 50%, 25%, and 0%, with nodes/features preserved.
- Secondary context-size sensitivity: 8, 32, and 128. Size 32 remains primary regardless of result.

## Seeds and budget-selection rules

Seeds are exactly 829, 1829, 2829, 3829, and 4829. Python, NumPy, Torch, and CUDA are all seeded. No seed may be removed.

The maximum epoch count (not above 50), batch size, learning rate, and early-stopping patience (target 8) will be frozen after one source-only smoke run. Adjustments may use source stability, source-validation behavior, and memory only. Held-out metrics are forbidden during smoke and configuration selection.

## Primary and control suites

The primary receiver suite is 5 folds × 8 models × 5 seeds = 200 runs. The full day suite is 4 × 8 × 5 = 160 runs. Context retention is P2 only: 5 receiver folds × 5 levels × 5 seeds = 125 runs. Context size is P2 only: 5 folds × 3 sizes × 5 seeds = 75 runs. The stress protocol, if run, is P0/P1/P2/P2-SHUFFLED × 5 seeds = 20 secondary runs.

If source-only ETA exceeds 48 hours, execution priority is: (1) receiver primary suite, (2) shuffled/null controls already contained in it, (3) day suite, (4) retention, (5) size sensitivity, then stress. Scientific definitions do not change.

## Reporting and uncertainty

Report every seed and fold plus mean, standard deviation, median, minimum, and maximum. Paired descriptive differences match exact fold and seed for P1−P0, P2−P0, P2−P1, P2−P2-SHUFFLED, P2−P2-NULL, and P2−P0-WIDE.

Before results, hierarchical uncertainty is fixed as 2,000 paired bootstrap replicates over receiver folds as top-level clusters, preserving matched seed/model differences inside each sampled fold. Packets are not bootstrapped as independent units. Bootstrap intervals are descriptive; no significance claim is preregistered.

## Stop/go rule

Static receiver-context GO requires all of:

1. reproducible source-validation improvement for P2;
2. held-out receiver macro-F1 not degraded by more than 0.01 absolute versus P0;
3. reproducible advantage over P2-SHUFFLED;
4. advantage over P0-WIDE;
5. benefit not confined to one receiver fold;
6. no leakage or integrity gate failure.

Possible verdicts are GO, CONDITIONAL GO, and NO-GO. Negative folds and seeds are retained. A target-only gain cannot alter the frozen context, folds, models, or eligibility set.
