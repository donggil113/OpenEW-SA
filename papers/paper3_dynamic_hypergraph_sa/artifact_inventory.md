# Paper 3 Artifact Inventory

Audit date: 2026-09-01

## Source selection

### VERIFIED FACT

The frozen Paper 1 training configs and the Paper 2 `manifest_build.yaml` all point to the same converted artifacts under `/mnt/d/openew_sa_data/processed/{jamshield,deepsense,electrosense}`. The Paper 2 full manifest contains 170,236 rows, exactly the sum of the three selected metadata tables. Paper 2 per-dataset manifests contain 92,486 JamShield rows, 32,000 DeepSense rows, and 45,750 ElectroSense rows and point back to these processed directories.

Directories under `/mnt/d/openew_sa_data/experiments/*` and `*_v1` contain metrics, predictions, summaries, figures, or manuscript packages. They are experiment outputs, not alternate processed artifact inputs, and were not selected as audit sources.

The audit inspected the following for each dataset:

- `metadata.csv` in full, read with string-preserving semantics;
- `labels.json`, including its ordered `source_files` descriptors;
- `features.npy` in memory-mapped mode for shape and dtype only;
- the local raw-dataset README and source filenames/headers needed to interpret provenance; and
- Paper 1 configs and Paper 2 manifest/split summaries, read-only.

No model predictions or observed holdout performance were used to select relations.

## Common converted schema

All three `metadata.csv` files have 15 columns:

`sample_id`, `dataset_source`, `input_type`, `time_index`, `frequency_band`, `tx_id`, `rx_id`, `modulation_label`, `occupancy_label`, `abnormal_event_label`, `domain_id`, `synthetic_mission_context`, `situation_label`, `threat_level`, and `human_review_required`.

Blank fields remain blank. Symbolic identifiers are read as strings. DeepSense values such as `0000`, `0001`, and `0010` are never cast to integers.

## JamShield

### VERIFIED FACT

- Processed artifact: `/mnt/d/openew_sa_data/processed/jamshield`
- Raw source: `/mnt/d/openew_sa_data/raw/jamshield/JamShield-Dataset-main/JamShield-Dataset-main/data`
- Rows: 92,486
- Feature array: `92,486 x 37`, `float32`
- Source CSVs: 20
- Converted domains/source stems: 20
- Station identifiers: 7, present on 100% of rows
- `time_index`: populated on 100% of rows from the raw `sample` field
- Frequency: constant placeholder `wifi_unknown`
- Recognition target: `abnormal_event_label`

The raw README defines `sample` as a unique sample identifier and `station` as the MAC address of the station transmitting the data. It does not document an acquisition timestamp. The 20 raw files each represent a particular benign or jammer setting. Within every file, `sample` is the monotonic integer sequence 1 through the file row count. Every file/domain is target-pure in the frozen artifact, and file stems visibly contain tokens such as `benign`, `constant_jammer`, `random_jammer`, or `reactive_jammer`.

The frozen Paper 1 scenario holdout uses three jammer domains plus `data_benign_4`; the reactive-family holdout uses reactive jammer domains plus `data_benign_4`. Paper 2's scenario-domain OOD split likewise derives from `domain_id`. This establishes `domain_id` as legitimate split metadata but not a permissible model relation.

### INFERENCE

Station equality is plausibly available at acquisition time, but the source semantics are endpoint/station identity rather than a verified receiver identity. Two of seven station values occur with only one target in the frozen rows, so station edges require shortcut monitoring and an ablation even though weighted target purity equals the dataset majority baseline (0.676751).

## DeepSense

### VERIFIED FACT

- Processed artifact: `/mnt/d/openew_sa_data/processed/deepsense`
- Raw source selected by config: `/mnt/d/openew_sa_data/raw/deepsense/sdr_wifi`
- Rows: 32,000
- Feature array: `32,000 x 2 x 1,024`, `float32`
- Source captures: 32 `.bin` files, 16 per day
- Windows per source file: 1,000
- Occupancy classes: 16 leading-zero four-bit strings
- Domains: `day1`, `day2`
- Receiver identifiers: one constant value
- Frequency: one constant 20 MHz/four-channel descriptor
- Recognition target: `occupancy_label`

The local source README states that each `.bin` file is one continuous complex time series for one four-channel occupancy combination on one day. The converter uses non-overlapping 1,024-sample windows and stores window order as `time_index`. Filename stems contain both the target occupancy code and the day. All 32 reconstructed source captures are target-pure. `time_index` repeats from 0 to 999 in every file, while `metadata.csv` does not carry a safe capture identifier.

Paper 1 and Paper 2 use `day1` as the retained/training domain and `day2` as the held-out domain. Day is therefore split-only for the intended preserved protocol.

### INFERENCE

Within-file signal order is real, but using it as a temporal graph requires the enclosing capture boundary. That boundary is exactly one target class and its original filename encodes the target. The current artifact therefore cannot support a leakage-safe dynamic sequence for occupancy classification.

## ElectroSense

### VERIFIED FACT

- Processed artifact: `/mnt/d/openew_sa_data/processed/electrosense`
- Raw source: `/mnt/d/openew_sa_data/raw/electrosense`
- Rows: 45,750
- Feature array: `45,750 x 512`, `float32`
- Converted source files: 229; skipped files: 3
- Converted receivers/sensors: 40, present on 100% of rows
- Coarse date-folder values: 19, reconstructable for 100% of rows
- Frequency bands: 125, present on 100% of rows
- Local source-row indices: 0--199 after the configured 200-row cap
- Recognition target: `situation_label` with six technology classes

The local README describes measurements from 47 source sensors, but the selected converted artifact contains 40 receiver IDs after conversion/filtering; Paper 3 uses the converted count. Source descriptors retain sensor ID, coarse date-folder ID, band, technology, row count, and original array shape. The source does not provide an exact timestamp, timezone, time-of-day, or cross-file scan order in the converted artifact.

All 40 receiver groups contain multiple target classes. The 19 date groups also contain multiple target classes. In contrast, all 125 observed `frequency_band` values and all 229 source captures are target-pure. Derived band lower/upper/center values retain near-exact or exact target purity.

Paper 1 uses receiver/sensor holdout (`alcorcon1`, `bcn-L`, and `Geneva` in the reference config). Paper 2 uses a different class-OOD protocol for ElectroSense; Paper 3 relation selection does not use that Paper 2 class holdout or its performance.

### INFERENCE

Receiver equality and coarse date grouping are acquisition-plausible static relations. Sensor names may suggest sites, but no independent coordinates or explicit site entity are present, so a separate location relation is not verified. Row order inside a technology/band file is insufficient to claim a dynamic acquisition sequence.

## UNRESOLVED

- JamShield has no verified timestamp or target-independent session identifier.
- DeepSense has no safe mixed-label capture/session key in the converted metadata.
- ElectroSense date tokens lack year/time-of-day and cross-file ordering semantics.
- No dataset provides a verified cross-sensor clock alignment.
- No transmitter identity is populated in any selected converted artifact.
