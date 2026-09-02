# WiSig Leakage Precheck

The target is transmitter identity. Classification fails closed: existence in metadata does not imply eligibility.

| Field/source | Classification | Reason |
|---|---|---|
| `receiver_id` / `rx_list` | **RELATION_ALLOWED** | Physical receiver is known at acquisition and is independent of the transmitter target definition. Official count-matrix audit gives 100% coverage, 41 groups, maximum receiver-group target purity 0.022712, target NMI diagnostic 0.022617, and no one-to-one mapping. Labels were used only for this safety audit. |
| receiver hardware family | **AUDIT_ONLY** | Provenance is described, but record-level mapping and deployment semantics are not yet fully verified. |
| capture day/date | **SPLIT_ONLY** | Coarse acquisition domain, suitable for a predeclared day holdout. It is not temporal evidence and may not enter the model. |
| receiver-day tuple | **UNRESOLVED** | Coverage is high, but this composite was not an independently frozen PR #82 relation type. It must not be introduced after qualification. |
| channel / 2462 MHz | **MODEL_FEATURE_ALLOWED** | Acquisition setting, but essentially constant in WiSig and not a useful relation. |
| sample rate / receive gain / capture length | **MODEL_FEATURE_ALLOWED** | Physical capture parameters if read from trusted metadata. They must not be inferred from unverified path tokens. |
| ORBIT node/grid position | **UNRESOLVED** | Potentially physical context, but record-level geometry recovery and privacy/deployment semantics need independent verification. |
| raw capture ID | **FORBIDDEN_TARGET_PROXY** | A raw capture is generated for one transmitter at a time; grouping by it recreates the target. |
| packet/window order within raw capture | **AUDIT_ONLY** | Order is target-nested and cannot define temporal neighbours. |
| `transmitter_id`, `tx_list`, node/device ID | **FORBIDDEN_TARGET** | RF fingerprinting class annotation. |
| transmitter hardware family | **ANNOTATION_ONLY** | Semantically tied to target device identity; not a relation. |
| target-bearing directory or filename token | **FORBIDDEN_TARGET_PROXY** | Official raw names and hierarchy expose transmitter identity. |
| spoofed MAC/IP | **AUDIT_ONLY** | Authors intentionally used common spoofed addresses; they are not device identities or useful relations. |
| filesystem mtime | **UNRESOLVED** | System metadata only; never accepted as acquisition time. |
| model prediction, correctness, OOD/ID, target performance | **FORBIDDEN_TARGET_PROXY** | Target-derived or evaluation-derived. |

## Aggregate target-proxy audit

| Candidate context | Groups | Packets represented | Max group purity | NMI diagnostic | Decision |
|---|---:|---:|---:|---:|---|
| Receiver | 41 | 9,976,477 | 0.022712 | 0.022617 | relation allowed |
| Capture day | 4 | 9,976,477 | 0.021048 | 0.012237 | split only |
| Receiver-day | 158 | 9,976,477 | 0.024930 | 0.034755 | unresolved composite |

These are safety diagnostics, not feature selection and not evidence of model performance. The official metadata matrix contains aggregate packet counts, so no sample target labels were loaded into a relation builder.

## Required API boundary

Any future converter must write acquisition metadata and annotations separately. Relation construction may receive `sample_id` and `receiver_id` only; it must not accept a path, target, transmitter, day-domain identifier, or annotation table. Relations must be built independently inside train/validation/test partitions.
