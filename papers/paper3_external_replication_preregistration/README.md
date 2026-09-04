# Paper 3 external replication preregistration

Status: **DATASET QUALIFICATION COMPLETE; MODEL TRAINING NOT AUTHORIZED**

This package freezes the design for an independent replication of the WiSig
V2 receiver-calibration study. It does not modify, rerun, or reinterpret the
merged V2 result at commit `48cec06645736bd45c455a64841f3f50e0368b40`.

The qualification result is negative for the public releases examined: none
simultaneously provides a compatible RF-fingerprinting task, multiple physical
receivers, explicit target-neutral calibration episodes, acquisition-disjoint
query episodes, and a sufficiently clear licence/provenance path. Consequently,
no public payload was downloaded and no converter or model was run.

The prospective path is design-ready but data-not-ready. A new collection must
pass the gates in the following documents before the frozen P0, T3A, and P2
methods may be executed:

- `external_replication_requirements.md`
- `candidate_dataset_matrix.md`
- `calibration_episode_contract.md`
- `frozen_method_transfer_spec.md`
- `external_split_protocol.md`
- `external_statistics_preregistration.md`
- `prospective_replication_collection_protocol.md`
- `replication_go_no_go.md`

No target result exists in this workstream.
