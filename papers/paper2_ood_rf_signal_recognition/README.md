# Uncertainty-Calibrated Multi-View RF Signal Recognition for Open-Set Electromagnetic Spectrum Monitoring

This folder scaffolds Paper 2 experiments for OOD-aware RF signal recognition on top of the
OpenEW-SA converted artifact format. The initial scope is intentionally lightweight: protocol
configs, split generation, calibration metrics, OOD detection metrics, and risk-coverage curves.
Model-specific artifact integration can be added after the Paper 2 training pipeline is selected.

## Directory Layout

```text
papers/paper2_ood_rf_signal_recognition/
  README.md
  outline.md
  configs/
    manifest_build.yaml
    class_ood.yaml
    domain_ood.yaml
    hybrid_ood.yaml
  scripts/
    build_paper2_manifest.py
    generate_ood_splits.py
    train_baseline_classifier.py
    temperature_scaling.py
    baseline_ood_scores.py
    feature_distance_ood_scores.py
    entropy_scores_from_predictions.py
    fuse_ood_scores.py
    calibration_metrics.py
    ood_detection_metrics.py
    risk_coverage_curves.py
    report_v0_results.py
    run_v2_distance_experiments.sh
    run_v3_fusion_experiments.sh
```

## OpenEW-SA Artifact Assumptions

The scaffold reuses the repository's converted dataset convention:

```text
data/processed/<dataset>/
  metadata.csv
  features.npy or features.pt
  labels.json
```

The manifest builder reads each artifact directory and emits a unified Paper 2 CSV with:

```text
sample_id,dataset_source,task,label,domain_id,input_type,feature_path,feature_index,
split_hint,source_artifact_dir
```

The OOD split script can consume either the unified Paper 2 manifest or a raw OpenEW-SA
`metadata.csv`. It preserves all input columns in its output split manifests.

## Manifest Generation

Build the full manifest from the configured JamShield, DeepSense, and ElectroSense artifacts:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\build_paper2_manifest.py `
  --config papers\paper2_ood_rf_signal_recognition\configs\manifest_build.yaml
```

Smoke-test the manifest build without writing outputs:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\build_paper2_manifest.py `
  --config papers\paper2_ood_rf_signal_recognition\configs\manifest_build.yaml `
  --limit 500 `
  --dry-run
```

## Class-OOD Split Generation

Generate class-OOD splits from the unified manifest:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\generate_ood_splits.py `
  --manifest D:\openew_sa_data\paper2\manifests\paper2_manifest.csv `
  --output-dir D:\openew_sa_data\paper2\splits\class_ood `
  --protocol class_ood `
  --label-column label `
  --known-classes "normal,0000,dab,fm" `
  --ood-classes "abnormal_interference,1111,gsm,lte"
```

This writes `class_ood_train.csv`, `class_ood_val.csv`, `class_ood_test_id.csv`, and
`class_ood_test_ood.csv`.

## Domain-OOD Split Generation

Generate domain-OOD splits from the unified manifest:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\generate_ood_splits.py `
  --manifest D:\openew_sa_data\paper2\manifests\paper2_manifest.csv `
  --output-dir D:\openew_sa_data\paper2\splits\domain_ood `
  --protocol domain_ood `
  --label-column label `
  --domain-column domain_id `
  --train-domains "day1,alcorcon1" `
  --ood-domains "day2,barcelona1"
```

This writes `domain_ood_train.csv`, `domain_ood_val.csv`, `domain_ood_test_id.csv`, and
`domain_ood_test_ood.csv`.

## Baseline Classifier Training

Train a nearest-centroid ID classifier from split manifests and write validation/test predictions:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\train_baseline_classifier.py `
  --train-csv D:\openew_sa_data\paper2\splits\class_ood\class_ood_train.csv `
  --val-csv D:\openew_sa_data\paper2\splits\class_ood\class_ood_val.csv `
  --test-id-csv D:\openew_sa_data\paper2\splits\class_ood\class_ood_test_id.csv `
  --test-ood-csv D:\openew_sa_data\paper2\splits\class_ood\class_ood_test_ood.csv `
  --output-dir D:\openew_sa_data\paper2\predictions\class_ood_nearest_centroid `
  --model nearest_centroid `
  --label-column label `
  --seed 42
```

This writes `predictions_val.csv` when `--val-csv` is provided, plus `predictions_test_id.csv`,
`predictions_test_ood.csv`, and `predictions_all.csv`. The `logistic_regression` and `mlp` options
are available when scikit-learn is installed; otherwise use the pure NumPy `nearest_centroid`
baseline.

## Temperature Scaling Calibration

Fit a scalar temperature on validation predictions and write calibrated prediction CSVs:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\temperature_scaling.py `
  --val-predictions D:\openew_sa_data\paper2\predictions\class_ood_nearest_centroid\predictions_val.csv `
  --test-id-predictions D:\openew_sa_data\paper2\predictions\class_ood_nearest_centroid\predictions_test_id.csv `
  --test-ood-predictions D:\openew_sa_data\paper2\predictions\class_ood_nearest_centroid\predictions_test_ood.csv `
  --output-dir D:\openew_sa_data\paper2\predictions\class_ood_nearest_centroid_temperature_scaled `
  --probability-prefix prob_ `
  --true-label-column true_label
```

The script calibrates log-probabilities when logits are unavailable. It preserves symbolic labels
such as DeepSense `0000` and writes `predictions_val_calibrated.csv`,
`predictions_test_id_calibrated.csv`, `predictions_test_ood_calibrated.csv`,
`predictions_all_calibrated.csv`, and `temperature_scaling_summary.json`.

Generate calibrated maximum-softmax OOD scores:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\baseline_ood_scores.py `
  --split-csv D:\openew_sa_data\paper2\splits\class_ood\class_ood_eval.csv `
  --predictions D:\openew_sa_data\paper2\predictions\class_ood_nearest_centroid_temperature_scaled\predictions_all_calibrated.csv `
  --method max_softmax_probability `
  --probability-prefix prob_ `
  --true-label-column label `
  --output D:\openew_sa_data\paper2\scores\class_ood_temperature_scaled_msp_scores.csv
```

Generate calibrated entropy OOD scores:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\baseline_ood_scores.py `
  --split-csv D:\openew_sa_data\paper2\splits\class_ood\class_ood_eval.csv `
  --predictions D:\openew_sa_data\paper2\predictions\class_ood_nearest_centroid_temperature_scaled\predictions_all_calibrated.csv `
  --method entropy `
  --probability-prefix prob_ `
  --true-label-column label `
  --output D:\openew_sa_data\paper2\scores\class_ood_temperature_scaled_entropy_scores.csv
```

Recompute calibration metrics on calibrated ID predictions:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\calibration_metrics.py `
  --predictions D:\openew_sa_data\paper2\predictions\class_ood_nearest_centroid_temperature_scaled\predictions_test_id_calibrated.csv `
  --true-label-column true_label `
  --output D:\openew_sa_data\paper2\calibration\class_ood_nearest_centroid_temperature_scaled_calibration.json
```

Recompute risk-coverage summaries on calibrated ID predictions:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\risk_coverage_curves.py `
  --predictions D:\openew_sa_data\paper2\predictions\class_ood_nearest_centroid_temperature_scaled\predictions_test_id_calibrated.csv `
  --true-label-column true_label `
  --output D:\openew_sa_data\paper2\risk_coverage\class_ood_nearest_centroid_temperature_scaled_risk_coverage.csv `
  --summary-output D:\openew_sa_data\paper2\risk_coverage\class_ood_nearest_centroid_temperature_scaled_risk_coverage.json
```

## Baseline Score Generation

Generate smoke-test OOD scores directly from a split manifest:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\baseline_ood_scores.py `
  --split-csv D:\openew_sa_data\paper2\splits\class_ood\class_ood_eval.csv `
  --method random_baseline `
  --output D:\openew_sa_data\paper2\scores\class_ood_random_scores.csv `
  --seed 42
```

Generate maximum-softmax OOD scores when prediction probabilities are available:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\baseline_ood_scores.py `
  --split-csv D:\openew_sa_data\paper2\splits\class_ood\class_ood_eval.csv `
  --predictions D:\openew_sa_data\paper2\predictions\class_ood_nearest_centroid\predictions_all.csv `
  --method max_softmax_probability `
  --probability-prefix prob_ `
  --true-label-column label `
  --output D:\openew_sa_data\paper2\scores\class_ood_msp_scores.csv
```

Generate entropy OOD scores from the same probability columns:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\baseline_ood_scores.py `
  --split-csv D:\openew_sa_data\paper2\splits\class_ood\class_ood_eval.csv `
  --predictions D:\openew_sa_data\paper2\predictions\class_ood_nearest_centroid\predictions_all.csv `
  --method entropy `
  --probability-prefix prob_ `
  --true-label-column label `
  --output D:\openew_sa_data\paper2\scores\class_ood_entropy_scores.csv
```

The same script also supports `energy_score` for logit columns with `--logit-prefix`.

## Feature-Distance OOD Scores (v2)

Stage 1 adds train-only nearest-centroid Euclidean, nearest-centroid cosine, and shared-covariance
Mahalanobis scores. Every score is a distance, so larger values are always more OOD-like. The
evaluation manifest may combine ID and OOD rows and must contain `ood_label` for metric generation.

```bash
python papers/paper2_ood_rf_signal_recognition/scripts/feature_distance_ood_scores.py \
  --train-csv /mnt/d/openew_sa_data/paper2/splits/deepsense_domain_ood/deepsense_day2_ood_train.csv \
  --eval-csv /mnt/d/openew_sa_data/paper2/splits/deepsense_domain_ood/deepsense_day2_ood_eval.csv \
  --output /mnt/d/openew_sa_data/paper2/scores/deepsense_day2_ood_mahalanobis_scores.csv \
  --metadata-output /mnt/d/openew_sa_data/paper2/scores/metadata/deepsense_day2_ood_mahalanobis_metadata.json \
  --method mahalanobis --regularization 1e-4 --batch-size 4096 --seed 42
```

`--max-train-samples-per-class` provides deterministic, seed-controlled fitting subsampling. The
metadata JSON records original and fitted class counts, dimensions, row counts, regularization,
batching, and subsampling settings. Run all three methods for the three established protocols with:

```bash
bash papers/paper2_ood_rf_signal_recognition/scripts/run_v2_distance_experiments.sh
```

The runner writes scores, score metadata, and metrics to the established Paper 2 output directories,
and logs to the v2 snapshot. Its `REPO_ROOT`, `DATA_ROOT`, `PYTHON`, `REGULARIZATION`, `BATCH_SIZE`,
`SEED`, and `LOG_ROOT` environment variables can be overridden. It does not use or modify the frozen
v0/v1 snapshots.

## Uncertainty-Distance Fusion (v3)

Stage 1 combines temperature-scaled entropy with train-fitted feature distances. Each component is
oriented so that higher values are more OOD-like. Normalization is fitted exclusively on ID
validation scores and then frozen for evaluation:

```text
normalized = (score - validation_median) / (validation_IQR + 1e-12)
```

If validation IQR is zero or non-finite, the fusion script falls back to validation standard
deviation; if that is also unusable, it uses scale 1 and records a warning in metadata. Evaluation
OOD labels are used only for output consistency and downstream metrics, never for normalization,
orientation, weights, or thresholds.

Calibrated prediction files can be converted directly to entropy score components. Validation input
may be ID-only and does not need `ood_label`:

```bash
python papers/paper2_ood_rf_signal_recognition/scripts/entropy_scores_from_predictions.py \
  --predictions /path/to/predictions_val_calibrated.csv \
  --output /path/to/validation_ts_entropy_scores.csv
```

`feature_distance_ood_scores.py` likewise accepts an ID-only validation manifest. Its canonical v2
evaluation schema remains unchanged when `ood_label` is present.

Fuse matching validation and evaluation components with strict sample-ID alignment:

```bash
python papers/paper2_ood_rf_signal_recognition/scripts/fuse_ood_scores.py \
  --validation-component ts_entropy=/path/to/validation_entropy.csv \
  --validation-component nearest_centroid_cosine=/path/to/validation_cosine.csv \
  --evaluation-component ts_entropy=/path/to/evaluation_entropy.csv \
  --evaluation-component nearest_centroid_cosine=/path/to/evaluation_cosine.csv \
  --output /path/to/fused_scores.csv \
  --metadata-output /path/to/fused_metadata.json \
  --normalization robust_zscore --seed 42
```

Omitting `--weights` gives every component equal weight. Explicit repeated
`--weights component=value` arguments must cover every component and are normalized to sum to one.
The runner covers ElectroSense class-OOD, DeepSense day-2 OOD, and JamShield scenario-OOD with
variants A-D (equal-weight primary fusions) and variant E (the Mahalanobis exploratory ablation):

```bash
bash papers/paper2_ood_rf_signal_recognition/scripts/run_v3_fusion_experiments.sh
```

The runner writes working artifacts beneath `paper2/v3_fusion` by default, reads calibrated
predictions from `paper2/runs`, and copies valid canonical v2 evaluation distance scores without
modifying v0, v1, or v2 snapshots. After validation, `finalize_v3_fusion.py` creates tables,
analysis, integrity reports, and documentation for the frozen v3 snapshot. Stage 1 does not run
the real-data experiment script.

## Metric Generation

Compute OOD detection metrics from a baseline score CSV:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\ood_detection_metrics.py `
  --scores D:\openew_sa_data\paper2\scores\class_ood_msp_scores.csv `
  --output D:\openew_sa_data\paper2\metrics\class_ood_msp_ood_metrics.json
```

Compute calibration metrics from prediction probabilities:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\calibration_metrics.py `
  --predictions D:\openew_sa_data\paper2\predictions\class_ood_nearest_centroid\predictions_test_id.csv `
  --true-label-column true_label `
  --output D:\openew_sa_data\paper2\metrics\class_ood_calibration.json
```

Generate risk-coverage curves from predictions with confidence:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\risk_coverage_curves.py `
  --predictions D:\openew_sa_data\paper2\predictions\class_ood_nearest_centroid\predictions_test_id.csv `
  --true-label-column true_label `
  --output D:\openew_sa_data\paper2\curves\class_ood_risk_coverage.csv `
  --summary-output D:\openew_sa_data\paper2\curves\class_ood_risk_coverage.json
```

## Result Table Generation

Summarize v0 OOD metric JSON files into CSV and Markdown tables:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\report_v0_results.py `
  --metrics-dir D:\openew_sa_data\paper2\metrics `
  --output-csv D:\openew_sa_data\paper2\tables\paper2_v0_ood_results.csv `
  --output-md D:\openew_sa_data\paper2\tables\paper2_v0_ood_results.md
```

## Quick Checks

Each script is a standalone argparse CLI and supports `--help`:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\generate_ood_splits.py --help
python papers\paper2_ood_rf_signal_recognition\scripts\build_paper2_manifest.py --help
python papers\paper2_ood_rf_signal_recognition\scripts\train_baseline_classifier.py --help
python papers\paper2_ood_rf_signal_recognition\scripts\temperature_scaling.py --help
python papers\paper2_ood_rf_signal_recognition\scripts\baseline_ood_scores.py --help
python papers\paper2_ood_rf_signal_recognition\scripts\feature_distance_ood_scores.py --help
python papers\paper2_ood_rf_signal_recognition\scripts\entropy_scores_from_predictions.py --help
python papers\paper2_ood_rf_signal_recognition\scripts\fuse_ood_scores.py --help
python papers\paper2_ood_rf_signal_recognition\scripts\calibration_metrics.py --help
python papers\paper2_ood_rf_signal_recognition\scripts\ood_detection_metrics.py --help
python papers\paper2_ood_rf_signal_recognition\scripts\risk_coverage_curves.py --help
python papers\paper2_ood_rf_signal_recognition\scripts\report_v0_results.py --help
```

## Example Split Generation

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\generate_ood_splits.py `
  --metadata D:\openew_sa_data\processed\radioml\metadata.csv `
  --output-dir D:\openew_sa_data\paper2\splits\class_ood `
  --protocol class_ood `
  --label-column modulation_label `
  --known-classes BPSK,QPSK,8PSK `
  --ood-classes AM-DSB,WBFM
```

## Prediction CSV Expectations

Calibration and risk-coverage scripts expect one row per evaluated sample with at least:

```text
sample_id,true_label,predicted_label,confidence
```

For NLL and Brier score, `calibration_metrics.py` auto-detects class probability columns
with `prob_`, `probability_`, or `p_` prefixes:

```text
prob_BPSK,prob_QPSK,prob_8PSK
prob_0000,prob_0001,prob_0100
```

The suffix after the prefix is treated as the class label. Symbolic labels such as DeepSense
`0000` and `0100` should be kept as strings; if a digit label is missing leading zeros in memory,
the calibration script maps it back to a unique fixed-width probability suffix when possible.

OOD detection can consume either one labeled score CSV or separate ID/OOD score CSV files. Scores
are interpreted as higher-is-OOD by default, with `--lower-is-ood` available for energy-like or
confidence-like scores where lower means more likely OOD.

## Integration Notes

- Keep Paper 2 assets inside this directory unless shared utilities are intentionally promoted.
- Do not modify Paper 1 files for Paper 2 experiments.
- Prefer configs for artifact paths and protocol choices.
- Replace placeholder model names in the YAML files once the Paper 2 multi-view training pipeline is
  implemented.
