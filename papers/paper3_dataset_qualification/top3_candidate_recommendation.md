# Top-Three Candidate Recommendation

Ranking uses metadata readiness, licence/access clarity, task fit, relation diversity, temporal evidence, manageable import size, and reproducibility. It does not use predictive performance.

## 1. WiSig — CONDITIONAL GO

WiSig is the best candidate for a **static receiver-context** Paper 3. It has the strongest task continuity with RF signal recognition, 41 independently identified receivers, four acquisition days, official code, and bounded compact subsets. Aggregate metadata shows receiver groups are not close transmitter proxies. Its limitations are decisive: temporal order is target-nested, only one relation type passes, the licence is noncommercial/share-alike, and no sample-level converted artifact or frozen split exists.

## 2. OPERAnet — CONDITIONAL GO for metadata qualification, not adoption

OPERAnet has the strongest verified acquisition-time structure: millisecond timestamps, experiment boundaries, multiple RF receivers/channels, room context, and synchronized modalities. It could support a genuinely temporal context study after strict acquisition/annotation separation. It ranks second because the task is human activity/localization rather than spectrum situation assessment, annotation columns coexist with acquisition columns, and item-level licence/size review is incomplete.

## 3. OSU LoRa RFFP — CONDITIONAL GO

OSU LoRa has excellent RF-fingerprinting task fit and plain metadata sidecars with sample rate, time/day, and carrier frequency. It includes day/location/configuration/receiver setups. It ranks below WiSig because most files are target-specific, only two receivers appear in the receiver setup, the collection is over 1.2 TB, and the release note does not state clear redistribution/derived-artifact terms.

## Candidates not selected

- **Antwerp LPWAN localization:** timestamps and base-station IDs are promising and the files are manageable, but the task is localization from RSSI rather than raw-RF recognition; active-version licence and episode semantics remain unresolved.
- **POWDER Data Commons:** highly relevant spectrum context, but the portal combines heterogeneous datasets with item-specific schemas/licences. No single item passed all gates.
- **Oxford Radar RobotCar/RADIATE:** excellent temporal provenance, but automotive radar perception is too far from the intended RF situation task.
- **Widar3.0, XRF55, MM-Fi:** multiple RF views but target-pure action clips, target-bearing paths, unclear licences, and human-sensing task mismatch.
- **UAVSig:** relevant task but receiver/session/time structure, size, and licence were not sufficiently verified; released IQ has random dropped segments.
- **ORACLE, RadioML:** no adequate multi-receiver/session context.

## Decision

**TOP CANDIDATE: WiSig.** The next action is a human-approved, official ManyRx compact-subset import followed by conversion, sample-level proxy audit, and split preregistration. No model experiment is authorized by this ranking.
