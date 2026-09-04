# WiSig V2 execution runbook

Status: **FROZEN BEFORE TARGET-METRIC UNBLINDING**

All commands use `/home/user/venvs/openew-sa/bin/python`, `PYTHONPATH=src`, and repository `/home/user/src/openew-sa`. External scientific artifacts remain below `/mnt/d/openew_sa_data/paper3/wisig_v2`; no generated predictions, checkpoints, or RF payload are committed.

## 1. Raw-I/Q blind primary

```bash
PYTHONPATH=src /home/user/venvs/openew-sa/bin/python \
  scripts/paper3/wisig_v2/run_v2_suite.py \
  --repository /home/user/src/openew-sa \
  --converted-root /mnt/d/openew_sa_data/paper3/wisig/converted/pass_a \
  --split-root /mnt/d/openew_sa_data/paper3/wisig_v2/splits_v2_frozen \
  --run-root /mnt/d/openew_sa_data/paper3/wisig_v2/experiments/confirmatory_v2 \
  --phase primary_loso --blind-target-metrics
```

The 2,080 records must all be `COMPLETE`, contain null held-out metrics, and state that target labels were not loaded for metrics. Every record must share the frozen execution Git SHA and immutable converted-data manifest hash.

### Bounded two-process execution

The frozen primary grid may use at most two independent GPU processes. The
default suite process traverses receiver indices upward. A second worker is
permitted only for the static, disjoint receiver range 31 down to 20, using
`run_primary_worker.py`. The worker writes `worker_high_plan.json` and
`worker_high_status.json`; it does not rewrite the global suite plan or status.
Both processes must use Git SHA
`f776d13aab89645e049f032765e88de24969c8aa`, the same converted-data and split
roots, unique run directories, and blinded target archives. The worker refuses
an already-`RUNNING` run, and the normal resume contract skips compatible
completed records when the primary process later encounters them.

This scheduling decision is computational only. It does not alter receivers,
models, seeds, support selection, target blinding, or scientific analysis. At
launch the default process was at receiver 3 and the worker began at receiver
31, leaving 16 untouched receiver indices between their active ranges. Two
processes used about 5.0 GiB of 24.6 GiB GPU memory at the first post-launch
check. A third process is forbidden.

The RTX 4090 preflight showed approximately 4.3 GiB of 24.6 GiB allocated and about 37% utilization for one run. A second process is therefore permitted only on a statically disjoint, high receiver range, with the same frozen Git SHA/configs and a separate worker status file. `run_primary_worker.py` never writes the global suite status. The selected worker range is receiver 31 down through 20 (780 records); the global ascending scheduler was still on receiver 3 at launch, leaving a 16-receiver separation. The scheduler later revalidates and skips compatible completed records. If memory or integrity checks fail, the second worker stops; no third process is permitted.

## 2. Pre-unblinding freeze

First commit and push all protocol and analysis code while target results remain blind. From a clean worktree:

```bash
PYTHONPATH=src /home/user/venvs/openew-sa/bin/python \
  scripts/paper3/wisig_v2/freeze_before_unblinding.py \
  --repository /home/user/src/openew-sa \
  --run-root /mnt/d/openew_sa_data/paper3/wisig_v2/experiments/confirmatory_v2 \
  --split-root /mnt/d/openew_sa_data/paper3/wisig_v2/splits_v2_frozen \
  --split-manifest /mnt/d/openew_sa_data/paper3/wisig_v2/splits_v2_frozen/split_freeze_manifest.json \
  --protocol-file papers/paper3_wisig_methods_remediation/methods_remediation_preregistration_v2.md \
  --protocol-file papers/paper3_wisig_methods_remediation/go_rule_operationalization.md \
  --protocol-file papers/paper3_wisig_methods_remediation/model_config_freeze_v2.md \
  --output /mnt/d/openew_sa_data/paper3/wisig_v2/analysis/pre_unblinding_freeze.json
```

This gate recomputes hashes and exact frozen query membership for every blind archive without reading annotations.

## 3. One-time primary unblinding

```bash
PYTHONPATH=src /home/user/venvs/openew-sa/bin/python \
  scripts/paper3/wisig_v2/unblind_and_analyze_v2.py \
  --converted-root /mnt/d/openew_sa_data/paper3/wisig/converted/pass_a \
  --split-root /mnt/d/openew_sa_data/paper3/wisig_v2/splits_v2_frozen \
  --run-root /mnt/d/openew_sa_data/paper3/wisig_v2/experiments/confirmatory_v2 \
  --analysis-root /mnt/d/openew_sa_data/paper3/wisig_v2/analysis/confirmatory_v2 \
  --preregistration papers/paper3_wisig_methods_remediation/methods_remediation_preregistration_v2.md
```

The unblinding manifest is create-once. A second invocation must fail.

## 4. Frozen post-unblinding diagnostics

Run the preregistered oracle composition controls and support-budget/`k` sensitivities without altering checkpoints:

```bash
PYTHONPATH=src /home/user/venvs/openew-sa/bin/python scripts/paper3/wisig_v2/run_postunblind_diagnostics.py \
  --converted-root /mnt/d/openew_sa_data/paper3/wisig/converted/pass_a \
  --split-root /mnt/d/openew_sa_data/paper3/wisig_v2/splits_v2_frozen \
  --run-root /mnt/d/openew_sa_data/paper3/wisig_v2/experiments/confirmatory_v2 \
  --analysis-root /mnt/d/openew_sa_data/paper3/wisig_v2/analysis/confirmatory_v2 \
  --oracle --sensitivity
```

The oracle conditions are label-dependent diagnostics and are never included in the deployable primary table.

The general suite CLI deliberately does not execute the support-budget or
context-`k` phases. Those settings change only target-time support access, so
retraining a nominally new P2 checkpoint would add redundant algorithmic
variability and risk a post-freeze deviation. `run_postunblind_diagnostics.py`
loads the matching frozen primary P2 checkpoint for every receiver and seed.

## 5. Secondary suites

- Coarse-day: run `run_v2_suite.py --phase day_secondary --blind-target-metrics` in a separate run root; unblind only after the raw primary manifest exists.
- Repeated grouped receiver: use `run_grouped_secondary.py --blind-target-metrics` with the separately frozen grouped split root.
- Official equalized signal: convert `equalized_index=1` twice, require `audit_equalized_conversion.py` to pass, build a separate V2 split root, then run `run_equalized_diagnostic.py --blind-target-metrics`.

Raw, grouped, day, and equalized outputs must never share a run directory.

## 6. Analysis and integrity

Run target-proxy post-audits, compute accounting, rendering, the fixed decision rule, and analysis-package hashing only after primary unblinding. The standardized label-free latency benchmark may run after the primary checkpoints are complete; it is fixed to seed 829 and verifies reproduced probabilities against the blind archives:

```bash
PYTHONPATH=src /home/user/venvs/openew-sa/bin/python \
  scripts/paper3/wisig_v2/benchmark_inference_costs.py \
  --converted-root /mnt/d/openew_sa_data/paper3/wisig/converted/pass_a \
  --split-root /mnt/d/openew_sa_data/paper3/wisig_v2/splits_v2_frozen \
  --run-root /mnt/d/openew_sa_data/paper3/wisig_v2/experiments/confirmatory_v2 \
  --output /mnt/d/openew_sa_data/paper3/wisig_v2/analysis/confirmatory_v2/standardized_inference_benchmark.csv \
  --repeats 3
```

Before accepting a report, run `validate_v2_analysis.py`; it fails on incomplete receiver/model/seed grain, duplicate paired keys, missing receivers, out-of-range metrics, an incorrect inferential unit, incorrect resampling counts, undisclosed oracle label use, or an incomplete/nonreproducing latency benchmark. The final integrity command compares Paper 1, Paper 2, PR #80--#84 paths, raw archive SHA-256, both PR #84 conversion manifests, and all 54 files in the externally frozen PR #84 final-analysis snapshot against merge commit `53bcf41471c11cdd7a96f949fcfcb24b117deccd`:

```bash
PYTHONPATH=src /home/user/venvs/openew-sa/bin/python \
  scripts/paper3/wisig_v2/verify_v2_integrity.py \
  --repository /home/user/src/openew-sa \
  --baseline 53bcf41471c11cdd7a96f949fcfcb24b117deccd \
  --v1-root /mnt/d/openew_sa_data/paper3/wisig \
  --pr84-analysis-snapshot /mnt/d/openew_sa_data/paper3/wisig_v2/analysis/pr84_final_v1_snapshot.json \
  --output /mnt/d/openew_sa_data/paper3/wisig_v2/analysis/confirmatory_v2/final_integrity_report.json
```
