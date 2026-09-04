# WiSig V2 power-loss recovery report

Status: **COMPLETE**

## Recovery boundary

Recovery began on branch `paper3/wisig-methods-remediation-v2` at committed training HEAD `f776d13aab89645e049f032765e88de24969c8aa`. The existing backup at `/mnt/d/openew_sa_data/paper3/wisig_v2/recovery/worktree_20260904_210457/` was treated as immutable and was not overwritten or deleted. No branch switch, pull, rebase, reset, clean, or training restart was performed.

## Pre-unblinding recovery checks

- The current dirty-state listing, committed HEAD, and branch agreed with the recovery backup.
- A complete source audit covered 99 V2 files; all were nonempty, UTF-8, newline-terminated, and free of conflict/patch markers. Python and YAML parsing passed.
- The full V2 and regression suites passed before scientific unblinding code was committed.
- All 2,520 blinded records were reconciled without target labels: 2,080 primary, 260 day-secondary, and 180 grouped-secondary; zero failed or incomplete records.
- Prediction schemas contained only opaque sample IDs and probability matrices. Query sets, support/query disjointness, config/split/data hashes, probability simplexes, checkpoints, histories, and derived-checkpoint lineage passed.

## Immutable freeze and unblinding

- Pre-unblinding commit: `da07219a018d4c10eb365e9cd2a847fe59520eda`.
- Freeze created: `2026-09-04T12:45:26.457185+00:00`.
- Freeze SHA-256: `705f723b7af65564a17af04ec2cc63b6a33627c2db96fdf7425ffc23a889959e`.
- Frozen primary run-registry SHA-256: `b43e324f7d3de5b911638ad4ea10d8cf119c644710da6d7c7d646a19186a5ebf`.
- Frozen primary prediction-manifest SHA-256: `9e80ed7a25ddcf3d9aa3365d0a687eb9549257cbf789040cdc71c20391c2e1f1`.
- Frozen split SHA-256: `2be7d808b42e094b30aa0735a766e12dbc6dc027315443665a70d1cad07e2db4`.
- Frozen data-manifest SHA-256: `ffd98dcb8182435c1aaf416c3bb137e6f56f353811e7d1d7a6fc0cc4817ae4b6`.
- Frozen analysis-code tree SHA-256: `f3417220a04f2dfe45786c98b002368e4c9cdf9f328c0f427cecc387733fff84`.
- One-time primary unblinding: `2026-09-04T12:49:29.489216+00:00`.
- Primary unblinding-manifest SHA-256: `5095caede85af7544f7a578ad6ad33969e0c310e7794b609f998ef2c8132d284`.

The create-once primary, day, and grouped manifests were not overwritten. The equalized diagnostic remained unexecuted because its frozen structural gate failed.

## Recovery defect and repair

After valid numerical outputs had been generated, the comprehensive analysis validator rejected serialization because one optional audit flag was a NumPy boolean rather than a native JSON boolean. The canonical JSON writer failed closed. The repair converts NumPy scalar audit values to native JSON primitives and adds a regression test. It changes no metric, threshold, method, comparison, receiver, seed, support set, or statistical procedure. The validator then passed every required and optional gate.

## Final integrity

The post-analysis full blind reconciliation reproduced the pre-unblinding hashes for primary, day, and grouped predictions/checkpoints/histories. The final repository/data verifier passed Paper 1, Paper 2, PR #80--#84, raw-archive, conversion-manifest, and PR #84 analysis-tree checks. No model training, target-driven redesign, packet bootstrap, new method, or second target unblinding occurred during recovery.
