# OpenEW-SA

OpenEW-SA is a Python research codebase for an NRF project on **neuro-symbolic dynamic hypergraph-based electromagnetic spectrum situation awareness**. The repository focuses on reproducible data conversion, baseline neural models, and paper table generation while avoiding automatic downloads of large public RF datasets.

## Supported public RF datasets

| Dataset | Intended tasks | Expected raw input | Converter |
| --- | --- | --- | --- |
| DeepSense Spectrum Sensing | spectrum occupancy, sensing domain shift | `.npy` / `.npz` I/Q or spectrogram tensors | `openew.data.deepsense` |
| WiSig RF Fingerprinting | transmitter identification, receiver/domain shift | `.npy` / `.npz` I/Q tensors | `openew.data.wisig` |
| ElectroSense PSD Spectrum Dataset | PSD occupancy/anomaly modeling | PSD `.csv`, `.npy`, or `.npz` exports | `openew.data.electrosense` |
| JamShield Dataset | jamming/interference detection | tabular `.csv` metrics | `openew.data.jamshield` |
| RadioML 2016.10A | optional modulation baseline/pretraining | `RML2016.10a_dict.pkl` | `openew.data.radioml` |

## Unified metadata schema

Every converted dataset writes a `metadata.csv` with the same columns:

```text
sample_id, dataset_source, input_type, time_index, frequency_band, tx_id, rx_id,
modulation_label, occupancy_label, abnormal_event_label, domain_id,
synthetic_mission_context, situation_label, threat_level, human_review_required
```

Converters also write `features.npy` or `features.pt` and `labels.json` in the configured output directory.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Core dependencies are PyTorch, pandas, numpy, scikit-learn, PyYAML, and tqdm. Configuration uses lightweight YAML files and argparse entry points.

## Data preparation

Large datasets are **not downloaded automatically**. First, read the license/terms for each dataset and place files under `data/raw/<dataset>/` or update the relevant YAML file in `configs/data/`.

Print manual download reminders:

```bash
python scripts/prepare_download_placeholders.py
```

Convert a dataset after manual download:

```bash
python scripts/convert_dataset.py deepsense --config configs/data/deepsense.yaml
python scripts/convert_dataset.py wisig --config configs/data/wisig.yaml
python scripts/convert_dataset.py electrosense --config configs/data/electrosense.yaml
python scripts/convert_dataset.py jamshield --config configs/data/jamshield.yaml
python scripts/convert_dataset.py radioml --config configs/data/radioml.yaml
```

Inspect raw JamShield CSV files before choosing feature columns:

```powershell
python scripts\inspect_jamshield_raw.py --raw-dir D:\openew_sa_data\raw\jamshield --output D:\openew_sa_data\tables\jamshield_raw_inspection.txt
```

The inspector writes the readable text report to `--output` and a sibling `.csv` summary with the same stem.

Each conversion produces:

```text
data/processed/<dataset>/metadata.csv
data/processed/<dataset>/features.npy  # or features.pt
data/processed/<dataset>/labels.json
```

## Synthetic smoke test on Windows

For a lightweight end-to-end check from PowerShell, create tiny synthetic artifacts under the Windows path configured in `configs\data\tiny.yaml`:

```powershell
python scripts\dev\make_tiny_openew_dataset.py --output-dir D:\openew_sa_data\processed\tiny
```

Generate paper helper tables from the tiny artifacts:

```powershell
python scripts\generate_dataset_summary.py D:\openew_sa_data\processed\tiny --output D:\openew_sa_data\tables\dataset_summary_tiny.csv
python scripts\generate_task_summary.py --output D:\openew_sa_data\tables\task_summary.csv
```

Train and evaluate a tiny CPU baseline:

```powershell
python scripts\train_baseline.py --config configs\train\tiny_tabular_mlp.yaml
python scripts\evaluate_baseline.py --config configs\train\tiny_tabular_mlp.yaml
```

Or run the full tiny smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\dev\run_tiny_smoke_test.ps1
```

The tiny dataset contains mixed `dataset_source` values (`deepsense`, `wisig`, `electrosense`, `jamshield`, and `radioml`), 64-dimensional features, three situation classes (`normal`, `congested`, `abnormal`), and three threat levels (`low`, `medium`, `high`).

## Baseline models

Implemented PyTorch baselines:

- `IQCNN1D` for raw I/Q sequences.
- `SpectrogramCNN` for time-frequency images.
- `PSDMLP` for flattened PSD vectors.
- `PSDCNN` for PSD traces.
- `TabularMLP` for JamShield metrics.
- `MultiTaskTransformer` with modulation, occupancy, abnormal event, situation, and threat heads.

Model definitions live in `src/openew/models/baselines.py`, and configurable construction is handled by `src/openew/models/factory.py`.

## Training and evaluation

Train with a YAML file:

```bash
python scripts/train_baseline.py --config configs/train/iq_cnn.yaml
```

Evaluate a checkpoint:

```bash
python scripts/evaluate_baseline.py --config configs/train/iq_cnn.yaml
```

JamShield supports three evaluation modes:

```powershell
python scripts\train_baseline.py --config configs\train\tabular_mlp_jamshield.yaml
python scripts\evaluate_baseline.py --config configs\train\tabular_mlp_jamshield.yaml
```

```powershell
python scripts\train_baseline.py --config configs\train\jamshield_domain_holdout.yaml
python scripts\evaluate_baseline.py --config configs\train\jamshield_domain_holdout.yaml
```

```powershell
python scripts\train_baseline.py --config configs\train\jamshield_reactive_holdout.yaml
python scripts\evaluate_baseline.py --config configs\train\jamshield_reactive_holdout.yaml
```

The random config writes to `runs/jamshield_random`, the domain holdout config writes to `runs/jamshield_domain_holdout`, and the reactive jammer-type holdout config writes to `runs/jamshield_reactive_holdout`.

Analyze saved JamShield predictions by `domain_id`:

```powershell
python scripts\analyze_predictions_by_domain.py runs\jamshield_random\predictions.csv --output D:\openew_sa_data\tables\jamshield_random_by_domain.csv
python scripts\analyze_predictions_by_domain.py runs\jamshield_domain_holdout\predictions.csv --output D:\openew_sa_data\tables\jamshield_domain_holdout_by_domain.csv
python scripts\analyze_predictions_by_domain.py runs\jamshield_reactive_holdout\predictions.csv --output D:\openew_sa_data\tables\jamshield_reactive_holdout_by_domain.csv
```

For new datasets, update:

- `artifact_dir` to point at converted artifacts.
- `label_column` to one of the unified metadata labels.
- `model.name` and `model.kwargs` to match the feature shape and class count.

## Paper table generation

Dataset summary:

```bash
python scripts/generate_dataset_summary.py data/processed/deepsense data/processed/wisig --output tables/dataset_summary.csv
```

Task summary:

```bash
python scripts/generate_task_summary.py --output tables/task_summary.csv
```

Baseline performance table from metric JSON/CSV files:

```bash
python scripts/generate_baseline_performance_table.py runs/*/metrics.json --output tables/baseline_performance.csv
```

## Repository layout

```text
configs/                 YAML data and training configs
scripts/                 conversion, training, evaluation, and paper table CLIs
src/openew/data/          unified metadata schema and dataset-specific converters
src/openew/models/        baseline PyTorch models
src/openew/training/      dataset loader, training loop, evaluation entry point
src/openew/utils/         YAML/path helpers
```

## Notes for research extensions

- Keep all file locations in YAML configs rather than hard-coding paths.
- Extend dataset converters with dataset-specific raw parsers, but preserve the unified metadata schema.
- Use `synthetic_mission_context`, `situation_label`, and `threat_level` to bridge data-driven baselines with future neuro-symbolic dynamic hypergraph experiments.
- Store large raw/processed data outside git; commit configs and code only.
