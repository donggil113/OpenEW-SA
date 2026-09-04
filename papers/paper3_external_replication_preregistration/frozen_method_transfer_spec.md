# Frozen P0/T3A/P2 method-transfer specification

Status: **FROZEN AT MERGED V2 COMMIT `48cec06645736bd45c455a64841f3f50e0368b40`**

## Transfer rule

The external replication imports the V2 scientific procedures unchanged. It
does not tune architecture, optimizer, support budget, context width, or T3A
candidate set using WiSig V2 or external target results. Dataset-specific work
is limited to deterministic conversion, label encoding, provenance, and the
acquisition-designed support/query adapter defined in
`calibration_episode_contract.md`.

Changing the output dimension from six to the preregistered eligible class
count is permitted because the existing constructors already take
`class_count`; hidden layers, normalization, pooling, attention, and training
budget do not change.

## Immutable code ledger

SHA-256 values were computed from the merged PR #85 tree before this branch
introduced any new file.

| Frozen artifact | SHA-256 |
|---|---|
| `src/openew/paper3/wisig/models.py` | `6c8a851b33d2f2fd4d215af09576a5a1567c6c145edd3109f93db79ac9eb40ae` |
| `src/openew/paper3/wisig_v2/models.py` | `37fa646b20c6468c473e020e9ec8884e0bc0d28ceb38458a955992d3140d9eeb` |
| `src/openew/paper3/wisig_v2/support.py` | `3511fe806a12a311173fdc21be52700bbfa75f66056aec723820c68a55b24c2d` |
| `src/openew/paper3/wisig_v2/runner.py` | `641e5db271c38876de58f57c1894d49b0658912cf3bcb76ce28cc42a9f2a1e35` |
| `src/openew/paper3/wisig_v2/contracts.py` | `85a0b04122da654dbbf4e3730e011ae053efa6bd340c15b22d77eaf72d8fb54a` |
| `src/openew/paper3/wisig_v2/hashing.py` | `7021a1c13f52457fa7294f8e911da03dd17bb82169d2e896e0653d071159437d` |
| `configs/paper3/wisig_v2/methods_v2.yaml` | `2a224d4f25ee6f98a01a92dbec5b5c972f2097d2db07114d4559d0390cb872d0` |
| V2 preregistration | `9508282ac7d6cdc9915e5fadf278335088c500c705753a3755585af369c431d4` |
| V2 model freeze | `1817e7fc7d4da510693ab0b5ce1c5f29bc299fbe1d7baa12f8c6b390eeace04c` |

The future run manifest must reproduce this ledger or record an integrity
failure. No code in the frozen WiSig or WiSig V2 directories may be edited for
the replication.

## P0: Independent ERM

- Input: 256 complex samples represented as `[256, 2]` real/imaginary values.
- Preprocessing: the exact V2 per-packet RMS normalization.
- Encoder: compact 1-D residual CNN with GroupNorm and 64-dimensional embedding.
- Classifier: one linear `64 -> C` layer.
- Information regime: trained source model plus query packet only; zero target
  support at inference.
- Parameterization changes only through `C`, the frozen eligible class count.

## P2: Attentive Receiver-Context Conditioning

- Same RF backbone and per-packet preprocessing as P0.
- Attention scorer: `64 -> 32 -> 1` with `tanh`.
- Masked softmax over support embeddings; no position or time encoding.
- Fusion: concatenated 64-dimensional anchor and context representations,
  followed by `128 -> 64`, ReLU, dropout `0.2`, and `64 -> C`.
- No receiver-value, day, campaign, hardware, site, class, or episode embedding.
- Primary target support bank: 128 unlabeled packets from the held-out
  receiver's acquisition-designated calibration episode.
- Primary peers per query: 32, selected by the frozen stable-hash rule.
- Query packets never become support.

Source P2 training retains the V2 procedure exactly: all source-training
packets may be anchors and deterministic receiver-local chunks have width 33
(anchor plus at most 32 peers). Chunks remain partition-local but are not
redefined from acquisition episodes. Episode boundaries govern the held-out
receiver's acquired calibration/query separation; they are not a new learned
input or a post-V2 training relation.

## T3A: Test-Time Template Adjustment

- Start from the receiver-specific reset of the frozen P0 checkpoint.
- Use the same 128 unlabeled calibration packets available to P2.
- Initialize templates from the linear classifier weights, append calibration
  embeddings, pseudo-label with the source classifier, rank by prediction
  entropy within pseudo-class, form normalized prototypes, and classify
  disjoint queries by normalized prototype similarity.
- No gradients and no target labels.
- `filter_K` candidates remain exactly `{1, 5, 20, 50, 100, -1}`.
- Selection uses source-validation receiver calibration/query simulations only,
  separately inside each LOSO protocol. External target receiver metrics cannot
  select or revise `filter_K`.

## Frozen optimization and seeds

| Item | Value |
|---|---|
| Optimizer | AdamW |
| Learning rate | `5e-4` |
| Weight decay | `1e-4` |
| Maximum epochs | 30 |
| Early-stopping patience | 8 |
| Checkpoint selection | source-validation receiver macro-F1 only |
| Packet batch size | 1,024 |
| Context node budget | 1,056 |
| Source context width | 33 |
| Support budget / context k | 128 / 32 |
| Seeds | 829, 1829, 2829, 3829, 4829 |

No support-budget or context-k sensitivity suite is part of the replication.

## Deterministic input adapter

The source format may differ, but conversion must be frozen before labels are
opened for proxy/support auditing. A documented physical frame/burst detector
must locate a packet independently of its class, and a fixed rule must extract
exactly 256 consecutive complex samples. Cropping offset, filtering,
resampling, synchronization, and quality thresholds are fixed using acquisition
specification, source-only QA, and source-validation simulation only.

If scientifically valid conversion to the frozen input is impossible, the
candidate fails. The architecture is not changed to rescue it.

## Pre-execution code freeze

Before future training, commit the converter/adapter, run its tests, record its
code-tree SHA-256, record the V2 ledger above, freeze the exact split and
support manifests, and require a clean worktree. Target predictions remain
blinded until every preregistered run is complete.
