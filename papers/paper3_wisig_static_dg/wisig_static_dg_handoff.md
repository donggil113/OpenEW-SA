# WiSig static receiver-context domain-generalization handoff

## Scientific status

This study asks whether target-neutral, unordered same-receiver context improves transmitter recognition under prespecified unseen-receiver and unseen-day shifts. It is not a dynamic, temporal, hypergraph, neuro-symbolic, or uncertainty-gating experiment. The 140-run PR #81 result remains frozen as an overall static-relational NO-GO and was neither rerun nor tuned.

## Verified data result

The official WiSig ManyRx compact archive was obtained from the UCLA/WiSig release path under the user-approved CC BY-NC-SA 4.0 local noncommercial research gate. The archive is 1,249,528,063 bytes with SHA-256 `d2b23108c3f6f63a10ebbb149d7b08d6e1c1961cf5184926fbab452def3049de`. The official citation is DOI `10.1109/ACCESS.2022.3154790`. Raw and signal-derived payloads remain external and are not redistributed.

Archive inspection found one safe member and no absolute path, traversal, escaping symlink, or executable member. The restricted loader admitted only the expected built-in containers, scalars, and NumPy objects. The official full index contains 9,976,477 non-equalized packet entries over 174 transmitters, 41 receivers, and four acquisition dates. ManyRx contains the official compact subset used here: ten transmitters, 32 receivers, four dates, and 249,666 resolvable non-equalized packets after the official 200-packet per-cell cap. Reconciliation found zero cell-count mismatches, duplicate packet keys, missing compact payloads, or orphan archive records.

Two complete deterministic conversions produced 31 float32 feature shards of shape `(packet, 256, 2)` plus separate acquisition and annotation tables. All 156 deterministic files were byte-identical across pass A and pass B; runtime/state files were intentionally excluded. Full-sample QA passed for all 249,666 rows with unique opaque sample IDs, finite features, matching annotations, valid receiver/day identifiers, complete shards, no target field in acquisition metadata, and no exact source path in model-visible artifacts.

## Verified leakage result

`transmitter_id` is the annotation-only target. `receiver_id` is the only allowed relation and is used only as an equality operator; receiver values are never embedded. `day_id` is split-only. Packet/source indices, storage coordinates, exact paths, transmitter IDs, and packet order are forbidden model context.

The audit-only receiver diagnostic passed: coverage 1.0, 32 groups, weighted target purity 0.102537, normalized mutual information 0.005639, and zero near-deterministic groups. `source_record_index` was correctly classified as a forbidden target proxy. Storage shard identity was strongly target-associated and remains storage-only. All data-quality flags are clear and constant, so they cannot explain differential model error.

## Frozen protocols

All ten compact-subset transmitter classes met the prespecified train/validation/test support thresholds of 100/20/20 packets per class. Five receiver-holdout folds use disjoint train, source-validation, and test receiver groups. Four leave-one-day-out protocols use two training dates, one source-validation date, and one held-out date. One combined receiver-plus-day protocol is a secondary stress test. The external split-freeze SHA-256 is `08561f708862c696b4140876abbc7871af257bf38aab1a7e2728a8de9152e449`; the converted data-manifest SHA-256 is `ffd98dcb8182435c1aaf416c3bb137e6f56f353811e7d1d7a6fc0cc4817ae4b6`.

## Frozen model study

P0 is the independent residual 1-D CNN baseline; P0-WIDE is the capacity-matched independent control. DG-CORAL and DG-GROUPDRO are source-domain baselines. P1 combines the anchor with an unordered same-receiver mean representation. P2 uses permutation-invariant attention over the same-receiver episode. P2-SHUFFLED breaks the receiver relation within each partition while preserving episode-size support, and P2-NULL removes peer context without changing the architecture.

All models use the same non-equalized 256-by-2 I/Q input and frozen per-packet RMS normalization. P0/P1/P2 share the same backbone. The primary context is anchor plus 31 peers; context sizes 8 and 128 are secondary. Retention is reported at 100%, 75%, 50%, 25%, and 0%, with 100% remaining primary. Optimization is AdamW (`5e-4`, weight decay `1e-4`), maximum 30 epochs, patience 8, and source-validation macro-F1 checkpoint selection. Seeds are 829, 1829, 2829, 3829, and 4829.

## Verified experiment result

The frozen grid declared 580 condition entries corresponding to 530 unique executable configurations after exact configuration reuse. All 530 unique runs completed and no run failed. The receiver-holdout primary study comprises 25 fold--seed runs per model (five receiver folds by five seeds).

| Model | Source-validation macro-F1 | Held-out receiver macro-F1 |
|---|---:|---:|
| DG-CORAL | 0.773263 +/- 0.039369 | 0.770310 +/- 0.050996 |
| DG-GroupDRO | 0.707033 +/- 0.034654 | 0.695924 +/- 0.045022 |
| P0 | 0.776129 +/- 0.038149 | 0.770749 +/- 0.048519 |
| P0-WIDE | 0.776200 +/- 0.039693 | 0.773934 +/- 0.045482 |
| P1 | 0.782808 +/- 0.038982 | 0.777142 +/- 0.049828 |
| P2 | 0.797620 +/- 0.031870 | 0.792544 +/- 0.045838 |
| P2-NULL | 0.791748 +/- 0.030607 | 0.787461 +/- 0.042485 |
| P2-SHUFFLED | 0.788746 +/- 0.032115 | 0.781335 +/- 0.046425 |

Mean seed-and-fold-matched held-out deltas were P1 minus P0 `+0.006393`, P2 minus P0 `+0.021795`, P2 minus P1 `+0.015402`, P2 minus P0-WIDE `+0.018610`, P2 minus P2-SHUFFLED `+0.011210`, and P2 minus P2-NULL `+0.005083`. P2 minus P0 was positive in every receiver fold: `+0.027766`, `+0.029602`, `+0.010317`, `+0.023911`, and `+0.017382` for folds 0--4. The source-validation P2-minus-P0 mean was `+0.021490`, with a positive fold mean in all five folds.

The four-fold secondary day-holdout means were `0.893495 +/- 0.026993` for P0 and `0.897316 +/- 0.028074` for P2. The secondary combined receiver-plus-day stress means were `0.433918 +/- 0.027573` for P0, `0.433964 +/- 0.023579` for P2, and `0.434955 +/- 0.032407` for P2-SHUFFLED. Thus the primary receiver-holdout evidence does not extend to a demonstrated combined-shift advantage.

The prespecified 2,000-replicate receiver-fold clustered bootstrap produced descriptive 95% intervals of `[0.015220, 0.027729]` for P2 minus P0, `[0.010992, 0.026280]` for P2 minus P0-WIDE, `[0.004172, 0.017231]` for P2 minus P2-SHUFFLED, and `[-0.000648, 0.010575]` for P2 minus P2-NULL. Receiver folds were resampled as top-level clusters while paired seed/model differences were preserved. No statistical-significance claim is made.

## Controls and diagnostic result

P2 exceeded P2-SHUFFLED on average and in four of five receiver folds; fold 2 had a small negative difference of `-0.001888`. This supports mechanism specificity at the aggregate preregistered level without implying a universal per-fold gain. P2 also exceeded both capacity-matched P0-WIDE and architecture-matched P2-NULL on average; the P2-minus-P2-NULL descriptive interval included zero.

The held-out macro-F1 retention curve was non-monotonic: `0.787461`, `0.790036`, `0.789048`, `0.783740`, and `0.792544` at 0%, 25%, 50%, 75%, and 100%. It therefore does not support a smooth dose--response claim, and no retention level was selected post hoc. Context-size means were `0.790113`, `0.792544`, and `0.788107` at sizes 8, 32, and 128; the frozen primary size remains 32 regardless of these secondary results.

Primary P2 context coverage was `0.999996`, the isolated-anchor fraction was `0.000004`, and mean episode size was `31.982425`. P2 attention entropy averaged `3.092659`, corresponding to `22.455140` effective context contributors; shuffled context averaged entropy `3.341872` and `28.359017` effective contributors. These are association diagnostics, not causal explanations.

The frozen post-prediction audit found receiver error rates ranging from `0.085128` to `0.404975` across the 32 receivers and day-level error rates from `0.192335` to `0.235723`. These diagnostics were not used to modify data, splits, models, or relations. Class-support analysis retained all ten preregistered transmitters and did not change class inclusion.

## Compute and reproducibility

Mean receiver-primary parameter counts were 65,034 for P0, 75,419 for P0-WIDE, 73,290 for P1, and 75,403 for P2. P0-WIDE and P2 differ by 16 parameters (`0.0212%`), satisfying the frozen +/-5% capacity criterion. Mean training/selection times were `30.336 s`, `31.619 s`, `45.498 s`, and `50.492 s`, respectively. Mean inference throughput was approximately 491,672 samples/s for P0, 525,696 for P0-WIDE, 270,047 for P1, and 256,092 for P2. Corresponding mean peak GPU allocations were approximately 166.5, 166.7, 168.9, and 169.0 MB.

The no-model I/O benchmark read 627,061,906 converted bytes, including 511,315,968 feature bytes. Bundle loading took `2.045 s`; deterministic context assembly averaged `0.078 s` across receiver folds (maximum `0.151 s`), or approximately 1,059,634 samples/s. All checkpoints, prediction files, and run records are external. Every completed prediction and checkpoint was re-hashed, every configuration hash was recomputed, and every run used training commit `1fc56737ba4376a0496437324cf1d3b34bb47373`.

## Integrity

The final fail-closed audit passed. It found exactly 530 expected unique configurations, no missing or unexpected run, no duplicate configuration hash, no malformed or nonterminal record, no missing checkpoint or prediction, and no prediction/checkpoint hash mismatch. Every run referenced one frozen converted-data manifest and the frozen training commit.

The raw archive hash, pass-A and pass-B manifest hashes, and split-freeze hash matched their preregistered values. All 156 deterministic conversion outputs remained byte-identical across the two passes. Git diffs against PR #83 base `8d7d3cfca85a200a781fada3c5ca15dbaef3cfe2` confirmed Paper 1, Paper 2, and PR #80--#83 artifacts unchanged. PR #81 was not rerun. No temporal, dynamic, hypergraph, uncertainty-gating, or neuro-symbolic model was executed.

## Interpretation

**VERIFIED RESULT.** All six preregistered GO criteria passed. P2 improved source validation in every receiver fold; did not degrade held-out receiver performance; exceeded shuffled context and capacity-matched P0-WIDE on average; benefited all five receiver folds relative to P0; and passed every leakage/integrity gate. The resulting bounded verdict is **GO for static receiver-context domain generalization on the official WiSig ManyRx compact subset**.

**INTERPRETATION.** The primary result is consistent with an advantage from target-neutral, same-receiver context beyond parameter count and generic pooled context. It does not establish that every receiver benefits, that more retained peers always help, or that attention is causal. The neutral combined-shift stress result, the non-monotonic retention curve, and the modest day-holdout difference delimit the claim.

**INTERPRETATION.** This result does not reverse PR #81. Instead, PR #81 remains a cautionary contrast: coarse equality metadata in the existing OpenEW-SA artifacts did not yield reliable relational generalization, motivating the leakage-audited dataset qualification and source validation used here.

**UNRESOLVED.** Replication on the full 174-transmitter/41-receiver index or an independently collected receiver-diverse corpus remains necessary before claiming broad receiver-context generality. Temporal, dynamic, uncertainty-gating, neuro-symbolic, and hypergraph extensions remain unauthorized by this study.

## Unresolved and human-review items

- Distribution of the raw archive, extracted payload, converted tensors, annotations, checkpoints, or predictions remains prohibited by the study policy absent a separate license review.
- The compact study covers ten of the 174 indexed WiSig transmitters and 32 of 41 indexed receivers; generalization beyond that official compact payload is unresolved.
- WiSig supplies no validated acquisition timestamps. Packet order is target-nested, so temporal and dynamic claims remain NO-GO regardless of static results.
- Attention weights, where reported, are association diagnostics and not causal explanations.
