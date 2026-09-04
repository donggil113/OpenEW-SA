# WiSig methods remediation V2

This package reframes PR #84's P1/P2 models as **test-time receiver-context conditioning**, separates pure-inductive (R0), receiver-calibration (R1), and test-time-adaptation (R2) information regimes, and evaluates them with disjoint support/query banks and receiver-level inference. It does not claim temporal, dynamic, graph, hypergraph, or neuro-symbolic reasoning.

## Immutable external inputs

- WiSig V1 conversion: `/mnt/d/openew_sa_data/paper3/wisig/converted/pass_a`
- V2 LOSO/day split freeze: `/mnt/d/openew_sa_data/paper3/wisig_v2/splits_v2_frozen`
- Grouped-secondary split freeze: `/mnt/d/openew_sa_data/paper3/wisig_v2/splits_v2_grouped_secondary`
- Raw primary run root: `/mnt/d/openew_sa_data/paper3/wisig_v2/experiments/confirmatory_v2`

RF payloads, checkpoints, blind predictions, generated tables, and generated figures remain external and must not be committed.

## Execution order

1. Run all 2,080 raw LOSO condition records with `run_v2_suite.py --phase primary_loso --blind-target-metrics`.
2. Verify the complete blind archive set, commit all pre-unblinding protocol/code additions, and record their Git SHA.
3. Invoke `unblind_and_analyze_v2.py` exactly once. The command refuses an incomplete suite or an existing unblinding event.
4. Run the post-unblinding oracle composition and frozen support-budget/`k` diagnostics; then render external figures/tables and apply the predeclared decision rule.
5. Run the separate blind day, grouped-receiver, and official-equalized secondary suites; unblind them only after the raw primary manifest exists.
6. Recompute PR #80--#84 Git/path integrity, the WiSig archive hash, and conversion-manifest hashes; run all regression suites and `git diff --check`.

The exact rules are in `methods_remediation_preregistration_v2.md`, `go_rule_operationalization.md`, `information_budget_matrix.md`, and the three secondary-protocol notes. Poor receivers, seeds, controls, and negative results remain in the analysis.
