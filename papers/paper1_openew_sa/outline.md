# Paper 1 Outline: OpenEW-SA Benchmark

## 1. Title Candidates

1. OpenEW-SA: A Unified Benchmark for Electromagnetic Spectrum Situation Awareness
2. Domain-Aware RF Situation Awareness with OpenEW-SA: From Jamming Detection to Spectrum Technology Classification
3. OpenEW-SA: Dataset Harmonization and Baseline Evaluation for Spectrum Situation Awareness
4. Toward Neuro-Symbolic Spectrum Situation Awareness: A Unified RF Benchmark with Domain Holdouts
5. OpenEW-SA: Public RF Dataset Conversion, Metadata Alignment, and Baselines for Spectrum Monitoring

## 2. Abstract Draft

Electromagnetic spectrum situation awareness requires models that can reason across heterogeneous RF sensing modalities, operational contexts, and distribution shifts. Existing public RF datasets are valuable but fragmented: they differ in raw formats, labels, metadata conventions, and evaluation protocols. This paper introduces OpenEW-SA, a research benchmark scaffold for neuro-symbolic dynamic hypergraph-based spectrum situation awareness. OpenEW-SA defines a unified metadata schema and conversion pipeline for public RF datasets, then evaluates initial baselines on three complementary completed subsets: JamShield tabular RF/network abnormal interference detection, DeepSense SDR WiFi I/Q occupancy classification, and ElectroSense PSD technology classification. Current results show strong random-split performance across the completed subsets, including JamShield tabular MLP performance of 0.953820 accuracy and 0.948885 macro-F1, DeepSense IQ CNN performance of 0.740781 accuracy and 0.768321 macro-F1, and nearly saturated ElectroSense PSD performance of 0.998885 accuracy and 0.998862 macro-F1. However, domain-aware evaluation exposes substantial generalization gaps: DeepSense day2 holdout falls to 0.114871 macro-F1, and ElectroSense sensor holdout falls to 0.554571 accuracy and 0.536666 macro-F1. These results show that OpenEW-SA can convert heterogeneous RF data into common artifacts, produce paper-ready benchmark tables, and reveal domain shift hidden by random splits.

## 3. Contribution List

- A unified OpenEW-SA metadata schema for RF samples spanning dataset source, input type, time, band, transmitter/receiver identity, labels, domain, mission context, situation label, threat level, and human-review status.
- A completed three-subset OpenEW-SA benchmark currently including:
  - JamShield tabular RF/network abnormal interference detection.
  - DeepSense SDR WiFi I/Q occupancy classification.
  - ElectroSense PSD technology classification.
- Real-data converters for JamShield CSV metrics, DeepSense SDR WiFi complex64 `.bin` captures, and ElectroSense PSD `.npy` arrays.
- Domain-aware evaluation protocols for JamShield scenario and jammer-type holdouts with benign controls, DeepSense day2 holdout evaluation, and ElectroSense sensor holdout evaluation.
- Baseline models and training workflows for tabular MLPs and I/Q CNNs with train-only feature standardization and detailed classification metrics.
- Paper-table generators that summarize dataset properties, split protocols, baseline metrics, and benchmark-level comparisons across JamShield, DeepSense, and ElectroSense.
- A forward path from the current benchmark toward WiSig RF fingerprinting, RadioML modulation baselines, and neuro-symbolic dynamic hypergraph modeling.

## 4. Section-by-Section Outline

### 1. Introduction

- Motivation: spectrum situation awareness needs more than isolated RF classifiers; it needs consistent metadata, domain-aware evaluation, and extensible benchmark infrastructure.
- Problem: public RF datasets use incompatible file formats, task labels, and metadata assumptions.
- Claim: OpenEW-SA provides a practical bridge from heterogeneous RF data to future neuro-symbolic dynamic hypergraph reasoning.
- Preview of current benchmark: JamShield, DeepSense, and ElectroSense with random and domain-aware evaluation.

### 2. Related Work

- RF spectrum sensing and modulation/occupancy benchmarks.
- Jamming and interference detection datasets.
- PSD-based spectrum monitoring and transmitter/technology identification.
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
- ElectroSense PSD converter:
  - Recursively reads PSD `.npy` files and skips too-small artifacts.
  - Infers sensor and date identifiers from parent folders.
  - Parses technology labels and frequency ranges from filenames.
  - Treats each PSD row as one sample and resamples each row to `[512]`.
  - Uses technology labels as `situation_label` classes and sensor IDs as `domain_id`.

### 5. Evaluation Protocols

- Random row split as a basic within-distribution baseline.
- JamShield scenario holdout:
  - Holds out selected jammer source domains plus benign control domain `data_benign_4`.
- JamShield jammer-type holdout:
  - Holds out reactive jammer domains plus benign control domain `data_benign_4`.
- DeepSense day-aware holdout:
  - Trains on `day1`, validates/evaluates on `day2`.
- ElectroSense sensor holdout:
  - Holds out selected receiver domains, including `alcorcon1`, `bcn-L`, and `Geneva`.
- Metrics:
  - Accuracy, macro-F1, weighted-F1, per-class precision/recall/F1, support, prediction counts.
  - AUROC and AUPRC for binary JamShield runs.

### 6. Baseline Models

- Tabular MLP for JamShield numerical metrics.
- Tabular MLP for flattened DeepSense I/Q windows.
- 1D IQ CNN for unflattened DeepSense `[2, 1024]` windows.
- Tabular MLP for ElectroSense `[512]` PSD vectors.
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
- ElectroSense findings:
  - Random split performance is almost saturated, reaching 0.998885 accuracy and 0.998862 macro-F1.
  - Sensor holdout reveals strong sensor-domain shift, dropping to 0.554571 accuracy and 0.536666 macro-F1.
  - DAB collapses under sensor holdout, while LTE and FM remain relatively strong compared with the other held-out classes.

### 8. Discussion

- Across JamShield, DeepSense, and ElectroSense, domain-aware splits consistently expose generalization gaps hidden by random splits.
- Unified metadata enables comparable analysis across tabular metrics, raw I/Q windows, and PSD feature vectors.
- The ElectroSense sensor holdout suggests that receiver/site effects can dominate PSD technology classification unless models explicitly handle domain shift.
- Why unified metadata matters for future graph/hypergraph construction.
- Limitations:
  - Current paper covers three converted datasets, while WiSig and RadioML are not yet integrated into the benchmark tables.
  - Baselines are intentionally lightweight.
  - No full neuro-symbolic hypergraph model is evaluated yet.
- Reproducibility and local-data constraints.

### 9. Completed ElectroSense Extension

- ElectroSense is now included as the third completed OpenEW-SA subset.
- The converter ingests PSD `.npy` arrays, maps each PSD row into a fixed `[512]` feature vector, and records sensor domains in unified metadata.
- The benchmark supports a random PSD classification split and a sensor-domain holdout split.
- The random split is nearly saturated, but sensor holdout exposes major domain shift and class-specific failure modes.
- Remaining future work:
  - Add WiSig RF fingerprinting as a device/domain generalization task.
  - Add RadioML as an optional modulation baseline or pretraining source.
  - Build neuro-symbolic dynamic hypergraph models over samples, sensors, frequency bands, time windows, situations, and threat labels.

### 10. Conclusion

- Summarize OpenEW-SA as a benchmark scaffold and evidence-generation pipeline.
- Emphasize the current three-dataset baseline as a foundation, not an endpoint.
- State next steps: WiSig/RadioML expansion and neuro-symbolic hypergraph models.

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
   - Details JamShield, DeepSense, and ElectroSense holdout definitions.
6. ElectroSense PSD Conversion and Sensor Holdout Table
   - Summarizes PSD row conversion, sensor-domain splits, per-class F1, and domain shift behavior.

## 6. Figure List

1. OpenEW-SA Pipeline Overview
   - Raw public RF datasets to converters to unified artifacts to baselines to paper tables.
2. Unified Metadata-to-Hypergraph Concept Figure
   - Samples, domains, frequency bands, receivers, situations, and threat levels as candidate graph/hypergraph entities.
3. JamShield Domain Holdout Diagram
   - Training domains versus held-out jammer and benign-control domains.
4. DeepSense Day-Aware Split Diagram
   - Day1 training and day2 validation/evaluation.
5. ElectroSense Sensor Holdout Diagram
   - Training sensors versus held-out receiver domains.
6. Baseline Model Sketch
   - Tabular MLP, PSD MLP, and IQ CNN paths.
7. Result Summary Bar Chart
   - Macro-F1 comparison across JamShield, DeepSense, and ElectroSense split protocols.

## 7. Current Result Summary

### Dataset Table

| Dataset | Task | Samples | Input Type | Feature Shape | Feature Dimension | Classes | Domains | Split Protocols |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| JamShield | Jamming/interference detection | 92,486 | tabular_metrics | [37] | 37 | 2 | 20 | Random row split; scenario holdout with benign control; reactive jammer-type holdout with benign control |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | 32,000 | iq_features | [2, 1024] | 2,048 | 16 | 2 | Random row split; day2 holdout; random IQ CNN split |
| ElectroSense PSD | Technology classification | 45,750 | psd_features | [512] | 512 | 6 | 40 | Random row split; sensor holdout |

### Baseline Table

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

### ElectroSense Per-Class F1 Snapshot

| Split Protocol | DAB | DVBT | FM | GSM | LTE | TETRA |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Random row split | 0.998985 | 0.997877 | 0.999695 | 0.998380 | 0.999750 | 0.998487 |
| Sensor holdout | 0.002639 | 0.575540 | 0.828479 | 0.487056 | 0.800641 | 0.525641 |

### Main Observations

- JamShield random split is strong, but domain-aware evaluation is more realistic and lowers macro-F1 from 0.948885 to 0.828574 for scenario holdout and 0.792954 for reactive jammer-type holdout.
- JamShield AUROC and AUPRC remain high under holdout evaluation, suggesting useful separability even when class-threshold behavior changes.
- DeepSense IQ CNN performance is substantially stronger than the tabular MLP under random splits, improving macro-F1 from 0.614465 to 0.768321.
- DeepSense day2 holdout is difficult for the current MLP baseline, with macro-F1 0.114871 despite balanced 1,000-sample support for each occupancy class.
- ElectroSense random split is almost saturated, with all six technology classes near perfect per-class F1.
- ElectroSense sensor holdout reveals strong receiver-domain shift: DAB collapses to 0.002639 F1, while FM and LTE remain comparatively strong at 0.828479 and 0.800641 F1.
- Across all three completed subsets, the contrast between random splits and domain-aware splits motivates future domain adaptation and neuro-symbolic context modeling.

## 8. Completed ElectroSense Extension Section

### Motivation

ElectroSense adds a PSD-centric perspective to OpenEW-SA. JamShield covers abnormal interference from tabular RF/network metrics, DeepSense covers 802.11 occupancy from raw I/Q windows, and ElectroSense extends the benchmark toward sensor-distributed, frequency-domain spectrum monitoring.

### Completed Converter

- Recursively ingests ElectroSense PSD `.npy` files from the configured raw directory.
- Skips too-small files and records skipped inputs in conversion metadata.
- Converts PSD rows into fixed-length `[512]` float32 feature vectors.
- Populates OpenEW-SA metadata:
  - `dataset_source = electrosense`
  - `input_type = psd_features`
  - `frequency_band` from parsed filename ranges
  - `rx_id` from sensor identity
  - `domain_id` from sensor identity
  - `situation_label` from technology labels: `dab`, `dvbt`, `fm`, `gsm`, `lte`, `tetra`
  - `synthetic_mission_context = spectrum_monitoring`

### Completed Tasks

- Six-class PSD technology classification.
- Random row split for within-distribution PSD recognition.
- Sensor holdout for receiver-domain generalization.

### Completed Baselines

- Tabular MLP over standardized `[512]` PSD vectors.
- Detailed metrics and per-domain prediction analysis through the shared OpenEW-SA reporting pipeline.

### Result Role

ElectroSense now serves as the third evidence point in the paper. It demonstrates that the OpenEW-SA schema and reporting tools cover tabular metrics, raw I/Q windows, and PSD spectrum traces. It also gives the strongest natural bridge to dynamic hypergraph modeling because sensors, frequency bands, time windows, technology states, and situations can be represented as typed nodes and hyperedges.

### Remaining Future Work

- Integrate WiSig for RF fingerprinting and device/domain generalization.
- Integrate RadioML 2016.10A as an optional modulation baseline and pretraining source.
- Develop neuro-symbolic dynamic hypergraph models that use OpenEW-SA metadata as structured context rather than only as reporting fields.
