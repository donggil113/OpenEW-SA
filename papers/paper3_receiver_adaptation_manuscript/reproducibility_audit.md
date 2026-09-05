# Reproducibility audit

**PASS within the tested source/environment scope.**

## Fresh-source reproduction

A no-hardlink clone was created at /tmp/openew-paper3-release-WkLlVH. It was advanced to tested code commit 734b11e9c0972199a41ce1b8ec5df6e0f4f062c9. All prior Paper 3 tests, new runtime/manuscript tests and Paper 2 tests passed: 1,466 tests plus seven passing subtests; zero failures/errors/skips. Breakdown: 356 new, 1,093 earlier Paper 3, 17 Paper 2. All Paper 3 including new: 1,449.

Exact invocation:

    PYTHONPATH=src:tests/paper3/metadata python -m pytest --import-mode=importlib -q tests/paper3 papers/paper2_ood_rf_signal_recognition/tests

The initial default-import combined invocation exposed pre-existing duplicate test-module names and the metadata tests' common helper import. Importlib mode plus the existing helper directory resolves collection without modifying old tests. Six warnings remain from frozen NumPy-internal compatibility and single-label synthetic metric cases.

Fresh-source checks also passed compileall, figure/table regeneration, main/supplement/checklist LaTeX builds, citation/font/number audits, CLI entrypoints, a synthetic collection cycle, 10,000 deterministic contract cases and mock Shen two-pass conversion. No private RF payload is needed for these steps. Regeneration leaves the clone's tracked files unchanged.

This is a fresh SOURCE clone using the same installed WSL/Python/TeX environment, not an independent clean-machine install or hardware replication. PDF timestamps may differ; numerical content and tracked generated assets match. Full environment and observed pinned core packages are in environment/. Native Windows and untested filesystems are outside the runtime claim.

## Synthetic runtime validation

Authoritative full stress output: /mnt/d/openew_sa_data/paper3/collection_runtime_validation/consolidation_v3/. It passed 10,000 metadata/state-input cases and 2,036 durable journal transitions over four 500-capture calibration cycles plus query/freeze/close steps. An additional eight-receiver, four-family, two-site synthetic SMALL-tier cycle passed schema/mix/disjoint-record QA over 64 captures and 150 transitions. Training authorization remains false.

The initial displayed transition counter omitted one day-freeze commit per cycle after journal-bound freezes were added. It was corrected to read persisted revision, regression-tested and the full stress run repeated. Earlier reports are retained; they are not the final count source.

Fault tests cover partial capture, disk-full, orphan payload/metadata, journal/state interruption, unclosed session, corrupt checksum and day-freeze interruption/tampering. One subprocess exits abruptly after durable journal persistence and recovery replays its transition. These are software fault simulations, not a physical power-cut qualification.

## Frozen evidence integrity

Read-only verification matched:
- WiSig raw archive SHA256 and both conversion manifests;
- all 248 listed raw-conversion shard members across pass A/B;
- all 2,080 primary blind predictions and the original primary registry/checkpoint manifest;
- all 260 day and 180 grouped blind predictions against recorded hashes;
- all 64 V2, 23 addendum and 32 benchmark listed analysis artifacts.

No frozen experiment, raw dataset, result or method was rewritten. Git changes are confined to the five new Paper 3 consolidation/runtime prefixes. Paper1/2 and PR80–88 packages remain unchanged. Older large raw corpora and nonprimary checkpoint bytes were not independently rehashed in this consolidation; the scope is explicit rather than overstated.

## Release boundary

The numerical release is small aggregate/receiver-seed evidence, not RF, packet predictions or annotations. Tests exercise synthetic data only. No model training, bootstrap rerun on scientific predictions, RF download, Shen access bypass or email sending occurred. Institutional licence review and independent physical data remain required.
