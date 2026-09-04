# Candidate dataset qualification matrix

Status: **OFFICIAL-SOURCE QUALIFICATION; NO PAYLOAD DOWNLOAD; NO TRAINING**

Evidence was checked on 2026-09-05 against official dataset pages,
institutional repositories, author repositories, and primary data-descriptor
papers. `UNKNOWN` is retained where an official source does not establish a
field. A candidate is not promoted merely because a converter might reconstruct
a convenient grouping.

## Decision matrix

| Candidate | Independent of WiSig | Physical receiver evidence | Acquisition-designed calibration/query episodes | RF/task compatibility with frozen 256-IQ transmitter classifier | Annotation/path separation | Licence/access | Verdict for this replication |
|---|---|---|---|---|---|---|---|
| WiSig ManyRx | **No** | 41 reported; 32 in V2 LOSO | No; V2 support/query was a deterministic split, not an acquired calibration protocol | Yes | Cleaned by the V2 converter, but raw paths are target-bearing | CC BY-NC-SA 4.0; official access | **REJECT: not independent and no acquired calibration episode** |
| OSU Bluetooth RFFP (2025) | Yes | Two Ettus B210 receivers in the across-receiver scenario | No explicit calibration/query episodes; data for each of 31 devices were collected in two-minute device-specific runs | Raw IQ exists; released frames have 1,850 complex samples and transmitter-ID task | Example release uses `X_*.npy` and `Y_*.npy`; acquisition/annotation separation and target-neutral source names are not established | Institutional download; citation request verified, standard payload licence unresolved | **NO-GO AS RELEASED** |
| OSU LoRa RFFP, different receivers | Yes | Two B210 receivers | No target-neutral calibration episode; official directories/files are per device and therefore target-bearing | Raw IQ, transmitter-ID task; deterministic 256-sample transfer could be engineered only after an independent conversion freeze | Device identity is present in paths and SigMF pairs | Research use/citation statement; redistribution terms unresolved; collection exceeds 1.2 TB | **NO-GO AS RELEASED** |
| POWDER RF Fingerprinting (2020) | Yes | One fixed B210 endpoint receiver; four base stations are transmitter classes | Five recording sets on two days, but no multiple receiver-calibration protocol | Raw IQ and emitter-ID task | Filename encodes waveform, day, transmitting base station, and set | Official GENESYS/POWDER access; page requests citation; item licence not verified | **REJECT: single receiver** |
| WIDEFT | Yes | Official record does not establish multiple physical receivers | No receiver-calibration or acquisition-disjoint support/query protocol found | RF bursts and device-ID task; mixed signal families; exact 256-IQ preprocessing not established | Corpus is organized by device/capture; separate target-neutral acquisition table not verified | Official Zenodo record, 2.1 GB archive; licence field not verified in the inspected record | **NO-GO: receiver and episode evidence absent** |
| INRIA PLA-AP I/Q dataset (2026) | Yes | One BladeRF AX4 receiver reported | Device-specific burst files; no multi-receiver calibration protocol | Complex IQ and device authentication task; preprocessing differs | Raw tree is organized by device ID | Official Zenodo/GitHub access; record exposes no usable licence value in the inspected rights field | **REJECT: single receiver and target-bearing organization** |
| OPERAnet | Yes | Two Wi-Fi CSI receivers; PWR has three surveillance channels; UWB has multiple nodes | Experiment IDs and millisecond timestamps exist, but there is no dedicated receiver-calibration/query acquisition for transmitter identification | Incompatible task and representation: human activity/localization using CSI, spectrograms, CIR, and vision rather than 256-IQ transmitter fingerprints | Activity/person/location columns coexist with acquisition columns and require separation | Official Figshare items; `wificsi1` is CC0; large modular downloads | **REJECT FOR THIS REPLICATION; useful only for a different sensing study** |
| Antwerp LPWAN localization | Yes | Multiple receiving base-station IDs | Message receive times exist, but calibration/query receiver episodes are not defined | RSSI/network localization, not raw-IQ transmitter fingerprinting | GPS location target is co-stored with network measurements | Official Zenodo access; active-version licence requires recheck | **REJECT FOR EXACT METHOD TRANSFER** |
| NIST mmWave COTS UE fingerprint data | Yes | Official catalog describes a repeatable test bed but does not establish multiple receiver units | No receiver-calibration episode schema in the released figure data/README | UE model fingerprinting from constellation/spectrum features, not a 256-IQ packet corpus | Insufficient released sample-level schema for this contract | Public NIST record and NIST open licence | **NO-GO: receiver/episode/input evidence insufficient** |
| AERPAW AADM multimodal measurements | Yes | Multiple base stations, but the UAV/gateway receive-chain records do not establish the required set of physical fingerprinting receivers | Flight/challenge runs exist; not a receiver-calibration design | Wireless link/telemetry task rather than transmitter RF fingerprinting with the frozen input | Task and telemetry schema require a separate study | Official Dryad record | **REJECT FOR THIS REPLICATION** |

## Official evidence anchors

- WiSig: [UCLA CORES dataset page](https://cores.ee.ucla.edu/downloads/datasets/wisig/) and DOI [`10.1109/ACCESS.2022.3154790`](https://doi.org/10.1109/ACCESS.2022.3154790).
- OSU Bluetooth: [official 2025 release note](https://research.engr.oregonstate.edu/hamdaoui/sites/research.engr.oregonstate.edu.hamdaoui/files/release_note_datasets_ble_august2025_v1.pdf). It states 31 transmitters, two B210 receivers, six-minute warm-up, two-minute device collection, 6 MS/s, and 1,850 complex samples per extracted frame.
- OSU LoRa: [official dataset hub](https://research.engr.oregonstate.edu/hamdaoui/datasets) and [official release note](https://research.engr.oregonstate.edu/hamdaoui/sites/research.engr.oregonstate.edu.hamdaoui/files/release_note_lora_datasets_final_oct2023_v2.pdf).
- POWDER RFF: [official GENESYS dataset page](https://genesys-lab.org/powder) and [POWDER Data Commons](https://powderwireless.net/data). The official description specifies one fixed B210 receiver, four X310 transmitter sites, five two-second sets, and two days.
- WIDEFT: [official Zenodo record](https://doi.org/10.5281/zenodo.4116383) and the [author-hosted paper](https://phillip-deleon.com/wp-content/uploads/Research/Publications/HST_2021.pdf).
- INRIA PLA-AP: [official Zenodo record](https://doi.org/10.5281/zenodo.18268648) and [official project repository](https://github.com/mlsysops-eu/model-physical-layer-authentication).
- OPERAnet: [Scientific Data descriptor](https://doi.org/10.1038/s41597-022-01573-2), [official Figshare collection](https://doi.org/10.6084/m9.figshare.c.5551209.v1), and [`wificsi1` item](https://figshare.com/articles/dataset/wificsi1/16578428).
- Antwerp LPWAN: [official Zenodo record](https://doi.org/10.5281/zenodo.3342253).
- NIST mmWave UE RFF: [official NIST catalog record](https://data.nist.gov/od/id/mds2-3742).
- AERPAW AADM: [official Dryad record](https://doi.org/10.5061/dryad.7d7wm3898).

## Qualification conclusion

No candidate is suitable for conversion under the present replication
contract. OSU Bluetooth is the closest task-compatible independent release,
but two receiver units cannot support the preregistered receiver-level
confirmatory analysis and its device-specific collection runs are not
target-neutral receiver-calibration episodes. OPERAnet has the strongest
session/time evidence, but it would change both the task and the model input and
therefore would not replicate the frozen P0/T3A/P2 question.

No payload was downloaded. No converter was implemented because that would
imply a candidate passed gates it did not pass.

## Evidence limitations and follow-up

The conclusion is bounded to the official releases inspected. An author-provided
sidecar could change a candidate only if it independently establishes physical
receiver IDs, target-neutral calibration/query episode boundaries, source-file
disjointness, and licence terms. It cannot retroactively make a target-specific
capture into a target-neutral calibration episode.
