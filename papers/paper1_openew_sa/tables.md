# Paper 1 Tables

Markdown versions of the current OpenEW-SA benchmark tables for `papers/paper1_openew_sa/outline.md`.

Source artifacts:

- `D:\openew_sa_data\tables\openew_sa_dataset_table.csv`
- `D:\openew_sa_data\tables\openew_sa_baseline_table.csv`
- `D:\openew_sa_data\tables\electrosense_results_summary.csv`

## Dataset Summary Table

| Dataset | Task | Samples | Input Type | Feature Shape | Feature Dimension | Classes | Domains | Split Protocols |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| JamShield | Jamming/interference detection | 92,486 | tabular_metrics | [37] | 37 | 2 | 20 | Random row split; scenario holdout with benign control; reactive jammer-type holdout with benign control |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | 32,000 | iq_features | [2, 1024] | 2,048 | 16 | 2 | Random row split; day2 holdout; random IQ CNN split |
| ElectroSense PSD | Technology classification | 45,750 | psd_features | [512] | 512 | 6 | 40 | Random row split; sensor holdout |

## Baseline Performance Table

| Dataset | Task | Model | Split Protocol | Accuracy | Macro-F1 | AUROC | AUPRC |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| JamShield | Jamming/interference detection | Tabular MLP | Random row split across JamShield domains | 0.953820 | 0.948885 | 0.996014 | 0.998183 |
| JamShield | Jamming/interference detection | Tabular MLP | Hold out selected jammer source domains plus `data_benign_4` | 0.845587 | 0.828574 | 0.970368 | 0.984382 |
| JamShield | Jamming/interference detection | Tabular MLP | Hold out reactive jammer domains plus `data_benign_4` | 0.845828 | 0.792954 | 0.928423 | 0.977445 |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | Tabular MLP | Random row split across day1/day2 windows | 0.577562 | 0.614465 | N/A | N/A |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | Tabular MLP | Train on day1, evaluate on day2 | 0.151812 | 0.114871 | N/A | N/A |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | IQ CNN 1D | Random row split using unflattened `[2, 1024]` I/Q windows | 0.740781 | 0.768321 | N/A | N/A |
| ElectroSense PSD | Technology classification | Tabular MLP | Random row split across ElectroSense PSD rows | 0.998885 | 0.998862 | N/A | N/A |
| ElectroSense PSD | Technology classification | Tabular MLP | Hold out selected sensor domains | 0.554571 | 0.536666 | N/A | N/A |

## ElectroSense Per-Class F1 Snapshot

| Split Protocol | DAB | DVBT | FM | GSM | LTE | TETRA |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Random row split | 0.998985 | 0.997877 | 0.999695 | 0.998380 | 0.999750 | 0.998487 |
| Sensor holdout | 0.002639 | 0.575540 | 0.828479 | 0.487056 | 0.800641 | 0.525641 |
