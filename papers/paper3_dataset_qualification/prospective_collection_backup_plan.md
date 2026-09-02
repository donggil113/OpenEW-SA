# Hardware-Neutral Prospective RF Collection Backup

Public data do not yet authorize a temporal/dynamic experiment. A new collection should therefore be designed independently of the completed target results.

## Mandatory contract

- At least two receivers and two independently revisited sites or campaigns.
- Multiple sessions per receiver/site combination, with target-neutral UUIDs for campaign, session, capture, and sample.
- UTC acquisition timestamps, stated resolution/uncertainty, clock domain, reset ID, and explicit gap semantics.
- Receiver ID, site/campaign ID, center/lower/upper frequency, bandwidth, sample rate, data type, antenna/hardware provenance, and within-capture sample index.
- Opaque raw filenames containing only capture UUID. No class, transmitter, jammer, occupancy, technology, scenario state, or target token in paths.
- Annotations written later to a separate table keyed only by sample UUID.
- Each deployment episode must contain multiple target states by design; labels may audit episode purity but never define episodes.

## Collection tiers

Assumptions for the storage examples: complex int16 IQ, 1 MS/s, one channel, 2 s per capture. Storage values are design estimates, not download commitments.

| Tier | Receivers | Campaigns | Sessions | Captures/session | Captures | Minimum mixed-label sessions | Raw estimate | Recommended disk with compression/features/headroom |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SMALL contract validation | 2 | 2 | 16 | 20 | 640 receiver-captures | 8 | 5.12 GB | about 13.1 GB |
| MEDIUM pilot-ready | 3 | 3 | 36 | 30 | 3,240 receiver-captures | 24 | 25.92 GB | about 66.4 GB |
| FULL domain study | 4 | 4 | 80 | 50 | 16,000 receiver-captures | 64 | 128.0 GB | about 328 GB |

The final acquisition rate/duration must be determined by signal physics and hardware, not these illustrative numbers. Each tier must pass schema, provenance, target-proxy, temporal, and episode QA before model work.

## Structural minimums

For a receiver holdout, at least three receivers are preferred so train/validation/test receiver roles can be distinct. For site/campaign holdout, at least three campaigns are likewise preferred. Each relation type should have >=80% coverage and >=50% membership in repeated groups under the frozen PR #82 gate. At least eight mixed-label sessions are required even for the smallest software qualification; a scientific study should use substantially more.

## Stop rules

Stop collection qualification if clocks cannot be related to reset IDs, if sessions are target-pure by construction, if target labels enter filenames, if capture/session IDs are reused across splits, or if licence/consent prevents derived research artifacts.
