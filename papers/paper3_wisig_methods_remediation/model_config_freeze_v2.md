# WiSig V2 model-configuration freeze

Status: **FROZEN AFTER SOURCE-ONLY SMOKE AND BEFORE TARGET PREDICTION**

The source-only smoke suite used `receiver_loso_00`, seed 829, a stable 16,384-packet source-training subset, the complete source-validation receivers, two epochs, and no held-out-receiver prediction or metric. All eight independently trained stages completed, all training losses decreased over the two smoke epochs, checkpoints were loadable, and no NaN/Inf or memory failure occurred.

| Stage | Source-validation macro-F1 (smoke diagnostic only) | Trainable parameters | Peak allocated GPU bytes | Wall seconds |
|---|---:|---:|---:|---:|
| P0 | 0.244446 | 64,774 | 166,500,864 | 2.170 |
| P0-WIDE | 0.232316 | 74,827 | 166,664,704 | 0.796 |
| DG-CORAL | 0.244109 | 64,774 | 166,500,864 | 2.322 |
| DG-GROUPDRO | 0.249975 | 64,774 | 166,501,376 | 1.176 |
| DG-DANN | 0.251505 | 70,754 | 166,447,616 | 0.761 |
| SOURCE-NORM | 0.243622 | 64,774 | 166,500,864 | 0.941 |
| P1 | 0.178243 | 73,030 | 189,578,752 | 5.801 |
| P2 | 0.188606 | 75,143 | 194,573,824 | 5.800 |

The abbreviated smoke scores are not scientific results or tuning outcomes. They did not trigger an architecture, context, or optimizer change. Every configured method retains the same full budget. Derived-condition smoke checks also completed: P2-SHUFFLED 0.187469, P2-NULL 0.104671, P2-MISMATCHED-RX 0.188801, RX-NORM 0.243088, and T3A 0.265653. T3A selected `filter_K=20` using source validation only in this smoke diagnostic.

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
