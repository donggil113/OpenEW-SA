# WiSig Official-Evidence Matrix

Status vocabulary: **VERIFIED** means supported by the official UCLA release, the peer-reviewed dataset paper, or the authors' released code. **UNRESOLVED** means the evidence examined does not establish the claim. No filesystem modification time is treated as acquisition time.

| # | Requirement | Official evidence and exact location | Status / confidence | Qualification note |
|---:|---|---|---|---|
| 1 | Receivers | Official overview, *Overview*: 41 USRP receivers. The official metadata index contains 41 receiver slots. | VERIFIED / high | `receiver_id` is acquisition context. |
| 2 | Transmitters | Official overview, *Overview*: 174 off-the-shelf Wi-Fi transmitters. | VERIFIED / high | This is the prediction target, never a relation. |
| 3 | Acquisition days | Dataset paper, capture description: 1, 8, 15, and 23 March 2021; official index keys match those four dates. | VERIFIED / high | Coarse domain/split context only. |
| 4 | Frequency/channel | Dataset paper, experimental setup: Wi-Fi channel 13, 2462 MHz center, 20 MHz Wi-Fi bandwidth. | VERIFIED / high | Constant acquisition setting, not a useful grouping relation. |
| 5 | Sample rate | Dataset paper and raw filename/parser code: 25 MS/s. | VERIFIED / high | Acquisition feature/provenance. |
| 6 | Capture/session identifier | Raw filenames identify one transmitter--receiver capture and encode capture parameters; no target-neutral session ID is released. | PARTIAL / high | Raw capture identity is target-bearing. |
| 7 | Packet/capture ordering | `split_signal_fun.py` detects packets sequentially within a raw capture. Compact pickle creation and example training code do not preserve a stable source-record key and may shuffle samples. | PARTIAL / high | Order exists only within a target-pure capture. |
| 8 | Acquisition timestamps | No per-packet or per-capture acquisition timestamp was found in the official schema/code. Day is recorded only as a date key. | UNRESOLVED / high | Filesystem mtime is rejected. |
| 9 | Receiver identity | Receiver is explicit in raw filenames, raw metadata indexes, and compact subset `rx_list`. | VERIFIED / high | Eligible equality relation after partition isolation. |
| 10 | Transmitter identity | Transmitter/node is explicit in paths, filenames, indexes, and subset `tx_list`. | VERIFIED / high | Annotation/target only. |
| 11 | Hardware identity | Dataset paper reports transmitter chip families (Atheros AR5212/AR9220/AR9280/AR9580) and USRP receiver families (B210/X310/N210). | VERIFIED / medium | Hardware family is provenance; per-record mapping must be checked before use. |
| 12 | Tx/Rx geometry | Dataset paper describes the ORBIT 20 x 20 grid and approximately 1 m spacing; node names encode grid placement. | PARTIAL / medium | Node geometry can be reconstructed only with an independently verified ORBIT node map. Not currently whitelisted. |
| 13 | Site/location | ORBIT grid at Rutgers WINLAB is the verified collection site. | VERIFIED / high | Single site; no site-holdout relation. |
| 14 | Channel/domain labels | Receiver and capture date are explicit. The radio channel is fixed. | VERIFIED / high | Receiver/day are domain axes; `domain_id` must not be a model input. |
| 15 | Task labels | RF fingerprinting target is transmitter identity. | VERIFIED / high | Annotation only. |
| 16 | Filename semantics | Raw-processing regex extracts transmitter, receiver, receive frequency, gain, capture length, and sample rate. | VERIFIED / high | Filenames are target-bearing. |
| 17 | Directory semantics | Released code traverses date/receiver/transmitter-oriented structures and target-specific files. | VERIFIED / high | Target-bearing path components must not define relations. |
| 18 | Annotation storage | Raw/processed indexes and compact pickle dictionaries include transmitter lists next to signal arrays. | VERIFIED / high | Logical separation is absent in legacy artifacts. |
| 19 | Label/acquisition separation | Transmitter labels and acquisition context coexist in official pickle structures and paths. | VERIFIED / high | A new converter must separate them. |
| 20 | Raw format | Raw complex IQ files are processed by the authors' GNU Radio/Python pipeline; compact subsets are Python pickles inside ZIP archives. | VERIFIED / high | Untrusted pickle must never be loaded with unrestricted `pickle.load`. |
| 21 | Total size | Official page: Raw WiSig approximately 1.4 TB; Full WiSig over 70 GB. Compact sets are approximately 1.0--2.5 GB. | VERIFIED / high | Full payload exceeds automatic-download limit. |
| 22 | Licence | Official download page identifies CC BY-NC-SA 4.0 for dataset data. | VERIFIED / high | Research-compatible but restricted. |
| 23 | Redistribution | CC BY-NC-SA permits sharing under attribution, noncommercial, and share-alike conditions. | VERIFIED / medium | Legal/institutional review is still required before redistributing derived payloads. |
| 24 | Derived artifacts | Adaptation is permitted under CC BY-NC-SA conditions. | VERIFIED / medium | Reports/code are separable; signal-derived artifacts inherit obligations requiring review. |
| 25 | Access mechanism | Official UCLA page links Google Drive archives and official GitHub processing/example repositories. | VERIFIED / high | No unofficial mirror is required. |
| 26 | Current availability | Official page, code repositories, and metadata indexes were reachable on 2026-09-02. A Google Drive request returned an interstitial rather than a stable noninteractive payload response. | VERIFIED / medium | Metadata/code access is GO; unattended payload import is deferred. |

## Official sources

- UCLA CORES Lab, [WiSig dataset page](https://cores.ee.ucla.edu/downloads/datasets/wisig/).
- S. Hanna, S. Karunaratne, and D. Cabric, [WiSig: A Large-Scale WiFi Signal Dataset for Receiver and Channel Agnostic RF Fingerprinting](https://doi.org/10.1109/ACCESS.2022.3154790), IEEE Access, 2022.
- Authors' official repositories: `wisig-process-raw`, `wisig-subset-creation`, `wisig-examples`, and `wisig-capture-commands` in the [WiSig GitHub organization](https://github.com/WiSig-dataset).

## Local evidence acquired under the metadata-only limit

The four official repositories and small index files were copied read-only under `/mnt/d/openew_sa_data/paper3/candidate_metadata/wisig/`. The manifest records URL, repository commit, size, retrieval time, and SHA-256. No RF payload was downloaded.
