# Shen multi-receiver LoRa official-evidence matrix

Status: **QUALIFICATION FROZEN BEFORE PAYLOAD ACCESS OR MODEL RESULTS**

## Primary sources and immutable local evidence

1. G. Shen, J. Zhang, A. Marshall, R. Woods, A. Cavallaro, and L. Chen,
   “Towards Receiver-Agnostic and Collaborative Radio Frequency Fingerprint
   Identification,” *IEEE Transactions on Mobile Computing*, vol. 23, no. 7,
   pp. 7618--7634, July 2024, DOI `10.1109/TMC.2023.3340039`. The accepted
   manuscript was obtained from the University of Liverpool repository record
   `https://livrepository.liverpool.ac.uk/3176924/`; local SHA-256
   `ef594aac7d0dd8bd8cecb50a4162c7e4b44790ea24f3bd1ffbe5e917022c30d8`.
2. Official author repository `https://github.com/gxhen/receiverAgnosticRFFI`,
   inspected at commit `ffad4828c267324fc514a5a729aac93a9b6ff556`.
3. IEEE DataPort DOI `10.21227/D6VX-R538`, whose DataCite record identifies
   “Radio Frequency Fingerprint LoRa Dataset With Multiple Receivers,” Shen,
   Zhang, and Marshall, IEEE DataPort, 2024.
4. Author-maintained dataset index `https://junqing-zhang.github.io/dataset-code/`.

`VERIFIED` means two compatible primary-source statements or one direct
machine-readable/source-code observation. `PARTIALLY VERIFIED` identifies a
bounded primary-source claim that cannot yet be reconciled against payload.
Unknowns fail closed.

| Requirement | Primary-source evidence | Status | Notes |
|---|---|---|---|
| Canonical dataset name | DataCite/DataPort title above | VERIFIED | DOI `10.21227/D6VX-R538` |
| Authors | Shen, Zhang, Marshall in DataCite; six paper authors above | VERIFIED | Dataset and paper author lists differ appropriately |
| Venue/year | IEEE TMC 23(7), 2024; online DOI year 2023 | VERIFIED | Paper DOI above |
| Transmitter count | Ten LoRa devices | VERIFIED | Five Pycom LoPy4 and five mbed SX1261 devices |
| Physical receiver count | Twenty SDR receivers | VERIFIED | Separate receiver files are enumerated in official code |
| Receiver hardware families | Six models | VERIFIED | 9 RTL-SDR, 2 ADALM-PLUTO, 2 USRP B200, 2 B200mini, 2 B210, 3 N210 |
| Receiver IDs | `rtl_1`--`rtl_9`, `pluto_1`--`pluto_2`, `b200_1`--`b200_2`, `b200mini_1`--`b200mini_2`, `b210_1`--`b210_2`, `n210_1`--`n210_3` | VERIFIED | Split/audit identity; never embedded |
| Transmitter hardware | Five LoPy4; five SX1261 | VERIFIED | Transmitter identity is the target annotation |
| Collection environment | Typical residential room, line of sight, approximately 1 m, fixed locations, SNR above 50 dB | VERIFIED | Paper experimental setup |
| Sites/days/campaigns | The official code contains `Location_A_*` test paths and commented `drift/*_day1`--`day4` paths for selected receivers | PARTIALLY VERIFIED | These path tokens establish that the authors contemplated location/day variants, but not that those files are in the canonical payload, nor their acquisition semantics or completeness; filesystem times remain inadmissible |
| Capture/session identifiers | Receiver train/test containers exist; no target-neutral acquisition-session semantics documented | PARTIALLY VERIFIED | File role is not an acquired calibration episode |
| Packets per transmitter/receiver | 800 training and 100 testing packets per device-receiver pair are reported/used | VERIFIED | 200 device-receiver pairs |
| Packet count | At least the reported 10 x 20 x (800 + 100) experiment subset | PARTIALLY VERIFIED | Exact payload rows require access and reconciliation |
| Sample format | HDF5 keys `data`, `label`, `SNR`, `CFO`; complex signal reconstructed from real/imaginary halves | VERIFIED | Exact row length and dtype require payload inspection |
| Raw I/Q availability | Complex-valued packet samples are reconstructed by official loader | PARTIALLY VERIFIED | Exact frozen 256-IQ conversion remains unverified without payload |
| Sample rate | 1 MHz for all receivers | VERIFIED | Paper experimental setup |
| Center frequency | 868.1 MHz | VERIFIED | Paper experimental setup |
| LoRa bandwidth / SF | 125 kHz / SF7 | VERIFIED | Paper experimental setup |
| Signal preprocessing | Paper uses channel-independent spectrogram, window 128 and overlap 64 | VERIFIED | Frozen P0/T3A/P2 require IQ, not spectrogram transfer |
| Target label | Physical transmitter/device identity | VERIFIED | Annotation-only |
| Filename semantics | Receiver identity and train/test role encoded in HDF5 filenames | VERIFIED | Receiver tokens are target-neutral; target rows are selected through `label` |
| Directory semantics | `Train/` and `Test/` acquisition roles; no class-named directories shown by official code | VERIFIED | Exact payload tree still uninspected |
| Paths encode target | Official loader path strings encode receiver/role, not transmitter | PARTIALLY VERIFIED | Must be confirmed across archive before conversion |
| Receiver identity explicit | Explicit in enumerated receiver filenames and loader mapping | VERIFIED | Physical-unit provenance is paper-supported |
| Timestamps | No timestamp key or timestamp semantics documented | REJECTED | Filesystem mtime is system metadata only |
| Packet order | Array order exists but official loader selects per-device indices | VERIFIED | Target-nested order; not temporal context |
| Acquired calibration episodes | No target-neutral calibration episode with open/close semantics is documented | REJECTED | Official fine-tuning uses labeled target packets |
| Receiver synchronization | No synchronization claim found | UNKNOWN | No temporal claim permitted |
| Licence | DataCite rights says CC BY 4.0; author repository says CC BY-NC-SA 4.0 | UNKNOWN | Conflicting official metadata; fail closed |
| Redistribution/derivatives | Cannot be resolved while licence conflict remains | UNKNOWN | No RF payload or derived release authorized |
| Access | Author links to `pan.seu.edu.cn`; host did not resolve during audit | PARTIALLY VERIFIED | DataPort landing page is official but automated payload access unavailable |
| Payload size | No size in DataCite record | UNKNOWN | A non-primary report says 27.67 GB; not used as verified fact |
| Official checksums | None located | UNKNOWN | Would be generated locally after lawful acquisition |

The location/drift path evidence is deliberately bounded. It does not establish
a target-neutral session, a timestamped sequence, a complete day-by-receiver
crossing, or current payload availability. Consequently it does not reopen the
acquired-calibration or temporal gates.

## Qualification conclusion

**VERIFIED DATA FACT:** the dataset is an independent, real, ten-transmitter,
twenty-receiver LoRa corpus with unusually strong receiver-hardware diversity.

**UNRESOLVED:** licence terms conflict across official sources, the currently
linked author download host is unavailable from the audit environment, and the
exact payload schema/shape cannot be reconciled without lawful access.

**GATE RESULT:** Q0 provenance/licence and payload-access gates do not pass.
No payload download, conversion, smoke training, blinded benchmark run, or
target metric is authorized by this audit.
