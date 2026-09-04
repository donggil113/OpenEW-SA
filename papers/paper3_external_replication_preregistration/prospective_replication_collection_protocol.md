# Prospective receiver-calibration replication collection protocol

Status: **CONCRETE DESIGN; DATA NOT YET COLLECTED; TRAINING NOT AUTHORIZED**

## Collection objective

Create an independent RF-transmitter fingerprinting dataset in which receiver
calibration is a real acquisition event rather than a partition of a test
batch. The design is hardware-agnostic: no specific SDR is assumed to be owned.

## Minimum confirmatory design

| Element | Frozen minimum |
|---|---:|
| Physical receiver units | 12 |
| Receiver hardware families | 2 preferred; at least 4 units per represented family for family-level description |
| Transmitter devices | 12 physical units; preferably the same radio/model family or a documented balanced mix |
| Sites | 2 operationally distinct sites, or one site in two independently opened campaigns if a second site is infeasible |
| Campaigns | 2, opened on separate acquisition occasions |
| Calibration episodes | 1 per receiver per campaign |
| Query episodes | 1 separate episode per receiver per campaign |
| Valid calibration packets | at least 768 per receiver/campaign before the label-free 128-packet selection |
| Valid query packets | at least 200 per transmitter/receiver/campaign |
| Raw burst extent | at least 4,096 complex samples per retained packet before deterministic 256-sample conversion |

The numbers are structural coverage requirements, not a predictive effect-size
or power claim. If procurement limits the first engineering capture to fewer
receivers, that capture validates acquisition and conversion only and cannot be
used as the confirmatory replication.

## Target-neutral acquisition workflow

1. Register receiver, site, antenna, clock, firmware, and RF configuration in
   an acquisition registry using opaque UUIDs.
2. Open a calibration episode before any query episode. The operator records an
   operational `episode_role=calibration`; no transmitter/class token enters
   the filename, directory, sample ID, or acquisition metadata.
3. A controller schedules packets from the transmitter set in a randomized
   round-robin order. The controller writes an opaque transmission-event UUID.
   Its private annotation log maps that UUID to transmitter identity; the RF
   recorder never receives the identity.
4. Close calibration on an operator stop, clock reset, receiver reboot,
   hardware/antenna/configuration change, or the predeclared duration/packet
   quota—not on a class transition.
5. Start a new capture and query episode after a documented separation. Query
   packets use a separately randomized schedule and cannot reuse raw records
   from calibration.
6. Repeat the procedure for every receiver and campaign. Do not rename files
   after annotation.

The calibration traffic is deliberately mixed to exercise receiver context.
The benchmark controller may ensure collection coverage, but the actual
128-packet support bank is selected later by opaque hash without labels.

## File and metadata layout

```text
raw/
  <campaign_uuid>/
    <receiver_uuid>/
      <session_uuid>/
        <capture_uuid>.sigmf-data
        <capture_uuid>.sigmf-meta
annotations/
  transmitter_events.parquet
manifests/
  raw_sha256sums.txt
  acquisition_registry.json
```

No class-, transmitter-, protocol-state-, site-name-, scenario-, split-, or
outcome-named folder is allowed. The acquisition table follows OpenEW-SA schema
v1.0.0 and adds controlled `episode_role`, `calibration_episode_id`, and
`query_episode_id` fields as split-only metadata. The annotation table contains
`sample_id`, `task_name`, `transmitter_id`, `annotation_source`, and annotation
provenance. Relation/support code must run with the annotation object absent.

## RF settings and synchronization

Use one documented center frequency, bandwidth, sample rate, gain policy,
antenna configuration, and frame waveform within the primary study. Record any
change at its exact capture boundary. Record UTC source, resolution,
uncertainty, clock domain, and reset ID. Time is provenance only; P2 receives no
temporal feature.

Packet detection, synchronization, optional filtering/resampling, and the
256-complex-sample crop are fixed from the waveform specification and a
label-blind engineering capture. They are validated in two deterministic
conversion passes before annotation-based proxy auditing.

## Storage estimate

At 4,096 complex int16 I/Q samples per retained packet (4 bytes per complex
sample), one receiver/campaign with 768 calibration packets and
`12 x 200 = 2,400` query packets requires about 49.5 MiB of retained packet
payload. Twelve receivers across two campaigns require about 1.16 GiB before
container, metadata, failed-capture, and continuous-recording overhead.

Reserve at least 10 GiB for raw captures, two converted passes, QA quarantine,
manifests, and future checkpoints. If continuous captures are retained instead
of packet-triggered bursts, recompute the budget from sample rate, duration, and
sample format before collection; do not silently discard raw data to fit disk.

## Pre-collection dry run

Use synthetic or lab-loopback signals only to validate IDs, clocks, episode
open/close events, annotation isolation, target-neutral paths, capture hashes,
and converter determinism. Do not report classifier accuracy from the dry run.

## Pre-training release gate

After collection, freeze raw hashes and perform full schema, duplicate,
nonfinite, receiver/hardware, calibration/query overlap, target-token, support-
label invariance, target-proxy, class-support, and two-pass conversion audits.
Then freeze LOSO splits and the exact method/statistics manifests in a clean
commit. Training remains prohibited until that review is complete.
