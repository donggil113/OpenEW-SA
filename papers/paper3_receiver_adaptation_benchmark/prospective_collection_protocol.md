# Prospective receiver-calibration collection protocol

Status: **PROPOSED DESIGN; SYNTHETICALLY VALIDATED SOFTWARE CONTRACT**

| Tier | Receivers | Hardware families | Sites | Days |
|---|---:|---:|---:|---:|
| SMALL | 8 | >=3 | 2 | >=1 |
| MEDIUM | 12 | >=3 | 2 | >=2 |
| FULL | 20 | >=4 | 3 | >=2 |

Every receiver needs physically separate CALIBRATION and QUERY sessions. A random split is not an episode. Calibration contains naturally mixed transmitter activity, never label-balanced support. Session/capture IDs are opaque UUIDs.

```text
raw/<campaign_uuid>/<session_uuid>/<capture_uuid>.sigmf-data
raw/<campaign_uuid>/<session_uuid>/<capture_uuid>.sigmf-meta
annotations/annotations.parquet
```

Raw paths must not contain target/class/transmitter/device/jammer/occupancy/technology. Metadata includes receiver/hardware/site/campaign, UTC interval, clock authority/reset, sample counters, frequency, sample rate/format, and quality flags. Labels are later annotations. Calibration/query UUIDs and source namespaces are disjoint; queries never adapt.

Validation rejects non-UTC times, nonpositive duration, duplicate capture/index, invalid counters/format/frequency/rate, missing clock provenance, target-bearing paths, and episode overlap. After separate label join, audit calibration purity, conditional entropy, receiver-target NMI, missingness, and diversity without reconstructing support.

## Operator checklist

- Before: licence/privacy approval, campaign/site UUIDs, hardware/firmware/antenna inventory, disk reserve, checksum plan, UUID filenames.
- Setup: receiver IDs, gain/frequency/rate/format, UTC authority, new reset ID after restart, target-neutral sanity capture.
- Calibration: new session, mixed activity, start/end times and counters, gaps/drops, checksum.
- Query: physically separate session/source namespace, no calibration reuse or class construction, checksum.
- Annotation: separate table; never rename raw files after labels.
- Freeze: schema/episode/proxy/separation/diversity/provenance gates and SHA-256 manifests.

Tooling is READY only when schema, episode, proxy, separation, source disjointness, tier counts/diversity, and provenance pass. Synthetic PASS is software readiness only and authorizes no model training or scientific claim.
