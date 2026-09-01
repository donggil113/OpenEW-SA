# Retrospective metadata recovery report

## Decision summary

| Dataset | Was useful label-independent acquisition metadata lost in conversion? | Rationale |
|---|---|---|
| JamShield | **NO** | The raw CSV adds the per-file `sample` counter and target-bearing filenames; station identity was already retained and tested. No timestamp/session/channel log was found. |
| DeepSense | **NO** | The raw binaries are headerless complex64 streams partitioned by occupancy/day. Window order is target-nested; no timestamp/session reset or varying receiver exists. |
| ElectroSense | **PARTIAL, but not experiment-enabling** | Coarse sensor/date/frequency/path facts exist upstream. Sensor/date were already recovered and tested; frequency/path are target proxies in this subset, and no valid within-day timing survives. |

**Can existing local raw data support a new relational experiment without
violating the completed NO-GO protocol? NO.** No newly verified relation was
recovered. Reusing or selecting a subset of station/receiver/date relations
after observing PR #81 target results would be target-visible optimization.

**Can existing local data support genuine temporal/dynamic modeling? NO.** The
temporal audit found zero `VALID_TEMPORAL_CONTEXT` fields. Coarse days, local
row counters, and target-pure file order do not establish dynamics.

## What was inspected

- 20 JamShield CSVs: 92,486 raw rows; every file target-pure; every `sample`
  counter consecutive from one.
- 32 DeepSense SDR binaries: occupancy/day target-bearing names; complex64
  lengths consistent with approximately 8.008 s (day1) and 5.005 s (day2) at
  the documented 20 MS/s.
- 10 local DeepSense simulated-LTE HDF5 train/test files: generator products,
  not physical acquisition sessions.
- 232 ElectroSense NPY files: 40 sensor tokens, 19 date tokens, six observed
  technologies, and no NPY attribute/header channel for timestamps.

Detailed machine-readable evidence is in
`/mnt/d/openew_sa_data/paper3/source_forensics/raw_metadata_forensics.json`.

## Newly recovered facts

No newly recovered field meets `RELATION_ALLOWED` for a new current-data
experiment. ElectroSense's upstream collection system was capable of recording
time/frequency/sensor context, but those fields were not retained with adequate
semantics in the local compressed subset. That observation motivates converter
v2 and prospective collection; it does not authorize retroactive reconstruction.

## Rejected reinterpretations

- filesystem mtime as acquisition time;
- JamShield `sample` as a global clock;
- DeepSense day1/day2 as a dynamic sequence;
- DeepSense within-file windows as mixed-state deployment episodes;
- ElectroSense NPY row number as verified acquisition time;
- target-bearing filenames as session IDs;
- ElectroSense frequency as a current relation;
- selecting ElectroSense receiver-only relations from PR #81 ablation results.

## Human follow-up

Only separately obtained owner logs can change this decision. Any log must be
linked to raw captures by cryptographic hash or stable capture UUID and must
document timestamp, clock, session, receiver/site, and annotation provenance.
The evidence must be audited before target performance is available.

