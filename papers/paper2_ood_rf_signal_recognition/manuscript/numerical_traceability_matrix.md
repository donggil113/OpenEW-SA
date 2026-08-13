# Paper 2 Numerical Traceability Matrix

## Scope

This matrix covers every empirical numerical statement transcribed into `paper2_full_manuscript_draft.md`. Each value is mapped to a verified CSV row by explicit key fields rather than by physical row number, so sorting the source table does not break provenance.

The verified source root is:

```text
/mnt/d/openew_sa_data/paper2/experiments/v3_publication_analysis_20260807/tables
```

Source aliases:

- `CI`: `paper2_v3_bootstrap_confidence_intervals.csv`
- `PAIR`: `paper2_v3_paired_differences.csv`
- `PUB`: `paper2_v0_v3_publication_summary.csv`

All point estimates and interval bounds are reproduced to six decimal places, matching the publication tables. Structural numbering, version identifiers such as `v0`-`v3`, mathematical constants in method definitions, and symbolic class/domain identifiers such as `0000` and `day2` are not empirical measurements. The `FPR95` token is a metric identifier and maps to rows whose `metric` or `score_method` fields define that quantity.

## Evaluation Counts And Bootstrap Configuration

| Trace ID | Manuscript location | Numerical statement | Source CSV | Row identifier | Metric | Source column(s) |
| --- | --- | --- | --- | --- | --- | --- |
| N001 | Datasets, Table 1, ElectroSense | ID 5,840; OOD 16,550; total 22,390 | `PUB` | `stage=v3_fusion; dataset=electrosense; protocol=class_ood; score_method=ts_entropy_cosine_euclidean` | Evaluation sample counts | `n_id`; `n_ood`; `n_samples` |
| N002 | Datasets, Table 1, DeepSense | ID 3,200; OOD 16,000; total 19,200 | `PUB` | `stage=v3_fusion; dataset=deepsense; protocol=day2_ood; score_method=ts_entropy_cosine_euclidean` | Evaluation sample counts | `n_id`; `n_ood`; `n_samples` |
| N003 | Datasets, Table 1, JamShield | ID 14,534; OOD 19,817; total 34,351 | `PUB` | `stage=v3_fusion; dataset=jamshield; protocol=scenario_ood; score_method=ts_entropy_cosine_euclidean` | Evaluation sample counts | `n_id`; `n_ood`; `n_samples` |
| N004 | Methods, bootstrap analysis; Results, Table 2 heading/caption | 1,000 successful replicates; 95% confidence level | `CI` | All rows; values are invariant across dataset, method, and metric | Bootstrap configuration represented in result rows | `successful_replicates`; `confidence_level` |
| N017 | Results, DeepSense no-skill context | OOD prevalence and no-skill AUPR-OOD baseline 0.833333 | `PUB` | `stage=v3_fusion; dataset=deepsense; protocol=day2_ood; score_method=ts_entropy_cosine_euclidean` | Derived prevalence anchor | `n_ood / n_samples = 16000 / 19200` |
| N018 | Results, DeepSense no-skill context | All-OOD trivial detection-accuracy baseline 0.833333 | `PUB` | `stage=v3_fusion; dataset=deepsense; protocol=day2_ood; score_method=ts_entropy_cosine_euclidean` | Derived majority-class anchor | `max(n_id, n_ood) / n_samples = 16000 / 19200` |

## Prespecified Primary Point Estimates And Intervals

| Trace ID | Manuscript location | Dataset | Reported value | Source CSV | Row identifier | Metric | Source column(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| N005 | Results, Table 2 | ElectroSense | AUROC 0.857037 [0.851138, 0.862585] | `CI` | `dataset=electrosense; method=v3_primary; metric=auroc` | AUROC | `point_estimate`; `ci_lower`; `ci_upper` |
| N006 | Results, Table 2 | ElectroSense | AUPR-OOD 0.934429 [0.930849, 0.937570] | `CI` | `dataset=electrosense; method=v3_primary; metric=aupr_ood` | AUPR-OOD | `point_estimate`; `ci_lower`; `ci_upper` |
| N007 | Results, Table 2 | ElectroSense | FPR95 0.434589 [0.420886, 0.447774] | `CI` | `dataset=electrosense; method=v3_primary; metric=fpr95` | FPR95 | `point_estimate`; `ci_lower`; `ci_upper` |
| N008 | Results, Table 2 | ElectroSense | Detection accuracy 0.856632 [0.853235, 0.860741] | `CI` | `dataset=electrosense; method=v3_primary; metric=detection_accuracy` | Detection accuracy | `point_estimate`; `ci_lower`; `ci_upper` |
| N009 | Results, Table 2 | DeepSense | AUROC 0.352958 [0.340919, 0.364553] | `CI` | `dataset=deepsense; method=v3_primary; metric=auroc` | AUROC | `point_estimate`; `ci_lower`; `ci_upper` |
| N010 | Results, Table 2 | DeepSense | AUPR-OOD 0.737936 [0.733647, 0.742146] | `CI` | `dataset=deepsense; method=v3_primary; metric=aupr_ood` | AUPR-OOD | `point_estimate`; `ci_lower`; `ci_upper` |
| N011 | Results, Table 2 | DeepSense | FPR95 0.992188 [0.989062, 0.995313] | `CI` | `dataset=deepsense; method=v3_primary; metric=fpr95` | FPR95 | `point_estimate`; `ci_lower`; `ci_upper` |
| N012 | Results, Table 2 | DeepSense | Detection accuracy 0.833490 [0.833333, 0.833750] | `CI` | `dataset=deepsense; method=v3_primary; metric=detection_accuracy` | Detection accuracy | `point_estimate`; `ci_lower`; `ci_upper` |
| N013 | Results, Table 2 | JamShield | AUROC 0.657625 [0.652294, 0.663324] | `CI` | `dataset=jamshield; method=v3_primary; metric=auroc` | AUROC | `point_estimate`; `ci_lower`; `ci_upper` |
| N014 | Results, Table 2 | JamShield | AUPR-OOD 0.710403 [0.704694, 0.716541] | `CI` | `dataset=jamshield; method=v3_primary; metric=aupr_ood` | AUPR-OOD | `point_estimate`; `ci_lower`; `ci_upper` |
| N015 | Results, Table 2 | JamShield | FPR95 0.927205 [0.922869, 0.931402] | `CI` | `dataset=jamshield; method=v3_primary; metric=fpr95` | FPR95 | `point_estimate`; `ci_lower`; `ci_upper` |
| N016 | Results, Table 2 | JamShield | Detection accuracy 0.634887 [0.630957, 0.639196] | `CI` | `dataset=jamshield; method=v3_primary; metric=detection_accuracy` | Detection accuracy | `point_estimate`; `ci_lower`; `ci_upper` |

## Paired Interval Decisions

Each row below maps all four Table 3 cells for one fixed comparison. The sign displayed in the manuscript is derived from `point_difference_left_minus_right`; the “excludes zero” or “includes zero” text is copied from `interval_excludes_zero` and checked against `ci_lower` and `ci_upper`. These mappings also cover the corresponding qualitative statements in the paired-comparison Results subsection.

| Trace ID | Dataset | Manuscript comparison | Source CSV | Row identifier | Metric rows | Source column(s) |
| --- | --- | --- | --- | --- | --- | --- |
| P001 | ElectroSense | Primary - TS entropy | `PAIR` | `dataset=electrosense; comparison=v3_primary_vs_temperature_scaled_entropy` | `auroc`; `aupr_ood`; `fpr95`; `detection_accuracy` | `point_difference_left_minus_right`; `ci_lower`; `ci_upper`; `interval_excludes_zero` |
| P002 | ElectroSense | Primary - NC cosine | `PAIR` | `dataset=electrosense; comparison=v3_primary_vs_nearest_centroid_cosine` | `auroc`; `aupr_ood`; `fpr95`; `detection_accuracy` | `point_difference_left_minus_right`; `ci_lower`; `ci_upper`; `interval_excludes_zero` |
| P003 | ElectroSense | Primary - NC Euclidean | `PAIR` | `dataset=electrosense; comparison=v3_primary_vs_nearest_centroid_euclidean` | `auroc`; `aupr_ood`; `fpr95`; `detection_accuracy` | `point_difference_left_minus_right`; `ci_lower`; `ci_upper`; `interval_excludes_zero` |
| P004 | ElectroSense | Exploratory four-component - primary | `PAIR` | `dataset=electrosense; comparison=four_component_exploratory_vs_v3_primary` | `auroc`; `aupr_ood`; `fpr95`; `detection_accuracy` | `point_difference_left_minus_right`; `ci_lower`; `ci_upper`; `interval_excludes_zero` |
| P005 | DeepSense | Primary - TS entropy | `PAIR` | `dataset=deepsense; comparison=v3_primary_vs_temperature_scaled_entropy` | `auroc`; `aupr_ood`; `fpr95`; `detection_accuracy` | `point_difference_left_minus_right`; `ci_lower`; `ci_upper`; `interval_excludes_zero` |
| P006 | DeepSense | Primary - NC cosine | `PAIR` | `dataset=deepsense; comparison=v3_primary_vs_nearest_centroid_cosine` | `auroc`; `aupr_ood`; `fpr95`; `detection_accuracy` | `point_difference_left_minus_right`; `ci_lower`; `ci_upper`; `interval_excludes_zero` |
| P007 | DeepSense | Primary - NC Euclidean | `PAIR` | `dataset=deepsense; comparison=v3_primary_vs_nearest_centroid_euclidean` | `auroc`; `aupr_ood`; `fpr95`; `detection_accuracy` | `point_difference_left_minus_right`; `ci_lower`; `ci_upper`; `interval_excludes_zero` |
| P008 | DeepSense | Exploratory four-component - primary | `PAIR` | `dataset=deepsense; comparison=four_component_exploratory_vs_v3_primary` | `auroc`; `aupr_ood`; `fpr95`; `detection_accuracy` | `point_difference_left_minus_right`; `ci_lower`; `ci_upper`; `interval_excludes_zero` |
| P009 | JamShield | Primary - TS entropy | `PAIR` | `dataset=jamshield; comparison=v3_primary_vs_temperature_scaled_entropy` | `auroc`; `aupr_ood`; `fpr95`; `detection_accuracy` | `point_difference_left_minus_right`; `ci_lower`; `ci_upper`; `interval_excludes_zero` |
| P010 | JamShield | Primary - NC cosine | `PAIR` | `dataset=jamshield; comparison=v3_primary_vs_nearest_centroid_cosine` | `auroc`; `aupr_ood`; `fpr95`; `detection_accuracy` | `point_difference_left_minus_right`; `ci_lower`; `ci_upper`; `interval_excludes_zero` |
| P011 | JamShield | Primary - NC Euclidean | `PAIR` | `dataset=jamshield; comparison=v3_primary_vs_nearest_centroid_euclidean` | `auroc`; `aupr_ood`; `fpr95`; `detection_accuracy` | `point_difference_left_minus_right`; `ci_lower`; `ci_upper`; `interval_excludes_zero` |
| P012 | JamShield | Exploratory four-component - primary | `PAIR` | `dataset=jamshield; comparison=four_component_exploratory_vs_v3_primary` | `auroc`; `aupr_ood`; `fpr95`; `detection_accuracy` | `point_difference_left_minus_right`; `ci_lower`; `ci_upper`; `interval_excludes_zero` |

## Stage-Wise Table Mapping

Table 4 is intentionally inserted from `PUB` rather than manually transcribed into the prose. Its complete row identity is the tuple:

```text
(stage, dataset, protocol, model, score_method)
```

Its reported metrics map directly to `auroc`, `aupr_ood`, `fpr95`, and `detection_accuracy`; evaluation counts map to `n_id`, `n_ood`, and `n_samples`; analysis terminology maps to `analysis_role`, `score_orientation`, and `detection_accuracy_note`. No Table 4 point estimate is duplicated elsewhere in the manuscript unless it is independently mapped above.

## Validation Rules

- Table 1 counts must match `PUB` for every v3 primary row and satisfy `n_id + n_ood = n_samples`.
- Every Table 2 point estimate and bound must match the keyed `CI` row after six-decimal formatting.
- Every Table 3 sign must match the sign of `point_difference_left_minus_right`.
- Every Table 3 interval decision must match `interval_excludes_zero` and the interval bounds.
- Every row described as evaluation-descriptive must have `threshold_note=evaluation-descriptive` in `CI` or `PAIR`, or the equivalent `detection_accuracy_note` in `PUB`.
- Primary, exploratory, and comparator labels must match `analysis_role` in the source tables.
- Derived DeepSense no-skill anchors N017 and N018 must equal the ratios of the frozen N002 evaluation counts and are descriptive quantities, not additional statistical tests.
