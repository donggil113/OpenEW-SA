# Receiver-adaptation benchmark handoff

Status: **COMPLETE — DRAFT HANDOFF**

## Verified result

- Frozen V2 evidence was fully reconciled: 2,080/2,080 records, exact method/receiver/seed grid, prediction and checkpoint manifests, converted manifest, raw archive, and PR #85/PR #87 analysis hashes all passed.
- New blind compute completed 160 SUP-FT-128 oracle records and 160 support-budget records, representing 1,280 adaptation/evaluation conditions, with zero failures.
- The create-once unblinding occurred at 2026-09-05T15:11:34.151668+00:00.
- T3A is the best unlabeled/deployable method: macro-F1 0.833692, +0.028014 over P0, 31/32 receivers positive, bootstrap [0.022011, 0.034661], sign-flip and Holm 0.000010.
- The supervised oracle is 0.838081 and is label-dependent.
- P2 remains 0.806726, approximately P0 (0.805679), and was not modified or rerun.
- AdaBN and Tent are not applicable to the frozen GroupNorm backbone. SHEN-GRL cannot be faithfully transferred to 256-IQ and was excluded, not approximated.
- T3A needs sufficient support: it is harmful at 16, below zero-support at 32, positive at 64, and stronger at 128/256. The 128 reference was not changed.
- T3A improves all three hardware-family means and has zero preregistered catastrophic receiver-seed failures.
- Classification improvement does not uniformly imply calibration improvement: T3A ECE is 0.102950 versus 0.088851 for P0.

## Track B: Shen readiness

No Shen RF payload was downloaded. The synthetic-only HDF5 adapter validates exactly data, label, SNR, CFO, finite numeric arrays, complex reconstruction, opaque IDs, annotation separation, six hardware families, 20 receiver LOSO, stable 128 support, disjoint queries, and fail-closed unknown formats. C2 centered 256-IQ is frozen for first lawful payload qualification. Software status is **READY; PAYLOAD GATE BLOCKED**.

## Track C: collection readiness

SMALL, MEDIUM, and FULL synthetic trees pass schema, episode, proxy/path, annotation separation, source-record disjointness, receiver count, hardware diversity, site/day, and provenance gates. Status is **READY FOR A REAL COLLECTION PILOT**, not scientific evidence.

## External outputs

- Root: /mnt/d/openew_sa_data/paper3/receiver_adaptation_benchmark/
- One-time unblinding: analysis/unblinding_manifest.json
- Receiver tables/statistics: analysis CSV files and receiver_level_inference.json
- Figures: analysis/figures/
- Information ledger: analysis/information_budget_ledger.csv
- Frozen V2 integrity: analysis/frozen_v2_integrity.json
- Pre-target freeze: analysis/pretarget_freeze.json
- Shen mock: mock/shen_contract_v1/
- Collection dry runs: mock/collection_small_v1, collection_medium_v1, and collection_full_v1

## Integrity and limitations

Paper 1, Paper 2, PR #80–#87 packages, WiSig raw/conversion/splits, and frozen V2 predictions/analysis were not edited. Target metrics were hidden until the exact new grid completed. There was no P2 tuning, receiver/seed removal, target-driven baseline addition, or external-data experiment.

The decisive limitation is external validity: WiSig remains the only scientific dataset, and its support bank is deterministic/disjoint but not a physically acquired calibration episode. The next action is a real SMALL-tier calibration/query pilot while lawful Shen access continues to be pursued.
