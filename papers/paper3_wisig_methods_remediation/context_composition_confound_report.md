# Context-composition confound report

Status: **COMPLETE — POST-HOC DIAGNOSTIC**

## Scope and estimand

This audit asks whether the receiver-level P2-minus-P0 difference varies with the composition of the frozen, label-free 128-packet receiver support bank. Support IDs were fixed before target annotations were opened. Labels were used only after the one-time unblinding to characterize the immutable banks and to construct explicitly nondeployable oracle controls.

The primary inferential unit remains the held-out receiver. Correlations are descriptive and post hoc; attention weights and oracle results are not interpreted causally.

## VERIFIED RESULT

### Natural support composition

- All 160 receiver-by-seed support banks contained exactly 128 packets and all six eligible transmitters.
- Support class entropy ranged from 1.603375 to 1.790789 nats; effective class count ranged from 4.969778 to 5.994181.
- The largest-class fraction ranged from 0.179688 to 0.273438. The smallest present-class fraction ranged from 0.007812 to 0.156250.
- Every evaluated query class was represented somewhere in its receiver support bank, so distinct-transmitter count and same-class-presence fraction were constant and their correlations were undefined by design.
- Across the 32 receiver-averaged rows, the association between support entropy and P2-minus-P0 was Pearson -0.207976 and Spearman -0.476173. The corresponding association with largest-class fraction was Pearson 0.162960 and Spearman 0.266951. These are descriptive diagnostics, not preregistered mechanism tests.

### Label-dependent oracle controls

Each oracle condition covered all 738,015 receiver-by-seed query evaluations. The oracle contexts are not deployable.

| Oracle condition | Mean macro-F1 | Difference from receiver-level P0 mean | Interpretation boundary |
|---|---:|---:|---|
| Same-class excluded | 0.825916 | +0.020237 | Query transmitter deliberately excluded from support |
| Same-class only | 0.608450 | -0.197229 | Label-dependent homogeneous support |
| Transmitter pure | 0.763193 | -0.042485 | One label-selected transmitter supplies support |

For transmitter-pure support, the mean fraction of predictions assigned to the selected support transmitter was 0.104880 (range 0.018408--0.208690). This does not indicate a simple collapse toward the selected support transmitter, but the condition substantially reduced macro-F1.

## INTERPRETATION

The natural support banks are broad six-class mixtures, not transmitter-pure containers. P2's small natural-support advantage over P0 does not appear to require same-class packets: removing the query class from context increased rather than removed the descriptive advantage, while same-class-only and transmitter-pure contexts were harmful. Support composition nevertheless matters strongly, because deliberately homogeneous contexts sharply degraded the fixed model.

The post-hoc entropy correlations are heterogeneous and cannot establish a causal mechanism. They do not justify changing the 128-packet support budget, k=32, receiver set, class set, or model.

## UNRESOLVED

- WiSig provides no verified deployment episode; the bounded support bank remains a calibration abstraction.
- Oracle conditions use target annotations and can never be presented as deployable methods.
- The same-class-excluded gain was diagnostic and was not included in the confirmatory Holm family.
- An external dataset with independently observed receiver-calibration sessions is still needed to test deployment realism.
