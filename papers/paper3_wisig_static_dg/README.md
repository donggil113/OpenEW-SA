# WiSig static receiver-context study

This directory documents the first data-backed Paper 3 experiment authorized after the PR #81 static-relational NO-GO. The study is a static receiver-context domain-generalization experiment for RF fingerprinting. It makes no dynamic, temporal, hypergraph, neuro-symbolic, or uncertainty-gating claim.

## Scientific contract

- Target: transmitter identity, stored only in the external annotation table.
- Allowed relation: equality of target-neutral `receiver_id` within a single train, validation, or test partition.
- Split-only field: `day_id`.
- Forbidden context: transmitter/class equality, source target-bearing paths, packet order, day as an input, receiver-value embeddings, or target-domain metadata crossing a partition boundary.
- Primary endpoint: macro-F1 on five prespecified unseen-receiver folds.
- Secondary endpoint: four leave-one-day-out protocols.
- Seeds: 829, 1829, 2829, 3829, and 4829.

The exact data, split, model, and post-freeze analysis definitions are in `manyrx_conversion_qa.md`, `split_freeze.md`, `experiment_preregistration_v1.md`, `model_config_freeze.md`, and `postfreeze_analysis_protocol.md`.

Final scientific outputs are summarized in `wisig_static_dg_handoff.md`. The executable preregistered decision is recorded in `static_receiver_context_go_no_go.md`, immutable-scope checks in `final_integrity_report.md`, and the bounded manuscript plan in `paper3_manuscript_outline_v1.md`.

## Data boundary

The official ManyRx archive, extracted payload, converted RF tensors, annotations, predictions, checkpoints, and generated analysis products remain outside Git. The code repository contains only software, small configuration files, immutable hashes, protocols, and scientific reports. See `wisig_license_and_distribution_policy.md` for the CC BY-NC-SA 4.0 research-use and attribution boundary.

## Execution outline

1. Verify the official archive and inspect it before extraction.
2. Convert independently to pass A and pass B and require deterministic equivalence.
3. Run full-sample QA and target-proxy audits.
4. Build and freeze support-qualified receiver/day splits.
5. Run source-only smoke tests and freeze model configuration.
6. Execute the checkpointed frozen suite.
7. Audit the complete 530-configuration registry before summarization.
8. Generate descriptive tables, paired deltas, clustered-bootstrap intervals, mechanism controls, and integrity evidence externally.

All executable CLIs live under `scripts/paper3/wisig/`. Every model run records the data-manifest, split, configuration, source-commit, checkpoint, and prediction hashes needed for review and safe resume.

## Frozen external roots

- Converted pass A: `/mnt/d/openew_sa_data/paper3/wisig/converted/pass_a`
- Converted pass B: `/mnt/d/openew_sa_data/paper3/wisig/converted/pass_b`
- Split freeze: `/mnt/d/openew_sa_data/paper3/wisig/analysis/splits_v1`
- Run registry: `/mnt/d/openew_sa_data/paper3/wisig/experiments/wisig_static_dg_v1`
- Final generated analysis: `/mnt/d/openew_sa_data/paper3/wisig/analysis/final_v1`

These roots are local evidence locations, not distributable release paths. Run the integrity verifier before trusting a copied or resumed analysis. The report generator refuses an incomplete 530-configuration grid, configuration-hash drift, missing or mismatched prediction hashes, missing checkpoints, inconsistent training SHAs, or a failed frozen qualification/leakage audit.
