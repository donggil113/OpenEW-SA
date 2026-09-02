# Paper 3 contribution boundary and prior negative-pilot integration

## Distinct scientific roles

- **Paper 1** establishes OpenEW-SA benchmark behavior under random and prespecified domain holdouts across the original datasets.
- **Paper 2** studies open-set/OOD detection using uncertainty and feature-distance scores; its scores are not relations or inputs in this study.
- **Paper 3** asks whether a static, target-neutral same-receiver context inductive bias improves transmitter recognition under independently qualified unseen-receiver and acquisition-day shifts in WiSig.

Paper 3 does not obtain novelty by adding another dataset to Paper 1. Its central mechanism test is the contrast among independent, capacity-matched, actual receiver-context, shuffled-context, null-context, retention, and context-size conditions under a pre-audited context contract.

## PR #81 negative result

The 140-run PR #81 static-relational pilot remains frozen as an overall NO-GO. Coarse station/receiver/date equality metadata in JamShield and ElectroSense did not satisfy the shuffled-control and relation-retention mechanism criteria. DeepSense had no allowed relation. No P0/M1/M2 run is repeated or tuned here.

If WiSig produces mechanism-specific receiver-context evidence, PR #81 should be reported as a cautionary contrast: relation metadata must be qualified for mixed-target support, coverage, and deployment meaning; equality fields alone do not guarantee relational value. If WiSig is also NO-GO, PR #81 remains an internal scientific gate or future cautionary appendix rather than being repackaged as a positive contribution.

## Prohibited framing

The study must not claim dynamic, temporal, hypergraph, neuro-symbolic, or uncertainty-gated learning. WiSig packet order is target-nested and no valid acquisition clock exists. The receiver episode is explicitly unordered.
