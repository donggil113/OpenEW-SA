# OpenEW-SA: A Unified Benchmark for Electromagnetic Spectrum Situation Awareness

## Abstract

Electromagnetic spectrum situation awareness requires models that can reason across heterogeneous sensing modalities, operational contexts, and distribution shifts. Public RF datasets provide valuable evidence for this problem, but they often differ in raw formats, label conventions, metadata availability, and evaluation practice. This paper introduces OpenEW-SA, a unified benchmark scaffold for neuro-symbolic dynamic hypergraph-based spectrum situation awareness. OpenEW-SA converts public RF datasets into a common artifact format consisting of `metadata.csv`, `features.npy` or `features.pt`, and `labels.json`, with a shared metadata schema spanning dataset source, input type, time, frequency band, receiver identity, domain, situation label, threat level, and human-review status.

We instantiate the benchmark with three completed subsets: JamShield tabular RF/network abnormal interference detection, DeepSense SDR WiFi I/Q occupancy classification, and ElectroSense PSD technology classification. Baseline results show that random row-level splits often report strong performance, including JamShield random-split macro-F1 of 0.948885, DeepSense IQ CNN random-split macro-F1 of 0.768321, and ElectroSense random-split macro-F1 of 0.998862. However, domain-aware splits reveal much larger generalization gaps: JamShield scenario and reactive holdouts reduce macro-F1 to 0.828574 and 0.792954, DeepSense day2 holdout reduces macro-F1 to 0.114871, and ElectroSense sensor holdout reduces macro-F1 to 0.536666. The central finding is that random row-level splits overestimate RF situation-awareness performance, while domain-aware splits expose generalization failures across scenarios, days, and sensors. These results motivate domain-aware evaluation as a default practice for RF situation awareness and provide a foundation for future WiSig, RadioML, and neuro-symbolic hypergraph extensions.

## 1. Introduction

Modern spectrum operations require situational awareness over signals, emitters, sensors, bands, and time. In practice, an RF model may be asked to identify abnormal interference, infer occupancy, classify spectrum technology, or support human review under changing environments. These tasks are not isolated: they are connected by shared receivers, frequency bands, operational contexts, and domain shifts. A benchmark for this setting therefore needs more than a collection of classifiers. It needs common metadata, repeatable conversion pipelines, and evaluation protocols that make cross-domain generalization visible.

Existing public RF datasets are useful but fragmented. JamShield provides tabular WiFi metrics for benign and jamming/interference conditions. DeepSense SDR WiFi captures expose raw I/Q occupancy states across collection days. ElectroSense PSD traces provide spectrum technology labels across many sensors. Each dataset carries different raw formats, label semantics, and natural domain identifiers. Without a shared conversion layer, it is difficult to compare tasks, build paper tables, or use dataset metadata as structured context for later neuro-symbolic modeling.

OpenEW-SA addresses this gap by harmonizing heterogeneous public RF datasets into a unified research scaffold. Each converted dataset writes common artifacts and schema-aligned metadata. The same training and evaluation code can then train lightweight baselines, save detailed predictions, and generate paper-ready benchmark tables. The current benchmark includes three completed subsets: JamShield for abnormal interference detection, DeepSense for WiFi I/Q occupancy classification, and ElectroSense for PSD technology classification.

The main empirical result is consistent across these subsets: random row-level splits substantially overestimate RF situation-awareness performance. Random splits mix domains and can reward memorization of sensor, collection, or scenario-specific signatures. Domain-aware splits instead hold out scenarios, days, or sensors, revealing the generalization gap that a deployed spectrum-awareness system would face. This distinction is central for the OpenEW-SA benchmark and for future neuro-symbolic dynamic hypergraph models built on top of it.

The contributions of this paper are:

- A unified OpenEW-SA metadata schema for heterogeneous RF samples.
- Real-data conversion pipelines for JamShield, DeepSense SDR WiFi, and ElectroSense PSD.
- Baseline training and evaluation workflows with detailed classification metrics.
- Domain-aware split protocols covering jammer scenario, jammer family, collection day, and sensor holdout settings.
- Paper-ready dataset, baseline, and domain-holdout tables for the first OpenEW-SA benchmark draft.
- A path toward WiSig RF fingerprinting, RadioML modulation baselines, and neuro-symbolic dynamic hypergraph modeling.

## 2. Related Work

RF machine learning benchmarks commonly focus on individual tasks such as modulation recognition, spectrum sensing, RF fingerprinting, or jamming detection. These datasets have enabled progress in neural architectures for I/Q sequences, spectrograms, PSD traces, and tabular RF/network statistics. However, many evaluations rely on random sample splits. In RF settings, this can blur the distinction between interpolation within a collection domain and generalization to new receivers, days, channels, or interference scenarios.

Spectrum sensing and occupancy datasets provide a natural testbed for domain generalization because sensors and days often define meaningful operational conditions. DeepSense-style SDR captures expose raw I/Q windows and collection-day shifts, while PSD datasets such as ElectroSense expose receiver and location effects over frequency-domain measurements. Jamming and interference datasets such as JamShield add another axis: the abnormal event type and the physical or network conditions under which it occurs.

Prior work on domain generalization and RF fingerprinting has shown that models often rely on environment-specific artifacts. This motivates explicit domain-aware evaluation. OpenEW-SA complements prior task-specific benchmarks by standardizing metadata and reporting across multiple RF modalities. The goal is not to replace specialized datasets, but to make them interoperable for spectrum situation awareness and future structured reasoning.

Neuro-symbolic and graph-based situation-awareness methods also require structured context. Receivers, frequency bands, time windows, emitters, situations, and threats can naturally become typed entities in a graph or hypergraph. OpenEW-SA provides the conversion and evaluation layer needed before such models can be compared fairly against neural baselines.

## 3. OpenEW-SA Benchmark Design

OpenEW-SA is organized around a common artifact contract. Each dataset converter writes:

- `metadata.csv`, containing one row per sample with the unified OpenEW-SA metadata schema.
- `features.npy` or `features.pt`, containing model-ready features.
- `labels.json`, containing label metadata, class names, feature shape, and source-file provenance where available.

The unified metadata schema includes:

```text
sample_id, dataset_source, input_type, time_index, frequency_band, tx_id, rx_id,
modulation_label, occupancy_label, abnormal_event_label, domain_id,
synthetic_mission_context, situation_label, threat_level, human_review_required
```

This schema is intentionally broader than any single dataset. For JamShield, the abnormal event label is central. For DeepSense, the occupancy label is central. For ElectroSense, the situation label carries the technology class. Shared fields such as `dataset_source`, `input_type`, `rx_id`, `domain_id`, and `frequency_band` enable cross-dataset reporting and future structured reasoning.

The benchmark design follows four principles. First, large raw datasets are never downloaded automatically; users place raw data locally and configure paths through YAML or CLI arguments. Second, converters preserve dataset-specific semantics while mapping them into common fields. Third, baselines remain lightweight and reproducible, making them useful reference points rather than final models. Fourth, evaluation emphasizes both random splits and domain-aware holdouts so that in-domain interpolation and out-of-domain generalization are reported separately.

> **Figure 1. OpenEW-SA pipeline overview.** Placeholder for a pipeline diagram showing raw public RF datasets flowing into dataset-specific converters, unified artifacts, baseline training/evaluation, paper tables, and future neuro-symbolic dynamic hypergraph modeling.

## 4. Dataset Conversion

### 4.1 JamShield

The JamShield converter recursively scans raw CSV files and excludes non-data outputs such as inspection summaries. Each raw row contains a sample index, station identifier, numerical metrics, and an `attack` column. Numerical features are formed by excluding `sample`, `station`, and `attack`; the resulting feature vector has 37 dimensions. The `attack` column maps to `normal` when `attack=0` and `abnormal_interference` when `attack=1`. Source CSV stems become `domain_id` values, allowing holdouts by individual scenario or jammer type.

JamShield is represented as tabular RF/network abnormal interference detection. Its converted benchmark contains 92,486 samples, two classes, and 20 domains.

### 4.2 DeepSense SDR WiFi

The DeepSense SDR WiFi converter recursively scans `.bin` files containing complex64 I/Q time series. Filename stems encode four-channel occupancy states, for example `1101_day2.bin`, where the first four characters become the occupancy label and the suffix identifies the collection day. Each stream is segmented into fixed windows and represented as unflattened `[2, 1024]` real/imaginary I/Q tensors, with a flattened dimension of 2,048 when used by tabular baselines.

DeepSense is represented as 4-channel WiFi occupancy classification. Its converted benchmark contains 32,000 samples, 16 occupancy classes, and two domains corresponding to `day1` and `day2`.

### 4.3 ElectroSense PSD

The ElectroSense converter recursively scans PSD `.npy` files, skips too-small files, and treats each PSD row as one sample. Parent folders identify sensors and dates, while filenames encode technology labels and frequency ranges. Each row is resampled to a fixed `[512]` PSD feature vector. Technology labels become `situation_label` values with six classes: `dab`, `dvbt`, `fm`, `gsm`, `lte`, and `tetra`. Sensor identifiers become `domain_id` values.

ElectroSense is represented as PSD technology classification. Its converted benchmark contains 45,750 samples, six classes, and 40 sensor domains.

**Table 1. Dataset summary.**

| dataset | task | samples | input_type | feature_shape | feature_dimension | classes | domains | split_protocols |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| JamShield | Jamming/interference detection | 92,486 | tabular_metrics | [37] | 37 | 2 | 20 | Random row split across JamShield domains.; Hold out selected jammer source domains plus data_benign_4.; Hold out reactive jammer domains plus data_benign_4. |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | 32,000 | iq_features | [2, 1024] | 2,048 | 16 | 2 | Random row split across DeepSense day1/day2 windows.; Train on day1 domains and validate/evaluate on day2 domains.; Random row split using unflattened [2, 1024] I/Q windows. |
| ElectroSense PSD | PSD technology classification | 45,750 | psd_features | [512] | 512 | 6 | 40 | Random row split across ElectroSense PSD samples.; Hold out sensors alcorcon1, bcn-L, and Geneva. |

## 5. Evaluation Protocols

OpenEW-SA reports both random row-level splits and domain-aware splits. Random splits are useful smoke tests and measure within-distribution interpolation. Domain-aware splits are designed to test whether models generalize to conditions not seen during training.

For JamShield, the random split samples rows across all domains. The scenario holdout split evaluates selected jammer source domains plus benign control domain `data_benign_4`. The reactive jammer-type holdout evaluates reactive jammer domains plus the same benign control domain. Including benign control samples ensures binary metrics remain meaningful instead of evaluating only abnormal samples.

For DeepSense, the random split samples windows across `day1` and `day2`. The day-aware holdout trains on `day1` and evaluates on `day2`, exposing cross-day generalization.

For ElectroSense, the random split samples PSD rows across sensors. The sensor holdout evaluates on held-out receiver domains, including `alcorcon1`, `bcn-L`, and `Geneva`, exposing sensor-domain shift.

All runs report accuracy and macro-F1. Binary JamShield runs additionally report AUROC and AUPRC. The training and evaluation pipeline also saves per-class precision, recall, F1, support, prediction counts, confusion matrices, and prediction CSVs for downstream by-domain analysis.

## 6. Baseline Models

The benchmark intentionally uses lightweight baselines so that the results are easy to reproduce and interpret. JamShield uses a tabular MLP over 37 numerical metrics. DeepSense uses both a tabular MLP over flattened I/Q windows and a 1D IQ CNN over unflattened `[2, 1024]` windows. ElectroSense uses a tabular MLP over standardized `[512]` PSD feature vectors.

All training configurations use YAML-controlled paths and model parameters. Feature standardization is fit on training features only and then applied to validation/evaluation features. Class-balanced cross entropy is available for imbalanced classification settings. These choices make the baseline pipeline suitable for controlled comparisons without adding architecture complexity that would obscure the split protocol effects.

## 7. Results

**Table 2. Baseline results.**

| dataset | task | model | split_protocol | accuracy | macro_f1 | auroc | auprc |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| JamShield | Jamming/interference detection | Tabular MLP | Random row split across JamShield domains. | 0.953820 | 0.948885 | 0.996014 | 0.998183 |
| JamShield | Jamming/interference detection | Tabular MLP | Hold out selected jammer source domains plus data_benign_4. | 0.845587 | 0.828574 | 0.970368 | 0.984382 |
| JamShield | Jamming/interference detection | Tabular MLP | Hold out reactive jammer domains plus data_benign_4. | 0.845828 | 0.792954 | 0.928423 | 0.977445 |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | Tabular MLP | Random row split across DeepSense day1/day2 windows. | 0.577562 | 0.614465 |  |  |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | Tabular MLP | Train on day1 domains and validate/evaluate on day2 domains. | 0.151812 | 0.114871 |  |  |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | IQ CNN 1D | Random row split using unflattened [2, 1024] I/Q windows. | 0.740781 | 0.768321 |  |  |
| ElectroSense PSD | PSD technology classification | Tabular MLP | Random row split across ElectroSense PSD samples. | 0.998885 | 0.998862 |  |  |
| ElectroSense PSD | PSD technology classification | Tabular MLP | Hold out sensors alcorcon1, bcn-L, and Geneva. | 0.554571 | 0.536666 |  |  |

> **Figure 2. Baseline macro-F1 comparison.** Placeholder for `D:\openew_sa_data\paper1\figures\figure_baseline_macro_f1.png`, comparing macro-F1 across the baseline rows in Table 2.

The random row-level splits produce the strongest apparent performance. JamShield reaches 0.948885 macro-F1 with high AUROC and AUPRC. ElectroSense is almost saturated under random splitting, with 0.998862 macro-F1. On DeepSense, model choice matters: the IQ CNN substantially improves random-split macro-F1 over the flattened tabular MLP, from 0.614465 to 0.768321.

The domain-aware results change the interpretation. JamShield scenario holdout lowers macro-F1 to 0.828574, and reactive jammer-type holdout lowers it further to 0.792954. DeepSense day2 holdout is much harder for the tabular MLP, with only 0.114871 macro-F1. ElectroSense sensor holdout reduces macro-F1 from 0.998862 to 0.536666. These shifts support the main finding: random row-level splits overestimate RF situation-awareness performance, while domain-aware splits reveal generalization gaps across scenarios, days, and sensors.

**Table 3. Domain-holdout summary.**

| dataset | split_protocol | domain_id | n_samples | true_label_distribution | predicted_label_distribution | accuracy | macro_f1 |
| --- | --- | --- | ---: | --- | --- | ---: | ---: |
| JamShield | Scenario holdout with benign control | constant_jammer_gaussian_25db | 3,918 | {"abnormal_interference": 3918} | {"abnormal_interference": 3918} | 1.000000 | 1.000000 |
| JamShield | Scenario holdout with benign control | data_benign_4 | 7,884 | {"normal": 7884} | {"abnormal_interference": 3037, "normal": 4847} | 0.614789 | 0.380724 |
| JamShield | Scenario holdout with benign control | random_jammer_gaussian_NLOS | 3,290 | {"abnormal_interference": 3290} | {"abnormal_interference": 3205, "normal": 85} | 0.974164 | 0.493457 |
| JamShield | Scenario holdout with benign control | reactive_jammer_square_NLOS | 4,725 | {"abnormal_interference": 4725} | {"abnormal_interference": 4540, "normal": 185} | 0.960847 | 0.490016 |
| JamShield | Reactive jammer-type holdout with benign control | data_benign_4 | 7,884 | {"normal": 7884} | {"abnormal_interference": 2937, "normal": 4947} | 0.627473 | 0.385551 |
| JamShield | Reactive jammer-type holdout with benign control | reactive_jammer_cos_NLOS | 3,195 | {"abnormal_interference": 3195} | {"abnormal_interference": 3040, "normal": 155} | 0.951487 | 0.487570 |
| JamShield | Reactive jammer-type holdout with benign control | reactive_jammer_gaussian_LOS | 7,232 | {"abnormal_interference": 7232} | {"abnormal_interference": 6333, "normal": 899} | 0.875691 | 0.466863 |
| JamShield | Reactive jammer-type holdout with benign control | reactive_jammer_gaussian_additional_end_devices | 3,375 | {"abnormal_interference": 3375} | {"abnormal_interference": 2949, "normal": 426} | 0.873778 | 0.466319 |
| JamShield | Reactive jammer-type holdout with benign control | reactive_jammer_square_NLOS | 4,725 | {"abnormal_interference": 4725} | {"abnormal_interference": 4474, "normal": 251} | 0.946878 | 0.486357 |
| JamShield | Reactive jammer-type holdout with benign control | reactive_jammer_triangle_NLOS | 3,335 | {"abnormal_interference": 3335} | {"abnormal_interference": 3011, "normal": 324} | 0.902849 | 0.474472 |
| ElectroSense PSD | Sensor holdout | Geneva | 1,000 | {"dab": 200, "dvbt": 200, "fm": 200, "lte": 200, "tetra": 200} | {"dab": 215, "dvbt": 366, "gsm": 180, "lte": 200, "tetra": 39} | 0.239000 | 0.221060 |
| ElectroSense PSD | Sensor holdout | alcorcon1 | 4,800 | {"dab": 600, "dvbt": 600, "fm": 600, "gsm": 1800, "lte": 600, "tetra": 600} | {"dab": 299, "dvbt": 885, "fm": 686, "gsm": 1522, "lte": 1043, "tetra": 365} | 0.635833 | 0.618975 |
| ElectroSense PSD | Sensor holdout | bcn-L | 1,200 | {"dab": 200, "dvbt": 200, "fm": 200, "gsm": 200, "lte": 200, "tetra": 200} | {"dab": 2, "dvbt": 112, "fm": 168, "gsm": 663, "lte": 255} | 0.492500 | 0.439398 |

> **Figure 3. Domain-aware macro-F1 comparison.** Placeholder for `D:\openew_sa_data\paper1\figures\figure_domain_holdout_macro_f1.png`, comparing per-domain macro-F1 across JamShield scenario holdout, JamShield reactive holdout, and ElectroSense sensor holdout domains.

Table 3 shows that the holdout problem is not uniform across domains. JamShield abnormal-only held-out jammer domains often retain high accuracy, but macro-F1 is lower when predictions include false normal outputs or when the benign control domain is difficult. The benign `data_benign_4` domain is particularly important because it exposes false abnormal predictions that would be hidden in abnormal-only evaluation.

ElectroSense sensor holdout exposes stronger receiver-domain variation. The Geneva sensor domain has 0.221060 macro-F1, while `alcorcon1` reaches 0.618975 and `bcn-L` reaches 0.439398. The per-class summary from the benchmark shows that DAB nearly collapses under sensor holdout, while FM and LTE remain comparatively stronger. This suggests that some technology classes transfer across sensors more robustly than others.

## 8. Discussion

The results support a simple but important claim: RF situation-awareness benchmarks should not rely only on random row-level splits. Random splits can be useful for checking whether a model and converter are functioning, but they can mix samples from the same scenarios, days, or sensors across train and validation sets. That mixing can make performance appear mature even when the model is not robust to realistic deployment shifts.

The three completed OpenEW-SA subsets demonstrate this pattern from different angles. JamShield shows scenario and jammer-family shift. DeepSense shows collection-day shift. ElectroSense shows sensor-domain shift. In each case, the domain-aware protocol reveals lower macro-F1 than the corresponding random evaluation. The exact magnitude differs by dataset and model, but the direction is consistent.

The benchmark also shows why unified metadata matters. The `domain_id` field is used differently across datasets: JamShield uses source CSV stems, DeepSense uses collection days, and ElectroSense uses sensor IDs. Yet the shared field makes it possible to implement common split logic, generate comparable tables, and analyze per-domain predictions. This same structure can support future graph and hypergraph modeling, where samples, domains, receivers, frequency bands, situations, and threat levels become typed entities.

The baseline results should not be interpreted as final model ceilings. They are intentionally lightweight reference points. More advanced architectures, domain adaptation, calibration, and neuro-symbolic reasoning may improve holdout performance. The benchmark contribution is to make those improvements measurable under protocols that better reflect operational shift.

## 9. Limitations

The current benchmark includes three completed subsets: JamShield, DeepSense SDR WiFi, and ElectroSense PSD. WiSig and RadioML are planned but not yet included in the Paper 1 benchmark tables. As a result, the current manuscript does not yet cover RF fingerprinting or modulation recognition at the same level of experimental detail.

The baselines are deliberately simple. JamShield and ElectroSense use tabular MLPs, while DeepSense uses a tabular MLP and an IQ CNN. These models are useful for establishing reference performance, but they do not exhaust the design space for RF representation learning.

The current draft does not add new experiments beyond the existing OpenEW-SA artifacts. It uses the generated benchmark summaries and paper-ready tables already present in the local workspace. Raw data files are not included in the repository.

Finally, the neuro-symbolic dynamic hypergraph component remains future work. The present paper builds the data, metadata, and evaluation foundation needed for that next step, but it does not yet evaluate a full hypergraph model.

## 10. Conclusion

OpenEW-SA provides a unified benchmark scaffold for electromagnetic spectrum situation awareness across tabular RF/network metrics, raw SDR I/Q windows, and PSD spectrum traces. By converting JamShield, DeepSense, and ElectroSense into common artifacts and metadata, the benchmark enables shared training, evaluation, and paper-table generation across heterogeneous RF tasks.

The main empirical finding is that random row-level splits overestimate performance. JamShield, DeepSense, and ElectroSense all show stronger random-split results than domain-aware results. Scenario, jammer-type, day, and sensor holdouts reveal generalization gaps that are more relevant to deployed spectrum-awareness systems. Future work will extend OpenEW-SA to WiSig and RadioML and use the unified metadata schema as the basis for neuro-symbolic dynamic hypergraph models.
