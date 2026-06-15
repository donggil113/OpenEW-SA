# OpenEW-SA: A Unified Benchmark for Electromagnetic Spectrum Situation Awareness

## Abstract

Electromagnetic spectrum situation awareness requires models that remain reliable across sensors, operating conditions, and signal environments. However, public military electronic warfare data are scarce, and available public RF datasets are fragmented across formats, labels, and evaluation protocols. This paper introduces OpenEW-SA, a reproducible public RF benchmark scaffold for spectrum situation awareness. OpenEW-SA converts heterogeneous datasets into shared artifacts with a unified metadata schema and evaluates lightweight baselines under both random and domain-aware splits. The current benchmark includes JamShield tabular RF/network abnormal interference detection, DeepSense SDR WiFi I/Q occupancy classification, and ElectroSense PSD technology classification. Random row-level splits produce strong apparent performance, including JamShield macro-F1 of 0.948885, DeepSense IQ-CNN macro-F1 of 0.768321, and ElectroSense macro-F1 of 0.998862. Domain-aware splits reveal larger generalization gaps: JamShield scenario and reactive holdouts fall to 0.828574 and 0.792954 macro-F1, DeepSense day2 holdout falls to 0.114871 for the MLP and 0.217708 for the IQ-CNN, and ElectroSense sensor holdout falls to 0.536666. These results show that random row-level splits can overestimate RF situation-awareness performance, while scenario, day, and sensor holdouts expose deployment-relevant failure modes.

## 1. Introduction

Military electronic warfare (EW) and spectrum operations depend on timely awareness of emitters, interference, occupancy, sensors, and mission context. In operational settings, models may need to identify abnormal interference, infer channel occupancy, classify spectrum technology, or flag observations for human review. These tasks are linked by shared RF environments and by domain shifts across receivers, collection days, geography, frequency bands, and interference scenarios.

Progress in this area is constrained by data availability. Real military EW data are rarely public because they can contain sensitive platforms, waveforms, locations, tactics, or collection capabilities. As a result, reproducible research must often rely on public RF datasets that were not originally designed as a unified EW benchmark. These datasets are valuable, but they are heterogeneous: JamShield provides tabular WiFi metrics for benign and jamming conditions \cite{panitsas2025jamshield,panitsas2024jamshieldDatasetGithub,panitsas2024jamshieldDatasetDataport}, DeepSense SDR WiFi provides raw I/Q captures with occupancy labels \cite{uvaydov2021deepsense,wiotlab2021deepsenseGithub}, and ElectroSense provides PSD traces over distributed sensors and spectrum technologies \cite{scalingi2023wirelessTechnologyClassification,scalingi2023electrosensePsdDataset,rajendran2017electrosenseOpenBig}.

This fragmentation creates two practical problems. First, raw formats and label conventions differ across datasets, making it difficult to compare models or build a cumulative evidence base. Second, many RF evaluations use random row-level splits that mix domains across training and validation. Such splits are useful for smoke testing, but they can hide failures that appear when a model is evaluated on unseen sensors, days, or interference scenarios. For spectrum situation awareness, these shifts are not edge cases; they are central to deployment.

OpenEW-SA addresses these problems by converting public RF datasets into a unified benchmark scaffold. As summarized in Figure 1, each dataset passes through a dataset-specific converter and is represented by `metadata.csv`, `features.npy` or `features.pt`, and `labels.json`. The metadata schema records dataset source, input type, frequency band, receiver identity, domain, task labels, situation label, threat level, and human-review status. This common structure supports consistent training, evaluation, paper-table generation, and future neuro-symbolic dynamic hypergraph modeling.

The current benchmark includes three completed subsets. JamShield supports tabular RF/network abnormal interference detection. DeepSense SDR WiFi supports 4-channel I/Q occupancy classification. ElectroSense supports PSD technology classification. Table 1 reports the resulting sample counts, feature shapes, class counts, and domain counts. Across these subsets, the primary empirical result is consistent: random row-level splits overestimate RF situation-awareness performance, while domain-aware splits reveal generalization gaps across scenarios, days, and sensors.

The contributions of this paper are:

- A unified OpenEW-SA metadata schema for heterogeneous RF samples.
- Real-data conversion pipelines for JamShield, DeepSense SDR WiFi, and ElectroSense PSD.
- Baseline training and evaluation workflows with detailed classification metrics.
- Domain-aware split protocols covering jammer scenario, jammer family, collection day, and sensor holdout settings.
- Paper-ready dataset, baseline, and domain-holdout summaries for the first OpenEW-SA benchmark release.
- A foundation for future WiSig RF fingerprinting, RadioML modulation baselines, and neuro-symbolic dynamic hypergraph models.

## 2. Related Work

RF machine learning benchmarks commonly focus on specific tasks such as modulation recognition, spectrum sensing, jamming detection, RF fingerprinting, or transmitter identification \cite{hall2019referenceRfDatasets,boegner2022largeScaleRfClassification}. Modulation recognition datasets have been especially influential for I/Q representation learning \cite{oshea2016convolutionalRadioModulation,deepsig2016radioml2016a}, while spectrum sensing datasets provide occupancy and sensing tasks closer to spectrum-monitoring workflows \cite{uvaydov2021deepsense,rajendran2017electrosenseOpenBig}. RF fingerprinting benchmarks further emphasize device identity and receiver-domain effects \cite{hanna2022wisig,coreslab2022wisigDataset}. For spectrum situation awareness, however, task performance alone is insufficient. A useful benchmark must also expose whether a model generalizes across operational domains.

Spectrum sensing and occupancy datasets provide natural domain shifts because sensors, days, and locations often correspond to different propagation and hardware conditions \cite{uvaydov2021deepsense,rajendran2017electrosenseOpenBig}. DeepSense-style SDR captures expose raw I/Q windows and collection-day variation \cite{uvaydov2021deepsense,wiotlab2021deepsenseGithub}. ElectroSense-style PSD measurements expose receiver and location effects across frequency-domain observations \cite{scalingi2023wirelessTechnologyClassification,scalingi2023electrosensePsdDataset,rajendran2017electrosenseOpenBig}. Jamming and interference datasets such as JamShield add scenario and jammer-family shifts, which are especially relevant to abnormal-event detection \cite{panitsas2025jamshield,panitsas2024jamshieldDatasetGithub,panitsas2024jamshieldDatasetDataport}.

Domain generalization is a recurring challenge in RF learning \cite{zhang2025domainGeneralizationRff}. Models can exploit receiver artifacts, collection conditions, or scenario-specific signatures that do not transfer to new domains. Random sample splits may therefore conflate within-domain interpolation with out-of-domain generalization. OpenEW-SA is designed to make that distinction explicit by reporting both random row-level baselines and domain-aware holdouts.

The benchmark also connects to neuro-symbolic reasoning \cite{cheng2024neuralSymbolicKgSurvey,liu2025neuralSymbolicQuerySurvey,delong2023neurosymbolicAiKgSurvey} and graph/hypergraph situation awareness \cite{gao2024hypergraphSituationAwareness,alavizadeh2022cyberSituationAwarenessSurvey}. Receivers, domains, bands, time windows, labels, and threat states can be treated as typed entities in a graph or hypergraph. Before such models can be evaluated, the underlying data must be converted into consistent artifacts with comparable metadata. OpenEW-SA provides that conversion and evaluation layer.

## 3. OpenEW-SA Benchmark Design

OpenEW-SA is organized around the workflow shown in Figure 1. Public RF datasets are first processed by dataset-specific converters, then standardized into shared artifacts, evaluated with lightweight baselines, and summarized through paper-ready outputs. Each dataset converter produces:

- `metadata.csv`, with one row per sample using the unified OpenEW-SA schema.
- `features.npy` or `features.pt`, with model-ready numerical features.
- `labels.json`, with class names, label metadata, feature shape, and source provenance when available.

The unified metadata schema is:

```text
sample_id, dataset_source, input_type, time_index, frequency_band, tx_id, rx_id,
modulation_label, occupancy_label, abnormal_event_label, domain_id,
synthetic_mission_context, situation_label, threat_level, human_review_required
```

The schema is intentionally broader than any individual dataset. JamShield primarily uses `abnormal_event_label`, DeepSense primarily uses `occupancy_label`, and ElectroSense primarily uses `situation_label`. Shared fields such as `dataset_source`, `input_type`, `frequency_band`, `rx_id`, and `domain_id` make cross-dataset analysis possible. The `domain_id` field is especially important because it supports scenario, day, and sensor holdouts without requiring dataset-specific training code.

The benchmark design follows four principles. First, large public datasets are not downloaded automatically; users provide raw files locally and configure paths explicitly. Second, dataset-specific converters preserve source semantics while mapping samples into common metadata. Third, baseline models are intentionally lightweight so that split-protocol effects remain interpretable. Fourth, evaluation reports random row-level splits alongside domain-aware splits, separating in-domain interpolation from deployment-relevant generalization.

> **Figure 1. OpenEW-SA pipeline overview.** Placeholder for `D:\openew_sa_data\paper1\figures\figure_pipeline_overview.png`, showing public RF datasets, dataset-specific converters, unified artifacts, baseline models, domain-aware evaluation, paper outputs, and future neuro-symbolic dynamic hypergraph reasoning.

## 4. Dataset Conversion

Table 1 summarizes the three completed OpenEW-SA subsets, including task definitions, feature shapes, class counts, domain counts, and split protocols. The table is intended to make the benchmark scope explicit before comparing model performance in Table 2 and domain-aware behavior in Table 3, Figure 3, and Supplementary Table S1.

### 4.1 JamShield

The JamShield converter recursively scans raw CSV files and excludes non-data outputs such as inspection summaries. Each raw row contains a sample index, station identifier, numerical metrics, and an `attack` column. Features are formed from numerical columns after excluding `sample`, `station`, and `attack`, yielding a 37-dimensional tabular feature vector. The `attack` field maps to `normal` for `attack=0` and `abnormal_interference` for `attack=1`. Source CSV stems define `domain_id` values, which support scenario and jammer-family holdout protocols.

JamShield is used for tabular RF/network abnormal interference detection. The converted subset contains 92,486 samples, two classes, and 20 domains.

### 4.2 DeepSense SDR WiFi

The DeepSense converter recursively scans `.bin` files containing complex64 I/Q time series. Filename stems encode four-channel occupancy labels, such as `1101_day2.bin`; the first four characters become the occupancy label, and the suffix identifies the collection day. Each stream is segmented into fixed windows and represented as `[2, 1024]` real/imaginary I/Q tensors. For tabular baselines, the same windows can be treated as 2,048-dimensional flattened features.

DeepSense is used for 4-channel WiFi occupancy classification. The converted subset contains 32,000 samples, 16 occupancy classes, and two day domains.

### 4.3 ElectroSense PSD

The ElectroSense converter recursively scans PSD `.npy` files, skips too-small files, and treats each PSD row as one sample. Parent folders identify sensors and dates, while filenames encode technology labels and frequency ranges. Each row is resampled to a fixed `[512]` PSD feature vector. Technology labels become `situation_label` values with six classes: `dab`, `dvbt`, `fm`, `gsm`, `lte`, and `tetra`. Sensor identifiers become `domain_id` values.

ElectroSense is used for PSD technology classification. The converted subset contains 45,750 samples, six classes, and 40 sensor domains.

**Table 1. Dataset summary.**

| dataset | task | samples | input_type | feature_shape | feature_dimension | classes | domains | split_protocols |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| JamShield | Jamming/interference detection | 92,486 | tabular_metrics | [37] | 37 | 2 | 20 | Random row split across JamShield domains.; Hold out selected jammer source domains plus data_benign_4.; Hold out reactive jammer domains plus data_benign_4. |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | 32,000 | iq_features | [2, 1024] | 2,048 | 16 | 2 | Random row split across DeepSense day1/day2 windows.; Train on day1 domains and validate/evaluate on day2 domains.; Random row split using unflattened [2, 1024] I/Q windows. |
| ElectroSense PSD | PSD technology classification | 45,750 | psd_features | [512] | 512 | 6 | 40 | Random row split across ElectroSense PSD samples.; Hold out sensors alcorcon1, bcn-L, and Geneva. |

## 5. Evaluation Protocols

OpenEW-SA evaluates each task with random row-level splits and, where supported by metadata, domain-aware holdouts. Random splits estimate within-distribution performance when samples from the same domains may appear in both training and validation. Domain-aware splits hold out complete domains, giving a more stringent estimate of generalization to unseen operating conditions. The aggregate effect of these protocols is reported in Table 2 and visualized in Figure 2.

For JamShield, the random split samples rows across all domains. The scenario holdout evaluates selected jammer source domains plus the benign control domain `data_benign_4`. The reactive jammer-type holdout evaluates reactive jammer domains plus the same benign control domain. Including benign samples in the holdout is necessary for meaningful binary evaluation because abnormal-only validation sets can make AUROC, AUPRC, and normal-class support difficult to interpret.

For DeepSense, the random split samples I/Q windows across `day1` and `day2`. The day-aware holdout trains on `day1` and evaluates on `day2`, testing temporal and collection-condition transfer.

For ElectroSense, the random split samples PSD rows across sensors. The sensor holdout evaluates held-out receiver domains, including `alcorcon1`, `bcn-L`, and `Geneva`, testing whether PSD technology recognition transfers across sensing sites.

All runs report accuracy and macro-F1. Binary JamShield runs additionally report AUROC and AUPRC. The training and evaluation pipeline also writes per-class precision, recall, F1, support, prediction counts, confusion matrices, and prediction CSVs for by-domain analysis. Table 2 reports aggregate baseline metrics, Table 3 summarizes the domain-aware holdout findings, and Figure 3 and Supplementary Table S1 report the detailed per-domain behavior.

## 6. Baseline Models

The baseline suite is intentionally compact. The purpose is to establish reproducible reference points and expose split-protocol effects, rather than to maximize task-specific accuracy with heavily tuned architectures.

JamShield uses a tabular MLP over 37 numerical RF/network metrics. DeepSense uses two baselines: a tabular MLP over flattened I/Q windows and a 1D IQ CNN over unflattened `[2, 1024]` I/Q tensors. ElectroSense uses a tabular MLP over standardized `[512]` PSD vectors. These model choices correspond to the baseline rows in Table 2 and the macro-F1 comparison in Figure 2.

All training configurations use YAML-controlled paths and model parameters. Feature standardization is fit on training features only and then applied to validation/evaluation features. Class-balanced cross entropy is available for imbalanced classification settings. This design keeps the baseline pipeline reproducible while avoiding leakage from validation domains into preprocessing.

## 7. Results

Table 2 presents the aggregate baseline results, and Figure 2 provides the corresponding macro-F1 comparison. The purpose of Figure 2 is to make the random-versus-holdout contrast visible across datasets and models. Table 3 then condenses the domain-aware failure modes across JamShield and ElectroSense, while Figure 3 and Supplementary Table S1 preserve the detailed per-domain behavior.

**Table 2. Baseline results.**

| dataset | task | model | split_protocol | accuracy | macro_f1 | auroc | auprc |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| JamShield | Jamming/interference detection | Tabular MLP | Random row split across JamShield domains. | 0.953820 | 0.948885 | 0.996014 | 0.998183 |
| JamShield | Jamming/interference detection | Tabular MLP | Hold out selected jammer source domains plus data_benign_4. | 0.845587 | 0.828574 | 0.970368 | 0.984382 |
| JamShield | Jamming/interference detection | Tabular MLP | Hold out reactive jammer domains plus data_benign_4. | 0.845828 | 0.792954 | 0.928423 | 0.977445 |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | Tabular MLP | Random row split across DeepSense day1/day2 windows. | 0.577562 | 0.614465 |  |  |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | Tabular MLP | Train on day1 domains and validate/evaluate on day2 domains. | 0.151812 | 0.114871 |  |  |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | IQ CNN 1D | Random row split using unflattened [2, 1024] I/Q windows. | 0.740781 | 0.768321 |  |  |
| DeepSense SDR WiFi | 4-channel WiFi occupancy classification | IQ CNN 1D | Train on day1 domains and validate/evaluate on day2 domains. | 0.281125 | 0.217708 |  |  |
| ElectroSense PSD | PSD technology classification | Tabular MLP | Random row split across ElectroSense PSD samples. | 0.998885 | 0.998862 |  |  |
| ElectroSense PSD | PSD technology classification | Tabular MLP | Hold out sensors alcorcon1, bcn-L, and Geneva. | 0.554571 | 0.536666 |  |  |

> **Figure 2. Baseline macro-F1 comparison.** Placeholder for `D:\openew_sa_data\paper1\figures\figure_baseline_macro_f1.png`, which visualizes the macro-F1 values reported in Table 2.

The random row-level results in Table 2 are strong across the completed benchmark, and the relative pattern is visible in Figure 2. JamShield reaches 0.948885 macro-F1 with AUROC 0.996014 and AUPRC 0.998183. ElectroSense is nearly saturated under random splitting, with 0.998862 macro-F1. DeepSense shows that representation matters: the IQ CNN reaches 0.768321 macro-F1 under random splitting, improving over the flattened MLP result of 0.614465.

The domain-aware results substantially change the interpretation. JamShield scenario holdout reduces macro-F1 to 0.828574, and reactive jammer-type holdout reduces macro-F1 to 0.792954. DeepSense day2 holdout falls to 0.114871 macro-F1 for the MLP. The day2 holdout IQ-CNN improves accuracy to 0.281125 and macro-F1 to 0.217708, showing that an architecture matched to unflattened I/Q windows helps cross-day transfer, but still leaves a large day-level domain gap relative to the 0.768321 random-split IQ-CNN macro-F1. ElectroSense sensor holdout falls from 0.998862 macro-F1 under random splitting to 0.536666. Thus, the same benchmark that appears strong under random splits reveals clear generalization gaps under scenario, day, and sensor holdouts. Figure 2 summarizes this aggregate pattern, while Table 3, Figure 3, and Supplementary Table S1 show that the holdout degradation also varies by protocol and individual domain.

Multi-seed robustness results over seeds 0, 1, and 2 show that the random-versus-holdout contrast is stable. JamShield random splitting reaches 0.9558 $\pm$ 0.0012 macro-F1, while JamShield domain holdout reaches 0.8252 $\pm$ 0.0128. DeepSense day2 MLP holdout remains low at 0.1021 $\pm$ 0.0110 macro-F1, and the day2 IQ-CNN improves to 0.2165 $\pm$ 0.0020 while still remaining far below the random IQ-CNN setting. ElectroSense random splitting remains near saturation at 0.9931 $\pm$ 0.0004 macro-F1, whereas ElectroSense sensor holdout drops to 0.4631 $\pm$ 0.0414.

**Table 3. Concise domain-aware holdout summary.**

| dataset | domain-aware protocol | held-out domains | macro-F1 range | main failure mode |
| --- | --- | --- | --- | --- |
| JamShield | Scenario holdout with benign control | `constant_jammer_gaussian_25db`, `data_benign_4`, `random_jammer_gaussian_NLOS`, `reactive_jammer_square_NLOS` | 0.380724 to 1.000000 | The benign control domain drives the lowest macro-F1 through false abnormal predictions; abnormal-only jammer domains are easier. |
| JamShield | Reactive jammer-type holdout with benign control | `data_benign_4`, `reactive_jammer_cos_NLOS`, `reactive_jammer_gaussian_LOS`, `reactive_jammer_gaussian_additional_end_devices`, `reactive_jammer_square_NLOS`, `reactive_jammer_triangle_NLOS` | 0.385551 to 0.487570 | Reactive-family transfer remains difficult across jammer domains, with benign-control false abnormal predictions still limiting macro-F1. |
| ElectroSense PSD | Sensor holdout | `Geneva`, `alcorcon1`, `bcn-L` | 0.221060 to 0.618975 | Sensor-domain shift is strongest for Geneva, with DAB collapse and comparatively stronger FM/LTE transfer. |

> **Figure 3. Domain-aware macro-F1 comparison.** Placeholder for `D:\openew_sa_data\paper1\figures\figure_domain_holdout_macro_f1.png`, which visualizes the per-domain macro-F1 values summarized in Table 3 and reported in full in Supplementary Table S1.

Table 3 shows that holdout performance varies strongly by protocol, and Figure 3 provides a compact view of the underlying domain-level variation. Supplementary Table S1 gives the full domain table, including sample counts, true and predicted label distributions, accuracy, and macro-F1. For JamShield, abnormal-only held-out jammer domains can retain high accuracy, but the benign control domain reveals false abnormal predictions that would be hidden in abnormal-only evaluation. The `data_benign_4` domain reaches only 0.380724 macro-F1 in the scenario holdout and 0.385551 macro-F1 in the reactive holdout, emphasizing why benign controls are needed for binary interference evaluation.

JamShield threshold analysis shows that calibration and decision thresholds matter under holdout evaluation. For the scenario/domain holdout, the default 0.50 threshold gives F1 0.875831, while the best evaluated threshold is 0.95 with F1 0.937551. For the reactive holdout, the default 0.50 threshold gives F1 0.888087, while the best evaluated threshold is 0.40 with F1 0.894402. The larger gain in the scenario holdout indicates that part of the binary holdout error is threshold-sensitive rather than purely ranking-sensitive.

ElectroSense sensor holdout exposes even stronger receiver-domain variation. Geneva reaches 0.221060 macro-F1, `alcorcon1` reaches 0.618975, and `bcn-L` reaches 0.439398. The per-domain class-error analysis in `papers/paper1_openew_sa/electrosense_error_analysis.md` shows that DAB collapses across the held-out sensors, while LTE remains stable. FM is strong for `alcorcon1` and `bcn-L`, reaching 0.933126 and 0.913043 F1, but fails on Geneva with 0.000000 F1. Figure 3 is intended to make these domain-level differences visible at a glance.

## 8. Discussion

The principal lesson from OpenEW-SA is methodological: RF situation-awareness benchmarks should not rely only on random row-level splits. Random splits can confirm that a converter, model, and training loop are functioning, but they can also mix samples from the same sensor, day, or scenario across train and validation sets. In that case, strong performance may reflect within-domain interpolation rather than operational robustness. The contrast between Table 2 and Table 3, together with Figures 2 and 3 and Supplementary Table S1, makes this issue visible at both aggregate and domain-specific levels.

The three completed subsets expose this issue through complementary modalities. JamShield shows that abnormal interference detection changes under scenario and jammer-family holdouts. DeepSense shows that WiFi occupancy classification changes under collection-day holdout. ElectroSense shows that PSD technology classification changes under sensor holdout. Across all three, the random split gives a more optimistic picture than the domain-aware protocol.

The unified schema is central to this analysis. The meaning of `domain_id` differs by dataset, but the field serves the same benchmark role: it identifies the unit that should be held out to test generalization. In JamShield, `domain_id` is a source CSV stem; in DeepSense, it is a collection day; in ElectroSense, it is a sensor. This consistency allows shared split logic, shared reporting, and cross-dataset comparison.

The same metadata structure also prepares the benchmark for neuro-symbolic dynamic hypergraph modeling, shown as the future extension in Figure 1. Samples, domains, receivers, bands, situations, threat levels, and human-review indicators can become typed nodes or attributes. The present paper establishes the data and evaluation foundation needed before more structured models can be evaluated fairly.

## 9. Limitations

The current benchmark includes three completed subsets: JamShield, DeepSense SDR WiFi, and ElectroSense PSD. WiSig and RadioML remain planned extensions and are not included in the Paper 1 benchmark tables. The current manuscript therefore does not yet cover RF fingerprinting \cite{hanna2022wisig,coreslab2022wisigDataset} or modulation recognition \cite{oshea2016convolutionalRadioModulation,deepsig2016radioml2016a} at the same experimental depth.

The baselines are intentionally lightweight. JamShield and ElectroSense use tabular MLPs, while DeepSense uses a tabular MLP and an IQ CNN. These models are appropriate reference points, but they do not represent the full range of possible RF architectures, domain adaptation methods, calibration strategies, or neuro-symbolic models.

The paper reports experiments generated through the current OpenEW-SA repository workflow and does not redistribute raw datasets. It uses existing OpenEW-SA artifacts, generated benchmark summaries, and paper-ready tables produced by that workflow.

Finally, the neuro-symbolic dynamic hypergraph component remains future work. OpenEW-SA provides the schema and evaluation scaffold for that direction, but this manuscript does not yet evaluate a full hypergraph model.

## 10. Conclusion

OpenEW-SA provides a reproducible public RF benchmark scaffold for electromagnetic spectrum situation awareness. By converting JamShield, DeepSense SDR WiFi, and ElectroSense PSD into unified artifacts and metadata, it enables consistent baseline training, domain-aware evaluation, and paper-ready reporting across heterogeneous RF modalities.

The main empirical finding is that random row-level splits overestimate performance. JamShield, DeepSense, and ElectroSense all show stronger random-split results than domain-aware results. Scenario, jammer-type, day, and sensor holdouts reveal generalization gaps that better approximate deployment challenges. Future work will extend the benchmark to WiSig and RadioML and use the unified metadata schema as the basis for neuro-symbolic dynamic hypergraph models.

## Figure and Table Captions

- **Figure 1. OpenEW-SA pipeline overview.** Workflow from public RF datasets through dataset-specific converters, unified artifacts, baseline models, domain-aware evaluation, paper-ready outputs, and future neuro-symbolic dynamic hypergraph reasoning.
- **Figure 2. Baseline macro-F1 comparison.** Macro-F1 values for JamShield, DeepSense, and ElectroSense baseline runs, contrasting random row-level splits with scenario, day, and sensor holdout protocols.
- **Figure 3. Domain holdout macro-F1 comparison.** Per-domain macro-F1 values for JamShield scenario/reactive holdouts and ElectroSense sensor holdout, showing heterogeneous generalization behavior across held-out domains.
- **Table 1. Dataset summary.** Converted OpenEW-SA subsets, tasks, sample counts, input types, feature shapes, class counts, domain counts, and split protocols.
- **Table 2. Baseline results.** Aggregate baseline accuracy, macro-F1, and binary AUROC/AUPRC where applicable for random and domain-aware evaluation protocols.
- **Table 3. Concise domain-aware holdout summary.** Protocol-level summary of held-out domains, macro-F1 ranges, and main observed failure modes for JamShield and ElectroSense holdout analyses.
- **Supplementary Table S1. Detailed domain-holdout results.** Domain-level sample counts, true and predicted label distributions, accuracy, and macro-F1 values corresponding to Table 3 and Figure 3.

## References

References are maintained in `papers/paper1_openew_sa/references.bib`.
