# Information-budget matrix

Target support is always unlabeled. The primary support bank contains 128 packets and is disjoint from every evaluated query. R0 methods are evaluated on the same query IDs but do not consume the support bank.

| Method | Regime | Source train | Source validation | Target-receiver support | Query as support | Target label | Test gradient | Test stats | Test prototypes | Extra parameters |
|---|---|---|---:|---:|---:|---:|---:|---|---|---:|
| P0 | R0 | Yes | Yes | 0 | No | No | No | No | No | No |
| P0-WIDE | R0 | Yes | Yes | 0 | No | No | No | No | No | Yes |
| DG-CORAL | R0 | Yes | Yes | 0 | No | No | No | No | No | No |
| DG-GROUPDRO | R0 | Yes | Yes | 0 | No | No | No | No | No | No |
| DG-DANN | R0 | Yes | Yes | 0 | No | No | No | No | No | Yes, training-only discriminator |
| SOURCE-NORM | R0 | Yes | Yes | 0 | No | No | No | Source-only fixed | No | No |
| P1 | R1 | Yes | Yes | 128 | No | No | No | No | No | Yes |
| P2 | R1 | Yes | Yes | 128 | No | No | No | No | No | Yes |
| P2-NULL | R1 control | Yes | Yes | Frozen but unused | No | No | No | No | No | Same as P2 |
| P2-MISMATCHED-RX | R1 control | Yes | Yes | 128 from a different receiver | No | No | No | No | No | Same as P2 |
| P2-SHUFFLED | R1 control | Yes | Yes | 128 mixed across different receivers | No | No | No | No | No | Same as P2 |
| RX-NORM | R1 | Yes | Yes | 128 | No | No | No | Input mean/RMS | No | No |
| T3A | R2 | Yes | Yes | 128 | No | No | No | No | Yes | No |
| AdaBN | R2 | N/A | N/A | N/A | No | No | N/A | N/A | No | N/A; GroupNorm backbone |
| Tent | R2 | N/A | N/A | N/A | No | No | N/A | N/A | No | N/A; GroupNorm backbone |

The shuffled and mismatched controls necessarily change support identities to break same-receiver membership; they match packet count and available day distribution but are not described as receiving the same target-receiver packets. Deployable same-information comparisons are P2 versus RX-NORM and T3A, which consume the identical target-receiver support bank.
