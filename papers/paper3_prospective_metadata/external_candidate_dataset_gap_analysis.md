# Official public-data gap analysis

This is reconnaissance only. No dataset was downloaded and no experiment was
started. “Promising” means metadata warrants a future access/licence audit, not
that the dataset is approved.

| Candidate | Official evidence | Context evidence | Gaps / risks | Classification |
|---|---|---|---|---|
| WiSig | [official WiSig organization](https://github.com/WiSig-dataset) and [raw-processing instructions](https://github.com/WiSig-dataset/wisig-process-raw) | four days; folders per receiver; raw archives contain multiple transmitters | packet/capture order, timestamps, sessions, path/target coupling, licence, and task fit need local audit | **PROMISING** for static receiver/day DG; temporal status unresolved |
| ElectroSense historical platform/API | [official project site](https://electrosense.networks.imdea.org/), [API examples](https://github.com/electrosense/api-examples), and [sensor software](https://github.com/electrosense/es-sensor) | sensor information plus raw/aggregated PSD; sensor software can record time, center frequency, and PSD | service is historical; export/licence/privacy, stable session IDs, label linkage, and current availability unresolved | **MAYBE** for prospective re-collection, not current compressed data |
| DeepSense 6G | [official dataset site](https://www.deepsense6g.net/) and [official organization](https://github.com/DeepSense6G) | synchronized multi-modal sensing/communications with scenario/location context | not the same DeepSense spectrum-occupancy dataset or task; receiver/time schema and licences must be scenario-specific | **MAYBE**; task mismatch may dominate |
| UC SmartHome RF fingerprinting | [official project repository](https://github.com/SmartHomePrivacyProject/RadioFingerprinting) | one receiver, five transmitters, three 30 s transmissions each, two days, declared center frequency/bandwidth/sample rate | one receiver; transmitter identity is target; capture folders may be target-separated; timestamps/session semantics not established | **REJECT** for current relational question unless new source audit changes facts |

No official candidate is declared experiment-ready. WiSig is the first access
candidate because receiver/day structure is explicit, but acquisition order and
target-neutral episode semantics must be verified from actual raw artifacts
before any use. ElectroSense is better viewed as a prospective collection
platform pattern than as recovered evidence for the frozen local subset.

**External candidates found: four; experiment-ready candidates: zero.**
