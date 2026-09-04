# Information-budget matrix

Status: **VALIDATED AFTER ONE-TIME UNBLINDING**

Target support is always unlabeled. The primary support bank contains 128 packets and is disjoint from every evaluated query. R0 methods are evaluated on the same query IDs but do not consume the support bank.

| Method | Regime | Source train | Source validation | Target-receiver support | Source-validation donor support | Query as support | Target label | Test gradient | Test stats | Test prototypes | Extra parameters |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---:|
| P0 | R0 | Yes | Yes | 0 | 0 | No | No | No | No | No | No |
| P0-WIDE | R0 | Yes | Yes | 0 | 0 | No | No | No | No | No | Yes |
| DG-CORAL | R0 | Yes | Yes | 0 | 0 | No | No | No | No | No | No |
| DG-GROUPDRO | R0 | Yes | Yes | 0 | 0 | No | No | No | No | No | No |
| DG-DANN | R0 | Yes | Yes | 0 | 0 | No | No | No | No | No | Yes, training-only discriminator |
| SOURCE-NORM | R0 | Yes | Yes | 0 | 0 | No | No | No | Source-only fixed | No | No |
| P1 | R1 | Yes | Yes | 128 | 0 | No | No | No | No | No | Yes |
| P2 | R1 | Yes | Yes | 128 | 0 | No | No | No | No | No | Yes |
| P2-NULL | R1 control | Yes | Yes | 0 (frozen bank unused) | 0 | No | No | No | No | No | Same as P2 |
| P2-MISMATCHED-RX | R1 control | Yes | Yes | 0 | 128 from one different receiver | No | No | No | No | No | Same as P2 |
| P2-SHUFFLED | R1 control | Yes | Yes | 0 | 128 mixed across different receivers | No | No | No | No | No | Same as P2 |
| RX-NORM | R1 | Yes | Yes | 128 | 0 | No | No | No | Input mean/RMS | No | No |
| T3A | R2 | Yes | Yes | 128 | 0 | No | No | No | No | Yes | No |
| AdaBN | R2 | N/A | N/A | N/A | N/A | No | No | N/A | N/A | No | N/A; GroupNorm backbone |
| Tent | R2 | N/A | N/A | N/A | N/A | No | No | N/A | N/A | No | N/A; GroupNorm backbone |

The shuffled and mismatched controls necessarily change support identities to break same-receiver membership; they match packet count and available day distribution but are not described as receiving the same target-receiver packets. Deployable same-information comparisons are P2 versus RX-NORM and T3A, which consume the identical target-receiver support bank.

## Verified information-matched result

T3A was the sole preregistered same-information TTA candidate and was selected using source-validation receiver macro-F1 only. On the 32 equal-weight held-out receivers, T3A achieved 0.833692 macro-F1 versus 0.806726 for P2. The mean receiver-level P2-minus-T3A difference was -0.026966, with a 10,000-replicate receiver-bootstrap interval of [-0.038002, -0.016769], two-sided 100,000-draw sign-flip p=0.000010, and Holm-adjusted p=0.000040.

RX-NORM achieved 0.800769 and therefore did not explain P2 through receiver-specific input statistics alone. RX-NORM was also -0.005207 below SOURCE-NORM descriptively. Neither comparison used target labels.

AdaBN and Tent remained not applicable because the frozen GroupNorm backbone contains no BatchNorm modules; no layer was retrofitted after target access. No faithful RF-specific receiver-robust baseline was added where verified implementation details were insufficient.
