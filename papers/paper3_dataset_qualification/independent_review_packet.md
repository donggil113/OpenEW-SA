# Independent Review Packet

## Decision requested

Review whether WiSig should proceed to a bounded ManyRx import and static receiver-context preregistration, and whether OPERAnet merits a separate task-fit/licence audit. No model training is proposed.

## Frozen history

- PR #80 established that current JamShield/DeepSense/ElectroSense metadata do not justify dynamic reasoning.
- PR #81 completed the 140-run static M0--M2 pilot and recorded an overall NO-GO; shuffled controls and retention curves did not support a stable relational mechanism.
- PR #82 added a fail-closed acquisition/annotation contract, provenance, QA, and metadata readiness thresholds.

## Evidence supplied

- WiSig 26-item official evidence matrix, leakage precheck, source-code processing trace, external metadata manifest, aggregate proxy audit, and machine-readable qualification report.
- Seventeen-candidate official-source matrix.
- Deep evidence summaries for WiSig, OSU LoRa, OPERAnet, Antwerp LPWAN, and POWDER.
- Top-three ranking and bounded access plans.

## Main findings

1. WiSig receiver identity is a credible target-neutral equality relation with 41 groups and full indexed coverage. Day is split-only. Transmitter and capture/path identity are forbidden.
2. WiSig has no valid temporal context: packet order exists only within transmitter-pure captures, and no explicit acquisition clock is released.
3. WiSig's CC BY-NC-SA licence permits research use but imposes restrictions; derived-payload handling needs institutional review.
4. OPERAnet contains the strongest verified temporal structure but has a different human-sensing task and co-located annotations.
5. No candidate currently passes all conditions for model authorization.

## Reviewer questions

- Is a receiver-context RF-fingerprinting study sufficiently distinct from Paper 1's domain-generalization benchmark?
- Are CC BY-NC-SA obligations acceptable for the intended artifact policy?
- Is receiver equality alone mechanistically rich enough to justify a static relational paper, or should new prospective collection be mandatory?
- Should OPERAnet be excluded on task-fit grounds despite superior metadata?

## Recommended decision

Authorize only a metadata/sample conversion gate for WiSig ManyRx—not a model experiment. Require a second independent review after sample-level proxy/readiness audit and split preregistration.
