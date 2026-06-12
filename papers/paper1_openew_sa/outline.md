# Paper 1 Outline: OpenEW-SA Benchmark

## 1. Title Candidates

1. OpenEW-SA: A Unified Benchmark for Electromagnetic Spectrum Situation Awareness
2. Domain-Aware RF Situation Awareness with OpenEW-SA: From Jamming Detection to WiFi Occupancy
3. OpenEW-SA: Dataset Harmonization and Baseline Evaluation for Spectrum Situation Awareness
4. Toward Neuro-Symbolic Spectrum Situation Awareness: A Unified RF Benchmark with Domain Holdouts
5. OpenEW-SA: Public RF Dataset Conversion, Metadata Alignment, and Baselines for Spectrum Monitoring

## 2. Abstract Draft

Electromagnetic spectrum situation awareness requires models that can reason across heterogeneous RF sensing modalities, operational contexts, and distribution shifts. Existing public RF datasets are valuable but fragmented: they differ in raw formats, labels, metadata conventions, and evaluation protocols. This paper introduces OpenEW-SA, a research benchmark scaffold for neuro-symbolic dynamic hypergraph-based spectrum situation awareness. OpenEW-SA defines a unified metadata schema and conversion pipeline for public RF datasets, then evaluates initial baselines on two complementary tasks: JamShield jamming/interference detection from tabular WiFi metrics and DeepSense SDR WiFi 4-channel occupancy classification from complex I/Q captures. Current results show strong JamShield random-split performance with a tabular MLP (accuracy 0.954, macro-F1 0.949, AUROC 0.996), but lower performance under scenario and jammer-type holdouts, indicating meaningful domain shift. On DeepSense, an IQ CNN trained on unflattened I/Q windows outperforms a tabular MLP under random splits (macro-F1 0.768 versus 0.614), while day2 holdout performance remains low (macro-F1 0.115), highlighting cross-day generalization challenges. The benchmark produces paper-ready dataset and baseline tables and establishes a path for extending OpenEW-SA to PSD-based ElectroSense spectrum monitoring.

## 3. Contribution List

- A unified OpenEW-SA metadata schema for RF samples spanning dataset source, input type, time, band, transmitter/receiver identity, labels, domain, mission context, situation label, threat level, and human-review status.
- Real-data converters for JamShield tabular WiFi jamming metrics and DeepSense SDR WiFi complex64 I/Q `.bin` captures.
- Domain-aware evaluation protocols for JamShield scenario and jammer-type holdouts with benign controls, plus DeepSense day2 holdout evaluation.
- Baseline models and training workflows for tabular MLPs and I/Q CNNs with train-only feature standardization and detailed classification metrics.
- Paper-table generators that summarize dataset properties, split protocols, baseline metrics, and benchmark-level comparisons across JamShield and DeepSense.
- A planned extension path for ElectroSense PSD spectrum monitoring to broaden OpenEW-SA from packet-level and I/Q tasks toward wide-area spectrum occupancy analysis.

## 4. Section-by-Section Outline

### 1. Introduction

- Motivation: spectrum situation awareness needs more than isolated RF classifiers; it needs consistent metadata, domain-aware evaluation, and extensible benchmark infrastructure.
- Problem: public RF datasets use incompatible file formats, task labels, and metadata assumptions.
- Claim: OpenEW-SA provides a practical bridge from heterogeneous RF data to future neuro-symbolic dynamic hypergraph reasoning.
- Preview of current benchmark: JamShield and DeepSense with random and domain-aware evaluation.

### 2. Related Work

- RF spectrum sensing and modulation/occupancy benchmarks.
- Jamming and interference detection datasets.
- RF fingerprinting and domain generalization in wireless sensing.
- Neuro-symbolic and graph/hypergraph approaches to situation awareness.
- Benchmark infrastructure and metadata harmonization for ML research.

### 3. OpenEW-SA Benchmark Design

- Unified metadata schema and rationale for each field.
- Artifact format: `metadata.csv`, `features.npy` or `features.pt`, `labels.json`.
- Dataset conversion philosophy: no automatic large downloads, reproducible local conversion, Windows-friendly configs.
- Baseline training/evaluation design: shared loaders, YAML configuration, train-only standardization, metrics and predictions.

### 4. Dataset Converters

- JamShield converter:
  - Recursively reads raw CSV files.
  - Uses numerical columns excluding `sample`, `station`, and `attack`.
  - Maps `attack=0` to normal and `attack=1` to abnormal interference.
  - Uses source CSV stems as `domain_id`.
- DeepSense SDR WiFi converter:
  - Recursively reads `.bin` files as `np.complex64`.
  - Parses four-bit occupancy labels from filename stems.
  - Parses `day1` and `day2` domains.
  - Segments each stream into `[2, 1024]` I/Q tensors.

### 5. Evaluation Protocols

- Random row split as a basic within-distribution baseline.
- JamShield scenario holdout:
  - Holds out selected jammer source domains plus benign control domain `data_benign_4`.
- JamShield jammer-type holdout:
  - Holds out reactive jammer domains plus benign control domain `data_benign_4`.
- DeepSense day-aware holdout:
  - Trains on `day1`, validates/evaluates on `day2`.
- Metrics:
  - Accuracy, macro-F1, weighted-F1, per-class precision/recall/F1, support, prediction counts.
  - AUROC and AUPRC for binary JamShield runs.

### 6. Baseline Models

- Tabular MLP for JamShield numerical metrics.
- Tabular MLP for flattened DeepSense I/Q windows.
- 1D IQ CNN for unflattened DeepSense `[2, 1024]` windows.
- Implementation details:
  - PyTorch training.
  - YAML-configured paths and model parameters.
  - Feature standardization fit only on training samples.

### 7. Results

- Dataset summary table and baseline result table.
- JamShield findings:
  - Random split performance is high.
  - Domain-aware holdouts reduce macro-F1 but retain strong AUROC/AUPRC.
  - Benign controls make binary metrics meaningful in holdout evaluation.
- DeepSense findings:
  - IQ CNN substantially improves random-split performance over the MLP.
  - Day2 holdout performance is low, indicating cross-day shift and a need for domain adaptation or richer context.

### 8. Discussion

- What the current results imply about domain shift in RF situation awareness.
- Why unified metadata matters for future graph/hypergraph construction.
- Limitations:
  - Current paper covers two converted datasets.
  - Baselines are intentionally lightweight.
  - No full neuro-symbolic hypergraph model is evaluated yet.
- Reproducibility and local-data constraints.

### 9. Planned ElectroSense Extension

- Add PSD spectrum data conversion and metadata mapping.
- Expand tasks from jamming and WiFi occupancy to wide-area spectrum occupancy or anomaly detection.
- Introduce split protocols by sensor, geography, frequency band, and time period.
- Use ElectroSense PSD traces as candidate nodes/events for future dynamic hypergraph construction.

### 10. Conclusion

- Summarize OpenEW-SA as a benchmark scaffold and evidence-generation pipeline.
- Emphasize the current two-dataset baseline as a foundation, not an endpoint.
- State next steps: ElectroSense extension, WiSig/RadioML expansion, and neuro-symbolic hypergraph models.

## 5. Table List

1. Dataset Summary Table
   - Source: `D:\openew_sa_data\tables\openew_sa_dataset_table.csv`
   - Columns: dataset, task, sample count, input type, feature shape/dimension, number of classes, number of domains, split protocols.
2. Baseline Performance Table
   - Source: `D:\openew_sa_data\tables\openew_sa_baseline_table.csv`
   - Columns: dataset, task, model, split protocol, accuracy, macro-F1, AUROC, AUPRC.
3. Unified Metadata Schema Table
   - Lists all OpenEW-SA metadata fields and their role in downstream situation awareness.
4. Dataset Converter Mapping Table
   - Maps raw dataset fields and filenames to OpenEW-SA metadata fields.
5. Domain Holdout Protocol Table
   - Details JamShield and DeepSense holdout definitions.
6. ElectroSense Planned Extension Table
   - Proposed PSD fields, labels, domains, and split protocols.

## 6. Figure List

1. OpenEW-SA Pipeline Overview
   - Raw public RF datasets to converters to unified artifacts to baselines to paper tables.
2. Unified Metadata-to-Hypergraph Concept Figure
   - Samples, domains, frequency bands, receivers, situations, and threat levels as candidate graph/hypergraph entities.
3. JamShield Domain Holdout Diagram
   - Training domains versus held-out jammer and benign-control domains.
4. DeepSense Day-Aware Split Diagram
   - Day1 training and day2 validation/evaluation.
5. Baseline Model Sketch
   - Tabular MLP and IQ CNN paths.
6. Result Summary Bar Chart
   - Macro-F1 comparison across JamShield and DeepSense split protocols.
7. ElectroSense Extension Concept Figure
   - PSD traces over sensors, frequencies, and time windows.

## 7. Current Result Summary

### Dataset Table

| Dataset | Task | Samples | Input Type | Feature Shape | Feature Dimension | Classes | Domains | Split Protocols |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| JamShield | Jamming/interference detection | 92,486 | tabular_metrics | [37] | 37 | 2 | 20 | Random row split; scenario holdout with benign control; reactive jammer-type holdout with benign control |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | 32,000 | iq_features | [2, 1024] | 2,048 | 16 | 2 | Random row split; day2 holdout; random IQ CNN split |

### Baseline Table

| Dataset | Task | Model | Split Protocol | Accuracy | Macro-F1 | AUROC | AUPRC |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| JamShield | Jamming/interference detection | Tabular MLP | Random row split across JamShield domains | 0.953820 | 0.948885 | 0.996014 | 0.998183 |
| JamShield | Jamming/interference detection | Tabular MLP | Hold out selected jammer source domains plus `data_benign_4` | 0.845587 | 0.828574 | 0.970368 | 0.984382 |
| JamShield | Jamming/interference detection | Tabular MLP | Hold out reactive jammer domains plus `data_benign_4` | 0.845828 | 0.792954 | 0.928423 | 0.977445 |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | Tabular MLP | Random row split across day1/day2 windows | 0.577562 | 0.614465 | N/A | N/A |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | Tabular MLP | Train on day1, evaluate on day2 | 0.151812 | 0.114871 | N/A | N/A |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | IQ CNN 1D | Random row split using unflattened `[2, 1024]` I/Q windows | 0.740781 | 0.768321 | N/A | N/A |

### Main Observations

- JamShield random split is strong, but domain-aware evaluation is more realistic and lowers macro-F1 from 0.948885 to 0.828574 for scenario holdout and 0.792954 for reactive jammer-type holdout.
- JamShield AUROC and AUPRC remain high under holdout evaluation, suggesting useful separability even when class-threshold behavior changes.
- DeepSense IQ CNN performance is substantially stronger than the tabular MLP under random splits, improving macro-F1 from 0.614465 to 0.768321.
- DeepSense day2 holdout is difficult for the current MLP baseline, with macro-F1 0.114871 despite balanced 1,000-sample support for each occupancy class.
- The contrast between random splits and domain-aware splits motivates future domain adaptation and neuro-symbolic context modeling.

## 8. Planned ElectroSense Extension Section

### Motivation

ElectroSense adds a PSD-centric perspective to OpenEW-SA. JamShield covers jamming/interference from tabular WiFi metrics, and DeepSense covers 802.11 occupancy from raw I/Q windows. ElectroSense can extend the benchmark toward long-duration, sensor-distributed, frequency-domain spectrum monitoring.

### Proposed Converter

- Recursively ingest ElectroSense PSD files from a configured raw directory.
- Convert PSD traces into fixed-length frequency or time-frequency windows.
- Save `features.npy` as float32 PSD feature tensors.
- Populate OpenEW-SA metadata:
  - `dataset_source = electrosense`
  - `input_type = psd_features`
  - `frequency_band` from available band metadata or file grouping
  - `rx_id` from sensor identity when available
  - `domain_id` from sensor, location, time period, or frequency-band grouping
  - `occupancy_label` or `abnormal_event_label` depending on label availability
  - `synthetic_mission_context = spectrum_monitoring`

### Proposed Tasks

- Binary or multi-class spectrum occupancy classification.
- Abnormal PSD event detection.
- Domain generalization across sensors, geography, time periods, or frequency bands.

### Proposed Split Protocols

- Random PSD window split for a basic baseline.
- Sensor holdout for receiver-domain generalization.
- Time-period holdout for temporal robustness.
- Frequency-band holdout for cross-band transfer.

### Planned Baselines

- PSD MLP for flattened PSD windows.
- PSD CNN for 1D frequency traces.
- Spectrogram CNN if time-frequency PSD windows are constructed.
- Multi-task transformer if occupancy, anomaly, and situation labels can be aligned.

### Expected Paper Role

ElectroSense should serve as the third evidence point in the paper: it would demonstrate that the OpenEW-SA schema and reporting tools cover tabular metrics, raw I/Q windows, and PSD spectrum traces. It also gives the strongest natural bridge to dynamic hypergraph modeling because sensors, frequency bins, time windows, occupancy states, and events can be represented as typed nodes and hyperedges.
