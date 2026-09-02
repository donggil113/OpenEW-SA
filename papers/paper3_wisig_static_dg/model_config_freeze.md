# Frozen WiSig model and training configuration

Status: **FROZEN BEFORE HELD-OUT EVALUATION**.

## Source-only evidence used

All eight model/control configurations completed the fold-0, seed-829 source-only smoke suite. Held-out metrics were disabled and are `null` in every run record. Training loss decreased in every configuration; checkpoint serialization/resume, finite-output gates, receiver episode construction, and target-prediction suppression passed. Peak allocated GPU memory was below 182 MB for the 16,384-packet smoke subset.

A subsequent full-source, source-validation-only profile used receiver fold 0 and seed 829:

| Model | Epochs | Best source-validation epoch | Best macro-F1 | Wall time | Target metrics |
|---|---:|---:|---:|---:|---|
| P0 | 20 | 19 | 0.741256 | 22.05 s | disabled |
| P2 | 20 | 16 | 0.752353 | 35.94 s | disabled |

The profile showed stable loss reduction and late source-validation maxima without memory pressure. It therefore supports a fixed maximum of 30 epochs and patience 8; this supplies headroom beyond the observed maxima while keeping the full preregistered suite feasible. This is a resource/stability decision, not a target-performance choice.

## Frozen representation and backbone

- Non-equalized 256×2 I/Q packet.
- Per-packet RMS normalization; no receiver, day, class, or target-test statistic.
- Compact shared residual 1-D CNN with 64-dimensional embedding.
- P0, P1, and P2 share the exact backbone.
- P0-WIDE has a wider independent head and matches P2 trainable parameters within 5%.
- P1 uses an unordered receiver-episode mean; P2 uses permutation-invariant learned attention pooling.
- No receiver-value embedding, day input, time/order encoding, or target-derived context.

## Frozen optimization

- AdamW, learning rate `5e-4`, weight decay `1e-4`.
- Maximum epochs 30; early-stopping patience 8.
- Checkpoint selection by source-validation macro-F1 only.
- Independent sample batch size 1,024.
- Context episode node budget 1,024, with primary context size 32.
- DG-CORAL source covariance weight 0.1.
- DG-GROUPDRO receiver-group step size 0.01.
- Seeds: 829, 1829, 2829, 3829, 4829.

## Frozen controls

Primary context size remains 32. Sizes 8 and 128 are secondary sensitivity conditions. Primary retention remains 100%; 75%, 50%, 25%, and 0% are reported as a curve. P2-SHUFFLED preserves partition and episode-size support while breaking receiver grouping without labels. P2-NULL preserves architecture and anchors with no peer context.

No held-out receiver/day result may change this configuration, the split, the eligible class set, the relation whitelist, the seed list, or the control definitions.
