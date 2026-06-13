# Paper 1 Reference TODO Mapping

This file maps every reference placeholder currently used in `draft.md` to candidate citations. The entries are intentionally reference-planning notes only; no BibTeX entries are invented here.

| placeholder | recommended citation title | authors if known | year | source type | why it is needed in the manuscript | status |
| --- | --- | --- | --- | --- | --- | --- |
| `[REF: RF machine learning benchmarks]` | Reference Data Sets for Training and Evaluating RF Signal Detection and Classification Models | Timothy Hall, Raied M. Caromi, Michael R. Souryal, Adam J. Wunderlich | 2020 | paper | Supports the claim that RF signal detection/classification benchmarks need reusable reference datasets and evaluation data. | needs BibTeX |
| `[REF: RF machine learning benchmarks]` | Large Scale Radio Frequency Signal Classification | Luke Boegner, Manbir Gulati, Garrett Vanhoy, Phillip Vallance, Bradley Comar, Silvija Kokalj-Filipovic, Craig Lennon, Robert D. Miller | 2022 | paper | Provides a modern RFML benchmark/dataset example and helps situate OpenEW-SA among RF signal-classification benchmarks. | needs BibTeX |
| `[REF: modulation recognition datasets]` | Convolutional Radio Modulation Recognition Networks | Timothy J. O'Shea, Johnathan Corgan, T. Charles Clancy | 2016 | paper | Motivates RadioML-style modulation recognition as a foundational RFML benchmark family and optional OpenEW-SA extension. | needs BibTeX |
| `[REF: modulation recognition datasets]` | RadioML 2016.10A | DeepSig; commonly associated with Timothy O'Shea and the RadioML dataset release | 2016 | dataset page | Documents the optional RadioML 2016.10A baseline/pretraining dataset mentioned in the manuscript limitations and future work. | needs BibTeX |
| `[REF: spectrum sensing datasets]` | DeepSense: Fast Wideband Spectrum Sensing Through Real-Time In-the-Loop Deep Learning | Daniel Uvaydov, Salvatore D'Oro, Francesco Restuccia, Tommaso Melodia | 2021 | paper | Supports the spectrum-sensing and occupancy-dataset discussion, especially real-time wideband sensing and the DeepSense subset. | needs BibTeX |
| `[REF: spectrum sensing datasets]` | Electrosense: Open and Big Spectrum Data | Sreeraj Rajendran, Roberto Calvo-Palomino, Markus Fuchs, Bertold Van den Bergh, Hector Cordobes, Domenico Giustiniano, Sofie Pollin, Vincent Lenders | 2017 | paper | Supports the broader public spectrum-sensing/crowdsensing context and the use of distributed PSD observations. | needs BibTeX |
| `[REF: DeepSense]` | DeepSense: Fast Wideband Spectrum Sensing Through Real-Time In-the-Loop Deep Learning | Daniel Uvaydov, Salvatore D'Oro, Francesco Restuccia, Tommaso Melodia | 2021 | paper | Primary citation for the DeepSense SDR WiFi/spectrum-sensing data source converted in OpenEW-SA. | needs BibTeX |
| `[REF: DeepSense]` | deepsense-spectrum-sensing-datasets | WIoT Networking, Artificial Intelligence, and Statistical Learning Lab; paper authors are Daniel Uvaydov, Salvatore D'Oro, Francesco Restuccia, Tommaso Melodia | 2021 | GitHub | Dataset/code source for manual download and reproducibility notes around the DeepSense converter. | needs BibTeX |
| `[REF: JamShield]` | JamShield: A Machine Learning Detection System for Over-the-Air Jamming Attacks | Ioannis Panitsas, Yagmur Yigit, Leandros Tassiulas, Leandros Maglaras, Berk Canberk | 2025 | paper | Primary citation for the JamShield jamming/interference detection task and over-the-air jamming context. | needs BibTeX |
| `[REF: JamShield]` | JamShield-Dataset | Ioannis Panitsas, Yagmur Yigit, Leandros Tassiulas, Leandros Maglaras | 2024 | GitHub | Dataset source for the raw JamShield CSV files and domain identifiers used in the OpenEW-SA converter. | needs BibTeX |
| `[REF: ElectroSense]` | A Framework for Wireless Technology Classification using Crowdsensing Platforms | Alessio Scalingi, Domenico Giustiniano, Roberto Calvo-Palomino, Nikolaos Apostolakis, Gerome Bovet | 2023 | paper | Primary citation for the ElectroSense PSD technology-classification framework; some repository text labels it as spectrum classification. | needs BibTeX |
| `[REF: ElectroSense]` | ElectroSense PSD Spectrum Dataset | Alessio Scalingi | 2023 | Zenodo | Dataset source for the PSD `.npy` files used by the ElectroSense converter and sensor-holdout experiments. | needs BibTeX |
| `[REF: ElectroSense]` | Electrosense: Open and Big Spectrum Data | Sreeraj Rajendran, Roberto Calvo-Palomino, Markus Fuchs, Bertold Van den Bergh, Hector Cordobes, Domenico Giustiniano, Sofie Pollin, Vincent Lenders | 2017 | paper | Platform citation for the ElectroSense crowdsensing network and open spectrum-data framing. | needs BibTeX |
| `[REF: RF domain generalization]` | Domain Generalization for Cross-Receiver Radio Frequency Fingerprint Identification | Ying Zhang, Qiang Li, Hongli Liu, Liu Yang, Jian Yang | 2025 | paper | Supports the claim that receiver/domain shift is a recurring RF learning problem and motivates domain-aware evaluation. | needs BibTeX |
| `[REF: RF fingerprinting]` | WiSig: A Large-Scale WiFi Signal Dataset for Receiver and Channel Agnostic RF Fingerprinting | Samer Hanna, Samurdhi Karunaratne, Danijela Cabric | 2022 | paper | Supports the planned WiSig RF fingerprinting extension and the manuscript's discussion of receiver/channel effects. | needs BibTeX |
| `[REF: RF fingerprinting]` | WiSig RF Fingerprinting Dataset | CORES Lab, UCLA; Samer Hanna, Samurdhi Karunaratne, Danijela Cabric | 2022 | dataset page | Dataset-page citation for the public WiSig data source that OpenEW-SA plans to support. | needs BibTeX |
| `[REF: neuro-symbolic reasoning]` | Neural-Symbolic Methods for Knowledge Graph Reasoning: A Survey | Kewei Cheng, Nesreen K. Ahmed, Ryan A. Rossi, Theodore L. Willke, Yizhou Sun | 2024 | survey | Provides background for the proposed neuro-symbolic reasoning direction after the benchmark scaffold is established. | needs BibTeX |
| `[REF: neuro-symbolic reasoning]` | Neural-Symbolic Reasoning over Knowledge Graphs: A Survey from a Query Perspective | Lihui Liu, Zihao Wang, Hanghang Tong | 2024/2025 | survey | Alternative or complementary survey focused on query-oriented neural-symbolic KG reasoning; verify whether citing the arXiv preprint or ACM SIGKDD Explorations version. | needs BibTeX |
| `[REF: graph/hypergraph situation awareness]` | Representing and Assessing Distributed Situation Awareness in Multi-Agency Disaster Response: A Hypergraph-Based Methodology | Chong Gao, Hui Jiang, Xiaoling Guo | 2024 | paper | Motivates using hypergraphs to represent higher-order situation-awareness relationships. | needs BibTeX |
| `[REF: graph/hypergraph situation awareness]` | A Survey on Cyber Situation-awareness Systems: Framework, Techniques, and Insights | Hooman Alavizadeh, Julian Jang-Jaccard, Simon Yusuf Enoch, et al. | 2022 | survey | Provides broader situation-awareness framing and can support the discussion of graph/knowledge-structured SA systems. | needs BibTeX |

## Coverage Check

- `[REF: RF machine learning benchmarks]`
- `[REF: modulation recognition datasets]`
- `[REF: spectrum sensing datasets]`
- `[REF: DeepSense]`
- `[REF: JamShield]`
- `[REF: ElectroSense]`
- `[REF: RF domain generalization]`
- `[REF: RF fingerprinting]`
- `[REF: neuro-symbolic reasoning]`
- `[REF: graph/hypergraph situation awareness]`
