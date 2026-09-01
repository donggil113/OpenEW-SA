# Source metadata evidence register

Status terms in this register are evidentiary: **VERIFIED**, **PARTIALLY
VERIFIED**, **UNRESOLVED**, and **REJECTED**. They do not denote model utility.
Target labels were consulted only to audit leakage.

## JamShield

| Field | Local evidence | Official-source evidence | Confidence | Acquisition meaning | Deployment availability | Eligibility |
|---|---|---|---|---|---|---|
| `station` / `rx_id` | Present in all 20 local CSVs; seven values in the converted artifact | The [official dataset repository](https://github.com/panitsasi/JamShield-Dataset) defines `station` as the station MAC address | VERIFIED | station endpoint identity | plausible at collection/inference | relation-safe structurally, but already tested in PR #81 |
| `sample` | Unique consecutive 1-based counter in every local CSV | Official repository calls it a unique sample identifier; no interval or clock semantics are specified | VERIFIED as identifier; REJECTED as time | per-file row/sample key | unresolved | AUDIT ONLY; `TARGET_NESTED_ORDER` |
| source filename / `domain_id` | Filenames encode benign, jammer family, waveform, power, and LOS/NLOS | Official repository states that each dataset corresponds to a specific jamming type | VERIFIED | collection/scenario label container | not a target-neutral deployment field | FORBIDDEN TARGET PROXY / SPLIT ONLY |
| `attack` | Each local file is attack-pure (all 0 or all 1) | Official repository defines 0 as normal and 1 as attack | VERIFIED | task annotation | available only as ground truth | FORBIDDEN LABEL |
| station statistics | Packet/RSSI/SINR fields present | Official paper/repository describes these as network measurements | VERIFIED | node observations, not relational acquisition metadata | potentially available | outside this metadata-recovery question |
| filesystem mtime | Local filesystem value only | no acquisition-time provenance | REJECTED | system metadata | not scientifically trustworthy | SYSTEM_METADATA_ONLY |

The peer-reviewed provenance is the [IEEE ICC 2025 institutional
record](https://napier-repository.worktribe.com/output/4230965/jamshield-a-machine-learning-detection-system-for-over-the-air-jamming-attacks).
Dataset licensing/redistribution terms remain a human-review item.

## DeepSense SDR Wi-Fi

| Field | Local evidence | Official-source evidence | Confidence | Acquisition meaning | Deployment availability | Eligibility |
|---|---|---|---|---|---|---|
| occupancy code | Four leading binary digits in every filename; retained exactly as a string | The [official DeepSense repository](https://github.com/wineslab/deepsense-spectrum-sensing-datasets) says each file represents one four-channel occupancy combination | VERIFIED | task annotation | unavailable at inference | FORBIDDEN LABEL |
| `day1` / `day2` | Filename token; converted `domain_id` | Official repository states that acquisition occurred on two days with different transmitter orientations | VERIFIED | coarse campaign/domain | available only as campaign metadata | SPLIT ONLY; COARSE_DATE_ONLY |
| receiver | Converted constant `deepsense_receiver` | Official repository documents four transmit USRPs and one receiver at 20 MS/s | VERIFIED | one receiver | plausible | no relational variation; UNRESOLVED for relations |
| source capture | 32 headerless complex64 `.bin` streams | Official repository documents 32 files and its NumPy complex64 reader | VERIFIED | occupancy/day capture container | identifier is target-bearing | FORBIDDEN TARGET PROXY |
| within-file order | Converter creates sequential windows; raw samples are ordered | No timestamp, gap, session-reset, or cross-file synchronization semantics are provided | PARTIALLY VERIFIED | order within a target-pure capture | not sufficient | TARGET_NESTED_ORDER |
| channel/band | Converted descriptor `wifi_20mhz_4ch` | Official source documents four 5 MHz channels spanning 20 MHz | VERIFIED only at dataset level | fixed layout, not per-sample channel identity | unresolved | UNRESOLVED |
| filesystem mtime | Local filesystem value only | no acquisition-time provenance | REJECTED | system metadata | no | SYSTEM_METADATA_ONLY |

The ten local LTE HDF5 files are official simulated train/test products at
several SNRs. They add no receiver, site, physical session, or acquisition-time
context; train/test and SNR filename tokens are generator conditions, not
prospective deployment metadata.

## ElectroSense PSD technology subset

| Field | Local evidence | Official-source evidence | Confidence | Acquisition meaning | Deployment availability | Eligibility |
|---|---|---|---|---|---|---|
| sensor / `rx_id` | Sensor folder token; 40 values in the local subset | The [official framework repository](https://github.com/electrosense/PSD-technology-classification-framework) describes measurements from 47 European sensors | VERIFIED | sensing endpoint/site token | plausible | structurally relation-safe, already tested in PR #81 |
| `source_date_id` | 19 path date tokens, 45 receiver-date groups | Official example API uses sensor, month, and day parameters; no local within-day time survives | PARTIALLY VERIFIED | coarse date grouping | plausible but coarse | UNRESOLVED for a new experiment; COARSE_DATE_ONLY |
| technology token | Embedded in every local NPY filename; each file target-pure | Official framework is a technology-classification dataset | VERIFIED | task annotation/container | unavailable at inference | FORBIDDEN TARGET PROXY |
| frequency bounds | Filename tokens; 41 files contain inconsistent first/last frequency pairs | Official framework classifies transmissions using PSD over bands; the historical [sensor software](https://github.com/electrosense/es-sensor) can record time, center frequency, and PSD | PARTIALLY VERIFIED locally | physical spectrum bounds upstream | potentially available prospectively | FORBIDDEN in current frozen subset because band is technology-associated |
| array row order | Plain 2-D NPY arrays expose shape/dtype only | Official framework does not establish per-row timestamp or gap semantics for these compressed files | UNRESOLVED | row order in target-pure container | unresolved | TARGET_NESTED_ORDER |
| site/location | Sensor token may identify a named site | Official network is geographically distributed, but exact privacy-safe location metadata is absent locally | PARTIALLY VERIFIED | sensing site | plausible prospectively | UNRESOLVED |
| filesystem mtime | Local filesystem value only | no acquisition-time provenance | REJECTED | system metadata | no | SYSTEM_METADATA_ONLY |

The compressed dataset's official DOI is
[10.5281/zenodo.7521246](https://zenodo.org/record/7521246). The local subset
contains DAB, DVB-T, FM, GSM, LTE, and TETRA files; this is an observation about
the local frozen subset, not a claim that the Zenodo record defines exactly
those six classes. The upstream framework also documents an `unkn` state; no
local filename with that token was found.

## Cross-source conclusion

**VERIFIED:** no local raw container exposes a newly recovered, target-neutral
timestamp plus session/reset semantics. Existing station/receiver/date fields
are not new evidence; they were the inputs to the completed PR #81 NO-GO pilot.

**UNRESOLVED:** dataset owners may possess non-public acquisition logs that were
not included locally. Such logs would require hash-linked provenance and a new
audit before use.

