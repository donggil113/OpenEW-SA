# WiSig final scientific integrity report

## Frozen repository scope

Result: **PASS** against PR #83 base commit `8d7d3cfca85a200a781fada3c5ca15dbaef3cfe2`.

- `papers/paper1_openew_sa/`: unchanged.
- `papers/paper2_ood_rf_signal_recognition/`: unchanged.
- PR #80 relational-audit paper, source, scripts, configurations, and tests: unchanged.
- PR #81 static-relational pilot paper, source, scripts, configurations, tests, and frozen result: unchanged.
- PR #82 prospective-metadata paper, source, scripts, configurations, and tests: unchanged.
- PR #83 dataset-qualification paper, source, scripts, configurations, and tests: unchanged.

The check covers Paper 1, Paper 2, and every PR #80--#83 paper, source, script, configuration, and test path against `origin/main`; it is not limited to manuscript directories.

## External artifact immutability

Result: **PASS**.

- Raw ManyRx archive SHA-256 recomputed and matched.
- Pass-A and pass-B converted dataset-manifest hashes recomputed and matched.
- The two passes retained the same 156 deterministic files, with zero missing, additional, or byte-different files after excluding the explicitly nondeterministic runtime/state records.
- Split-freeze hash matched.
- The external raw/extracted tree remained read-only.
- No existing OpenEW-SA dataset, Paper 1/Paper 2 frozen experiment, or PR #81 result was overwritten.

Expected raw archive SHA-256: `d2b23108c3f6f63a10ebbb149d7b08d6e1c1961cf5184926fbab452def3049de`.

Expected pass-A/pass-B dataset-manifest SHA-256: `ffd98dcb8182435c1aaf416c3bb137e6f56f353811e7d1d7a6fc0cc4817ae4b6`.

Expected split-freeze SHA-256: `08561f708862c696b4140876abbc7871af257bf38aab1a7e2728a8de9152e449`.

## Experiment registry

Result: **PASS**.

- Declared condition entries: 580.
- Unique executable configurations: 530.
- Completed unique configurations: 530.
- Failed configurations: 0.
- Missing/unexpected/duplicate/malformed/nonterminal records: 0.
- Configuration hashes recomputed successfully: 530/530.
- Prediction files present and SHA-256 verified: 530/530.
- Checkpoint files present and SHA-256 inventoried: 530/530.
- Training Git SHA: `1fc56737ba4376a0496437324cf1d3b34bb47373` for every run.
- Converted data-manifest SHA: `ffd98dcb8182435c1aaf416c3bb137e6f56f353811e7d1d7a6fc0cc4817ae4b6` for every run.

The declared grid contains 580 condition entries and 530 unique executable configurations. Exact duplicate conditions are reused by `config_hash`; missing, unexpected, duplicate, malformed, nonterminal, unhashed, or prediction-hash-mismatched records fail closed. Every run must use training commit `1fc56737ba4376a0496437324cf1d3b34bb47373` and one data-manifest hash.

## Scientific constraints

Result: **PASS**. Target annotations were accessed only by evaluation and audit code after the split/model contracts were frozen. Receiver identity was the sole relation field and operated only by equality. Day remained split-only. Exact paths and target-bearing source tokens remained quarantined externally. All five frozen seeds, receiver folds, eligible transmitters, model definitions, primary context size, and retention levels were retained regardless of observed performance.

- No PR #81 M0/M1/M2 run was rerun or tuned.
- No target-visible relation, target-derived context, receiver-value embedding, or day model feature was introduced.
- No fold, class, seed, context size, retention level, model family, or optimizer choice was changed from held-out performance.
- No temporal, dynamic, hypergraph, uncertainty-gating, or neuro-symbolic model was run.
- No full raw WiSig payload or derived signal tensor was committed or uploaded.

## Validation

Final validation passed:

- WiSig-specific tests: 152/152.
- Prospective metadata tests: 84/84.
- Public dataset-qualification tests: 93/93.
- Prior static-relational tests: 19/19.
- Relational metadata-audit tests: 6/6.
- Paper 2 regression tests: 17/17.
- `git diff --check`: PASS.

The publication-figure audit found nine expected PNG/PDF pairs, readable axes and legends, embedded fonts in every PDF, and zero Type 3 fonts. Generated payloads, predictions, checkpoints, CSVs, and figures remain external and untracked.
