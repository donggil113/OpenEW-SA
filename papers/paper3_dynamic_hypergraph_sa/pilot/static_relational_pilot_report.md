# OpenEW-SA Paper 3 static relational M0–M2 pilot report

## Technical summary

**VERIFIED RESULT.** The complete frozen pilot executed 140/140 checkpointed runs successfully on the three Paper 1 domain-holdout families. All 140 held-out prediction archives reconcile exactly to their metadata metrics, and the post-run hashes of Paper 1, Paper 2, and the three processed datasets match their pre-run hashes. The preregistered outcome is **NO-GO** for using the tested static equality relations as the central Paper 3 contribution.

JamShield station equality reduced both source-validation and held-out macro-F1 relative to the independent-sample baseline on average. ElectroSense receiver/date relations improved source-validation macro-F1 but produced a small mean held-out degradation and did not clear the relation-specific shuffled-control margin. DeepSense remained an M0-only cross-day reference because the feasibility audit found no defensible relation.

The frozen run root is `/mnt/d/openew_sa_data/paper3/experiments/static_relational_m0_m2_20260902T000000Z`. Generated CSVs, figures, and integrity reports are in `/mnt/d/openew_sa_data/paper3/pilot_analysis/` and are intentionally outside Git.

## 1. Scientific question

Can deployment-available, label-independent equality context improve RF situation assessment under frozen unseen scenario, jammer-family, or sensor shifts?

This pilot tests only static relations verified in the preceding metadata audit. It does not test dynamic hypergraphs, temporal reasoning, uncertainty-aware gating, or neuro-symbolic constraints.

## 2. Frozen protocols

The suite preserved the Paper 1 holdouts:

| Protocol | Train | Source validation | Held-out | Held-out definition |
|---|---:|---:|---:|---|
| JamShield scenario | 58,138 | 14,531 | 19,817 | frozen scenario domains plus `data_benign_4` |
| JamShield reactive family | 50,194 | 12,546 | 29,746 | frozen reactive-jammer family plus `data_benign_4` |
| ElectroSense sensor | 31,000 | 7,750 | 7,000 | `alcorcon1`, `bcn-L`, and `Geneva` |
| DeepSense cross-day | 12,800 | 3,200 | 16,000 | day1 source to day2 held-out |

Source validation was a deterministic 20% source-only split stratified by source domain and target class with split seed 20260901. Labels were used for splitting and supervision, never for relation construction. No edge or hyperedge crossed train, validation, or held-out partitions.

## 3. Exact relation whitelist

- JamShield: `rx_id` equality, exposed as relation type `station`.
- ElectroSense: `rx_id` and reconstructed `source_date_id` equality, exposed as `receiver`, `date`, and their joint `receiver_date` type.
- DeepSense: no allowed relation.

`domain_id` was split-only. Frequency, target class, OOD/ID, attack state, correctness, predictions, source file/path, and target-pure scenario fields were forbidden. Relation values were grouping operators only; no receiver, station, or date value embeddings were learned.

## 4. M0/M1/M2 definitions

M0 is an independent-sample control: a two-hidden-layer tabular MLP for JamShield, a two-hidden-layer PSD MLP for ElectroSense, and the existing-capacity 1-D I/Q CNN family for DeepSense.

M1 uses the same base node encoder but adds pairwise mean messages from deterministic, capped same-relation neighborhoods. Self is excluded and no clique is materialized.

M2 uses typed incidence/group means. JamShield has one station type. ElectroSense keeps receiver, date, and receiver-date transformations distinct. The implementation reduces groups with pure PyTorch indexing/scatter-style operations and does not expand an O(N²) adjacency matrix.

## 5. Implementation details

The full suite used PyTorch 2.11.0+cu128 on one NVIDIA RTX 4090. Models were trained for 10 epochs with AdamW, learning rate 0.001, weight decay 0.01, hidden width 128, and dropout 0.1. Batch sizes were 64 for JamShield and 128 for ElectroSense/DeepSense. JamShield used source-training class weights. The selected checkpoint maximized source-validation macro-F1.

Every relation group was deterministically hash-chunked to a maximum context size of 64 using dataset, partition, relation type/value, sample ID, and seed. The limit was frozen from resource profiling before held-out metrics were opened. All target probabilities and sample IDs were serialized before held-out labels were read for metric computation.

## 6. Seed policy

The exact paired seeds were 829, 1829, 2829, 3829, and 4829. Python, NumPy, Torch, and CUDA seeds were set for each run. No seed was replaced or selected based on performance.

## 7. Checkpoint and resume policy

Each run wrote atomic metadata, checkpoint, metric, and prediction artifacts. Completion was reusable only when config hash, source hash, artifact hashes, and split hashes matched. A post-suite resume invocation skipped all 140 runs as compatible. Artifact mismatch, leakage-contract violation, split contamination, label-dependent incidence, or corrupted source data were suite-stopping errors.

The suite contained 50 primary runs, 15 shuffled-relation controls, 60 additional non-100% retention runs, and 15 ElectroSense component ablations. Six source-only smoke runs passed before the freeze commit. An initial smoke-only loader defect for nested JamShield class-name metadata was corrected before the design freeze; no full run failed.

## 8. Primary results

**VERIFIED RESULT.** Values are five-seed mean ± sample standard deviation. No inferential significance claim is made.

| Protocol | Stage | Source-validation macro-F1 | Held-out macro-F1 |
|---|---|---:|---:|
| JamShield scenario | M0 | 0.988761 ± 0.001230 | 0.555165 ± 0.075781 |
| JamShield scenario | M1 | 0.985679 ± 0.002205 | 0.480810 ± 0.028689 |
| JamShield scenario | M2 | 0.985667 ± 0.002395 | 0.476876 ± 0.040576 |
| JamShield reactive | M0 | 0.987234 ± 0.000668 | 0.682252 ± 0.043125 |
| JamShield reactive | M1 | 0.983751 ± 0.002263 | 0.659341 ± 0.040645 |
| JamShield reactive | M2 | 0.983898 ± 0.002008 | 0.662984 ± 0.040606 |
| ElectroSense sensor | M0 | 0.995106 ± 0.000348 | 0.452858 ± 0.033506 |
| ElectroSense sensor | M1 | 0.999476 ± 0.000112 | 0.450970 ± 0.028290 |
| ElectroSense sensor | M2 | 0.999398 ± 0.000286 | 0.446144 ± 0.045065 |
| DeepSense cross-day | M0 | 0.717977 ± 0.005437 | 0.217815 ± 0.000767 |

The full seed-level table includes mean, standard deviation, median, minimum, and maximum in `primary_results_summary.csv`; individual results are in `primary_results_per_seed.csv`.

## 9. Source-validation results

**VERIFIED RESULT.** The paired M2-minus-M0 source-validation changes were -0.003094 for JamShield scenario, -0.003336 for JamShield reactive, and +0.004292 for ElectroSense. Thus neither JamShield protocol met the preregistered source-support condition. ElectroSense met it, but source macro-F1 was already above 0.995 for M0, limiting the practical room for improvement.

**INTERPRETATION.** The JamShield negative conclusion is not a target-only failure. ElectroSense shows that the relational architecture changes source fitting, but this alone does not establish unseen-sensor benefit.

## 10. Unseen-domain results

**VERIFIED RESULT.** Mean paired M2-minus-M0 held-out changes were -0.078289 for JamShield scenario, -0.019267 for JamShield reactive, and -0.006714 for ElectroSense. The first two exceed the frozen 0.01 non-degradation tolerance; ElectroSense remains within it.

DeepSense M0 cross-day macro-F1 was 0.217815 ± 0.000767. No M1/M2 DeepSense run was constructed.

**INTERPRETATION.** The tested station relation materially harms scenario generalization and modestly harms reactive-family generalization. ElectroSense is heterogeneous across seeds and does not show a mean relational gain on the target sensors.

## 11. Shuffled-relation null control

| Protocol | Actual M2 held-out | Shuffled M2 held-out | Actual − shuffled |
|---|---:|---:|---:|
| JamShield scenario | 0.476876 | 0.495386 | -0.018510 |
| JamShield reactive | 0.662984 | 0.702304 | -0.039320 |
| ElectroSense sensor | 0.446144 | 0.444197 | +0.001947 |

**VERIFIED RESULT.** The corresponding source-validation actual-minus-shuffled gaps were -0.002616, -0.001812, and +0.003605. None cleared the frozen +0.005 margin on both source validation and held-out data.

**INTERPRETATION.** Generic pooling cannot be ruled out for ElectroSense, while actual station equality was less useful than the label-independent shuffled control for both JamShield holdouts.

## 12. Relation-corruption results

| Retention | JamShield scenario | JamShield reactive | ElectroSense sensor |
|---:|---:|---:|---:|
| 0% | 0.568432 | 0.704566 | 0.450806 |
| 25% | 0.598605 | 0.706112 | 0.458260 |
| 50% | 0.614393 | 0.679284 | 0.442196 |
| 75% | 0.536988 | 0.680369 | 0.465086 |
| 100% | 0.476876 | 0.662984 | 0.446144 |

**VERIFIED RESULT.** These are held-out means, reported descriptively. The source-validation retention Spearman coefficients were -0.90, -1.00, and +1.00, respectively. Full-minus-zero source-validation changes were -0.002999, -0.002627, and +0.004165.

**INTERPRETATION.** JamShield source evidence becomes worse as relations are retained. ElectroSense has orderly source dependence but a non-monotone held-out curve. No retention level is selected.

## 13. Component ablations

JamShield's sole component is station equality; its no-relation M2 control is the 0% retention condition. Mean held-out macro-F1 increased from 0.476876 to 0.568432 for scenario holdout and from 0.662984 to 0.704566 for reactive holdout when station incidences were removed.

For ElectroSense, held-out means were 0.446144 for all three types, 0.476436 for receiver only, 0.451487 for date only, 0.465096 for receiver-date only, and 0.450806 for no relations.

**UNRESOLVED.** These target results cannot justify retrospective relation selection. The receiver-only result would need a separately motivated, source-frozen replication; it is not a new primary method from this pilot.

## 14. Computational cost

| Protocol | Stage | Parameters | Mean training time (s) | Mean inference time (s) | Mean context construction (s) |
|---|---|---:|---:|---:|---:|
| JamShield scenario | M0 / M1 / M2 | 5,122 / 21,506 / 21,506 | 15.01 / 33.65 / 31.54 | 0.13 / 0.48 / 0.48 | 0.00 / 5.10 / 5.07 |
| JamShield reactive | M0 / M1 / M2 | 5,122 / 21,506 / 21,506 | 12.68 / 28.33 / 28.30 | 0.18 / 0.69 / 0.71 | 0.00 / 4.50 / 4.51 |
| ElectroSense sensor | M0 / M1 / M2 | 66,438 / 99,206 / 115,590 | 5.49 / 33.97 / 40.80 | 0.04 / 0.34 / 0.42 | 0.00 / 7.15 / 9.82 |

Peak allocated GPU memory for primary runs was approximately 18.3 MB for JamShield M0, 22.9 MB for JamShield M1/M2, 19.6 MB for ElectroSense M0, 51.1 MB for M1, and 55.1 MB for M2. The complete 140-run suite spanned 3,992.4 seconds (1 h 6 min 32.4 s) from earliest run start to latest run end on the stated hardware.

**INTERPRETATION.** Relational processing increased training time roughly two- to seven-fold without producing a supported overall generalization benefit.

## 15. Failure analysis

No full run failed and no non-finite output occurred. All completed run metadata passed resume compatibility. Before the freeze commit, an initial smoke invocation exposed a loader mismatch because JamShield `labels.json` stores class names by label column. The loader was corrected to select the dataset target's nested class-name list; all six source-only smoke runs then passed. Held-out smoke metrics remained disabled.

## 16. Leakage audit

Tests and runtime contracts rejected `domain_id`, target/label/OOD/correctness/prediction fields, ElectroSense frequency fields, and all DeepSense relation requests. Relation plans were constructed from metadata restricted structurally to sample ID plus whitelisted equality keys. Changing labels leaves incidence unchanged. Corruption and shuffle masks depend on stable hashes, never labels.

Every context was built independently within train, source-validation, or held-out partitions. Held-out receiver values require no train-seen categorical embedding. The runner saved 140 prediction archives containing all sample IDs and domain IDs before metrics were computed.

## 17. Integrity verification

**VERIFIED RESULT.** Prediction-level reconciliation covered all 140 archives. Each archive had the exact frozen held-out ID set, no duplicate IDs, matching domains, finite normalized probabilities, and zero difference between independently recomputed and stored macro-F1, balanced accuracy, accuracy, and ECE.

Post-run SHA-256 tree digests exactly match pre-run values:

- processed JamShield: `29413b71e344b487363950b4cc75daf05fc9dfcc53ad45356d03e22d92aa972b`
- processed DeepSense: `d5957d470f00a1ece62a0330d338f608ab338ed97011b94733501431679da9ce`
- processed ElectroSense: `f76f33ad9ea5521fe21738e0d23a25ca2c97fa26c5f125f2c519dcfc274f3f64`
- Paper 1 frozen tree: `736fd7dabb945e208419f1f16c5e37a9070df3472b239b991781fede494a8a31`
- Paper 2 frozen tree: `9c8031c7aa5812521d9c4b6b829381752d176e099624a5a7808ed09c70925bf0`

No dataset was downloaded, no Paper 1/Paper 2 experiment or bootstrap analysis was rerun, no test-driven relation was introduced, and no M3/M4/M5 experiment ran.

## 18. Limitations and robustness

- Equality metadata are coarse. All full-relation held-out nodes had coverage 1.0, but every raw group exceeded the 64-node cap and was deterministically chunked.
- JamShield has seven station groups; five are mixed-label and two are single-target in the frozen artifact. Target purity was diagnostic-only and never entered a model.
- ElectroSense held-out data contain three receiver groups, four date groups, and five receiver-date groups; the full artifact has 40 receiver groups, 19 date groups, and 45 receiver-date groups.
- Context chunks are static acquisition batches, not temporal sequences.
- Five seeds characterize variability but do not support significance claims.
- This pilot assesses only the frozen architectures and budgets; it does not establish that all possible relational models fail.
- Target metrics were necessarily read for final evaluation and ablation reporting but were never used to modify the frozen model, context size, relation whitelist, or seed set.

## 19. GO/NO-GO conclusion

**VERIFIED RESULT.** JamShield scenario is NO-GO; JamShield reactive is NO-GO; ElectroSense is CONDITIONAL GO; overall static relational Paper 3 is **NO-GO** under the preregistered rule.

**INTERPRETATION.** The available equality relations are insufficient as a general cross-dataset basis for “Relational Domain Generalization for RF Situation Assessment.” The strongest defensible conclusion is negative: high relation coverage and efficient typed aggregation do not imply domain-generalization value, and relation-specific null controls are necessary.

No `paper3_outline_v0.md` is created because the overall result is NO-GO.

## 20. Recommended next experiment

Do not run dynamic, uncertainty-gated, or neuro-symbolic extensions on these relations. The next scientific action should be a prospective acquisition/metadata phase that records label-independent capture session, order/time, channel/band, receiver/site, and operational context. After verifying that these fields are inference-available and not target-pure, freeze a new relational protocol with source-only design decisions and independent held-out domains.

## Exploratory artifact map

- Primary table: `/mnt/d/openew_sa_data/paper3/pilot_analysis/primary_results_summary.csv`
- Seed-level results: `/mnt/d/openew_sa_data/paper3/pilot_analysis/primary_results_per_seed.csv`
- Paired descriptive differences: `/mnt/d/openew_sa_data/paper3/pilot_analysis/paired_seed_differences.csv`
- Shuffled/retention source: `/mnt/d/openew_sa_data/paper3/pilot_analysis/run_registry.csv` and run metadata
- Corruption table: `/mnt/d/openew_sa_data/paper3/pilot_analysis/relation_corruption_results.csv`
- Ablation table: `/mnt/d/openew_sa_data/paper3/pilot_analysis/relation_ablation_results.csv`
- Complexity table: `/mnt/d/openew_sa_data/paper3/pilot_analysis/complexity_summary.csv`
- Integrity: `/mnt/d/openew_sa_data/paper3/pilot_analysis/pre_run_integrity.json` and `post_run_integrity.json`
- Six figures: matching `paper3_*.png` and `paper3_*.pdf` files in the same analysis directory.

## Human-review questions

**UNRESOLVED.** A human decision is required on whether the negative pilot is valuable as a methods/benchmark caution, or whether Paper 3 should pause until prospectively richer metadata exist. Any ElectroSense receiver-only replication must be framed and frozen independently; it must not be presented as a selected winner from this target-visible ablation.
