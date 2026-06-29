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
    class_ood.yaml
    domain_ood.yaml
    hybrid_ood.yaml
  scripts/
    generate_ood_splits.py
    calibration_metrics.py
    ood_detection_metrics.py
    risk_coverage_curves.py
```

## OpenEW-SA Artifact Assumptions

The scaffold reuses the repository's converted dataset convention:

```text
data/processed/<dataset>/
  metadata.csv
  features.npy or features.pt
  labels.json
```

The OOD split script operates on `metadata.csv` and preserves all metadata columns in its output
split manifests. It expects OpenEW-SA schema fields such as `sample_id`, `dataset_source`,
`input_type`, `modulation_label`, `occupancy_label`, `abnormal_event_label`, `domain_id`,
`situation_label`, and `threat_level`.

## Quick Checks

Each script is a standalone argparse CLI and supports `--help`:

```powershell
python papers\paper2_ood_rf_signal_recognition\scripts\generate_ood_splits.py --help
python papers\paper2_ood_rf_signal_recognition\scripts\calibration_metrics.py --help
python papers\paper2_ood_rf_signal_recognition\scripts\ood_detection_metrics.py --help
python papers\paper2_ood_rf_signal_recognition\scripts\risk_coverage_curves.py --help
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

For NLL and Brier score, `calibration_metrics.py` can also consume class probability columns:

```text
prob_BPSK,prob_QPSK,prob_8PSK
```

OOD detection can consume either one labeled score CSV or separate ID/OOD score CSV files. Scores
are interpreted as higher-is-OOD by default, with `--lower-is-ood` available for energy-like or
confidence-like scores where lower means more likely OOD.

## Integration Notes

- Keep Paper 2 assets inside this directory unless shared utilities are intentionally promoted.
- Do not modify Paper 1 files for Paper 2 experiments.
- Prefer configs for artifact paths and protocol choices.
- Replace placeholder model names in the YAML files once the Paper 2 multi-view training pipeline is
  implemented.
