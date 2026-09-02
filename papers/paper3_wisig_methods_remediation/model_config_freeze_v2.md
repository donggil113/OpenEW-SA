# WiSig V2 model-configuration freeze

Status: **FROZEN AFTER SOURCE-ONLY SMOKE AND BEFORE TARGET PREDICTION**

The source-only smoke suite used `receiver_loso_00`, seed 829, a stable 16,384-packet source-training subset, the complete source-validation receivers, two epochs, and no held-out-receiver prediction or metric. All eight independently trained stages completed, all training losses decreased over the two smoke epochs, checkpoints were loadable, and no NaN/Inf or memory failure occurred.

| Stage | Source-validation macro-F1 (smoke diagnostic only) | Trainable parameters | Peak allocated GPU bytes | Wall seconds |
|---|---:|---:|---:|---:|
| P0 | 0.171184 | 64,774 | 166,521,344 | 2.295 |
| P0-WIDE | 0.125317 | 74,827 | 166,691,328 | 0.858 |
| DG-CORAL | 0.172184 | 64,774 | 166,521,344 | 3.103 |
| DG-GROUPDRO | 0.176118 | 64,774 | 166,521,856 | 1.427 |
| DG-DANN | 0.176531 | 70,754 | 166,468,096 | 0.842 |
| SOURCE-NORM | 0.171895 | 64,774 | 166,521,344 | 0.932 |
| P1 | 0.081404 | 73,030 | 189,601,792 | 5.788 |
| P2 | 0.047794 | 75,143 | 194,596,864 | 5.919 |

The abbreviated smoke scores are not scientific results or tuning outcomes. In particular, P2's low two-epoch source-validation score did not trigger an architecture, context, or optimizer change. Its source training loss fell from 2.056528 to 1.897510. Every configured method will retain the same full budget.

P0-WIDE differs from P2 by 316 trainable parameters, or approximately 0.42% of P2, satisfying the predeclared ±5% capacity criterion. The backbone contains zero BatchNorm modules, confirming that AdaBN and official Tent are not applicable without changing the frozen architecture.

## Final fixed configuration

- Backbone: PR #84 compact residual 1-D CNN with GroupNorm and 64-dimensional embedding.
- Input: 256 complex samples represented as real/imaginary channels.
- Standard preprocessing: per-packet RMS normalization, except the separately declared SOURCE-NORM/RX-NORM pair.
- Optimizer: AdamW.
- Learning rate: `5e-4`.
- Weight decay: `1e-4`.
- Maximum epochs: 30.
- Early-stopping patience: 8.
- Selection: source-validation receiver macro-F1 only.
- Packet batch size: 1,024.
- Context node budget: 1,056.
- Source context width: 33 nodes, yielding at most 32 peers per anchor; the anchor is excluded from its own peer set.
- CORAL coefficient: `0.1`.
- GroupDRO eta: `0.01`.
- DANN reversal coefficient: `0.1`.
- Primary target support budget / context `k`: 128 / 32.
- Seeds: 829, 1829, 2829, 3829, 4829.

No value above may change in response to V2 target performance.
