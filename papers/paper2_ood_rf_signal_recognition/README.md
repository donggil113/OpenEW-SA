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
    baseline_ood_scores.py
    calibration_metrics.py
    ood_detection_metrics.py
    risk_coverage_curves.py
    report_v0_results.py
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

Train a nearest-centroid ID classifier from split manifests and write test-ID/test-OOD predictions:

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

This writes `predictions_test_id.csv`, `predictions_test_ood.csv`, and `predictions_all.csv`.
The `logistic_regression` and `mlp` options are available when scikit-learn is installed; otherwise
use the pure NumPy `nearest_centroid` baseline.

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
python papers\paper2_ood_rf_signal_recognition\scripts\baseline_ood_scores.py --help
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
