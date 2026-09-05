# Shen author-payload import runbook

Status: **READY SOFTWARE CONTRACT; PAYLOAD NOT AVAILABLE OR AUTHORIZED**

PR #87's licence conflict and unavailable author route remain binding. Do not download, copy, or process a real Shen payload until lawful access and a payload licence are documented.

## Receipt gate

1. Record the sender, official source, access terms, dataset version, citation, redistribution and derived-artifact terms.
2. Store the original archive outside Git in a new read-only root.
3. Record receipt UTC, exact bytes, SHA-256, archive member list, and licence snapshot.
4. Reject path traversal, escaping symlinks, executables, unexpected keys, or undocumented serialization.
5. Do not infer a payload licence from paper copyright.

## Two-pass qualification

1. Inspect HDF5 schema without loading full payload.
2. Require exactly documented data, label, SNR, and CFO; unknown keys fail closed.
3. Verify numeric dtypes, finite values, row alignment, physical receiver manifest, and transmitter range.
4. Convert twice into new pass_a and pass_b roots.
5. Require identical opaque sample IDs, metadata/annotation hashes, shapes, and numerical feature values.
6. Freeze target-neutral acquisition metadata separately from transmitter annotations and restricted source provenance.
7. Run receiver, hardware, capture, path, missingness, packet-index, and target-proxy audits.

## Transfer gate

The frozen first qualification crop is the centered contiguous 256-IQ rule (C2). It is target independent and performance blind. Do not substitute first-window, energy search, or multi-crop aggregation after target access. The adapter may reject C2 for signal-semantic invalidity before modeling; any replacement requires a new source-only rationale and preregistration.

Freeze the ten-class head change, source normalization, 20-receiver LOSO map, three validation receivers, 128 support, disjoint queries, five seeds, P0/T3A/P2/P2-SHUFFLED code hashes, and one-time unblinding analysis before any target metric.

## Execution

1. Source-only smoke with target metrics disabled.
2. Commit converter, split, model-transfer, and analysis code.
3. Freeze archive/data/split/method hashes.
4. Execute blind records with checkpoint/resume.
5. Verify every receiver × method × seed record and query ID.
6. Unblind once at receiver level.
7. Recompute archive and derived-artifact integrity.
8. Keep RF payload, converted tensors, checkpoints, and predictions outside Git.

Synthetic fixtures are never scientific evidence and cannot satisfy the lawful-payload gate.
