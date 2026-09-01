# Paper 3 Static-Relational Pilot Configuration Freeze

Freeze date: 2026-09-02
Status: **FROZEN BEFORE HELD-OUT EVALUATION**

## Decision

The source-only smoke gate passed without a resource-driven or stability-driven change to the scientific design. The configuration in `configs/paper3/static_relational/pilot.yaml` and the definitions in `m0_m2_frozen_pilot_protocol.md` are frozen for the full target-domain suite.

## Runtime environment

- Python: 3.12.3
- PyTorch: 2.11.0+cu128
- CUDA available: yes, one device
- GPU: NVIDIA GeForce RTX 4090, 24,564 MiB reported by `nvidia-smi`
- PyTorch Geometric: not installed and not used
- Implementation: pure PyTorch bounded context gathering; no clique expansion

PyTorch was absent from the user-specified virtual environment at preflight and was installed because it is a declared project dependency and indispensable for the requested training. No PyTorch Geometric or other graph framework was installed.

## Frozen training configuration

- Seeds: 829, 1829, 2829, 3829, 4829
- Epochs: 10
- Optimizer: AdamW
- Learning rate: 0.001
- Weight decay: 0.01
- Hidden width: 128
- Dropout: 0.1 for JamShield/ElectroSense node MLPs
- Batch size: JamShield 64; ElectroSense 128; DeepSense 128
- Maximum relation-type context: 64 observations
- Source-validation fraction: 0.20, deterministic and stratified within source domain/target class
- Model selection: best epoch by source-validation macro-F1 only
- Target evaluation: disabled during smoke; enabled only after this freeze is committed

No architecture, relation, context size, seed, optimizer, split, preprocessing, or retention level was selected using held-out performance.

## Source-only smoke evidence

Run root: `/mnt/d/openew_sa_data/paper3/experiments/static_relational_smoke_20260902T000000Z`

All runs used seed 829, 8,192 source-training anchors, at most 2,048 source-validation anchors, and three abbreviated epochs. Held-out metrics were disabled.

| Dataset | Stage | Epoch losses | Source relation coverage | Peak GPU bytes | Result |
| --- | --- | --- | ---: | ---: | --- |
| JamShield | M0 | 0.249898, 0.114432, 0.103856 | 0.000000 | 18,271,744 | PASS |
| JamShield | M1 | 0.301631, 0.147860, 0.120020 | 1.000000 | 22,884,352 | PASS |
| JamShield | M2 | 0.301243, 0.148327, 0.119977 | 1.000000 | 22,884,352 | PASS |
| ElectroSense | M0 | 0.739923, 0.138452, 0.056140 | 0.000000 | 20,648,960 | PASS |
| ElectroSense | M1 | 0.978335, 0.278611, 0.104077 | 1.000000 | 42,269,696 | PASS |
| ElectroSense | M2 | 1.167668, 0.450520, 0.197069 | 1.000000 | 43,143,168 | PASS |

Every run produced a finite forward/loss path, decreasing source-training loss, a checkpoint, source-validation predictions, metrics, relation diagnostics, and completed metadata. A second `--resume` execution skipped 6/6 runs as compatible.

## Diagnosed technical failure and correction

The first JamShield smoke attempt failed before training because its verified `labels.json` stores `class_names` as a mapping from task-column name to class list, while the initial loader treated the mapping keys as class values. The loader now selects `class_names[label_column]` when the field is a mapping. The actual frozen target strings remain exactly `normal` and `abnormal_interference`.

This was a schema interpretation defect. It changed no sample, label, split, relation, model capacity, optimizer, seed, or result. After the correction, all six smoke runs were rerun under a new compatible-source hash and passed. The balanced-accuracy implementation was also made explicit as the mean recall over classes present in the evaluated partition, eliminating harmless per-domain warnings without changing the primary macro-F1 endpoint.

## Freeze consequence

The full suite must use this committed configuration unchanged. Any later technical retry must retain the same config hash, source/artifact hashes, split hashes, and fixed run specification. A scientific integrity or leakage failure stops the suite; ordinary independent technical failures are recorded and do not suppress other runs.
