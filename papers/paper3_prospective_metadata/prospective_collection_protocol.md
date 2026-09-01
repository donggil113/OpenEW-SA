# Prospective RF collection protocol

## Required recording granularity

Record one acquisition row per model-addressable sample/window, plus stable links
to its raw capture and source-record range. Receiver/site/hardware/frequency
configuration is recorded at every change point and materialized per row during
conversion with provenance. Timestamps must include source, resolution,
uncertainty, clock domain, and reset identity.

## Session lifecycle

A session opens when an operator starts a target-neutral acquisition interval
under one declared clock domain and operational configuration. It closes on
operator stop, receiver reboot, clock discontinuity, hardware/antenna change,
site change, campaign boundary, or a documented maximum idle gap. Clock
resynchronization, backward time jump, reboot, or loss of time authority creates
a new `clock_reset_id`; it need not create a new session if the discontinuity is
explicit and downstream temporal builders segment at the reset.

The open/close rules are decided before semantic target labels are known. A
session is never opened because “the jammer started” or “class changed.” Such
events belong to annotations.

## Identity and privacy

- `receiver_id`, `station_id`, `sensor_id`, and `site_id` are opaque registry
  keys, not descriptive names.
- Hardware serials are stored only as salted hashes under controlled key/salt
  governance.
- Locations use a declared precision class; public releases default to site or
  region tokens, not coordinates.
- Campaign and operational-context tokens are opaque and proxy-audited.

## Frequency and clock metadata

Record center/lower/upper frequency, bandwidth, sample rate, channel ID, tuning
source, and configuration-change boundaries. Record UTC when trustworthy; also
retain device-clock domain/reset semantics. Missing or uncertain values are
explicit in `metadata_missing_mask` and `metadata_quality_flags`, never encoded
as 0 or an invented time.

## Annotation protocol

Labels are captured in a separate annotation system and joined only by
`sample_id`/capture time range. Record annotator/instrument, task definition,
annotation time, adjudication status, and uncertainty. Labels may be assigned
after collection. Acquisition services must not receive the label when naming
files, sessions, campaigns, or receiver/site records.

## Filename and directory policy

Normative target-neutral structure:

```text
raw/
  <campaign_uuid>/
    <session_uuid>/
      <capture_uuid>.bin
      <capture_uuid>.metadata.json
annotations/
  labels.parquet
```

Raw filename: opaque capture UUID only. Do not use class, jammer type,
occupancy, technology, scenario target state, attack/benign, OOD/ID, correctness,
or split membership in a folder or filename. Validation rejects known target
tokens and project-specific deny-list tokens.

## Operational QA before release

Run schema/provenance validation continuously, but run target-proxy diagnostics
only in a separate controlled process once annotations exist. Freeze original
capture hashes, preserve corrections as transformations, and quarantine—not
silently drop—invalid rows. A collection is not dynamic-ready merely because
timestamps parse; it must pass session/reset/gap/mixed-target episode criteria.
