# Lawful Shen payload receipt and qualification

No RF payload was acquired in this workstream. Synthetic HDF5 fixtures validate software only.

1. Obtain written licence/source authorization and institutional review. Retain the exact evidence and its SHA256.
2. Receive the official version through an authorized route. Record URL, sender/version, UTC, exact bytes and SHA256 before opening. Do not overwrite an existing receipt.
3. Inspect archive members for traversal, absolute paths, symlinks and unexpected executable content before extraction. Extract only to a new external directory and freeze it read-only where practical.
4. Run the receipt validator on each documented receiver HDF5 file. It rejects unknown keys, soft/external/virtual HDF5 links, unsupported shape/dtype, non-finite data and fractional labels. Audit the complete physical receiver map rather than assuming synthetic counts prove real counts.
5. The documented fields are data, label, SNR and CFO. Reconstruct real-half/imag-half complex samples; apply the unchanged centered-256 PR88 rule only after source-semantic review. Labels go to annotations, never acquisition metadata.
6. Convert to two NEW external directories with identical config. Compare sample IDs, acquisition CSV, annotations, provenance/manifest and feature shard contents. No target metrics.
7. Run proxy, class-support, receiver-support and split-integrity audits. Freeze method/split/preregistration hashes. Report missingness and rejection, not only successful records.
8. Source-only smoke is possible only after the evidence-bound gate. Target results remain blind. Commit analysis and blinding code before any authorized benchmark; unblind once after all preregistered records complete.
9. Preserve every gate output and exact input hash. No command in this receipt toolkit itself trains a model.

Command:

    scripts/paper3/collection_runtime/qualify-shen-payload --payload /external/lawful/receiver.h5 --receiver-id rtl_1 --evidence approved_receipt_evidence.json --output /external/new/receipt_report.json

Use the actual verified receiver ID accepted by the frozen map; rtl_1 is the first documented map entry, not permission to assign that receiver identity to an arbitrary file. The command checks schema and returns three booleans:

- AUTHORIZED_FOR_CONVERSION: bound lawful-source/licence attestation and valid receipt.
- AUTHORIZED_FOR_SOURCE_SMOKE: conversion plus two-pass/proxy/support/split/method PASS reports bound to exact data/method/split hashes, with preregistration hash.
- AUTHORIZED_FOR_BLIND_BENCHMARK: prior gates plus source-smoke, analysis-code-freeze and blinding PASS reports.

Synthetic or unknown status always blocks scientific authorization. The gate consumes reviewed evidence; it does not generate legal approval or establish physical provenance itself. A PASS for one file does not establish dataset-wide readiness. Class-head dimension is an explicit task adapter, not permission to change the encoder/T3A/P2 design. No external experiment is launched by this branch.
