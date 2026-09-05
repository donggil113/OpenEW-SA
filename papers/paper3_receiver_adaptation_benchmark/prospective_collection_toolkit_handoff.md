# Prospective receiver-calibration toolkit handoff

Status: **SOFTWARE READY; NO REAL COLLECTION EVIDENCE**

The toolkit creates target-neutral SigMF-style capture trees, validates acquisition/session metadata, keeps annotations separate, verifies physically distinct calibration/query namespaces, checks receiver/hardware/site/day minima, and estimates storage. SMALL, MEDIUM, and FULL synthetic dry runs all pass their software gates.

| Tier | Receivers | Hardware families | Sites | Days | Example raw | Converted | Minimum reserve | Capture time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SMALL | 8 | 3 | 2 | 1 | 7.68 GB | 2.304 GB | 15.216 GB | 0.533 h |
| MEDIUM | 12 | 3 | 2 | 2 | 23.04 GB | 6.912 GB | 45.288 GB | 1.600 h |
| FULL | 20 | 4 | 3 | 2 | 57.60 GB | 17.280 GB | 112.920 GB | 4.000 h |

The illustrative estimate assumes complex int16, 1 MS/s, 60 seconds per capture, two sessions per receiver, one capture per session at every listed site/day, and ten transmitters. It is a planning scenario, not a measurement.

## Operator checklist

### Before campaign

- Freeze licence, consent/privacy, sites, campaign UUIDs, hardware/firmware/antenna inventory, frequency/rate/format, clock authority, disk reserve, and checksum plan.
- Use opaque UUID filenames only. Never include class, transmitter, technology, jammer, occupancy, or target state.
- Prepare a separate annotation table and role-specific source namespaces.

### Receiver setup

- Verify receiver ID, hardware ID/family, gain, antenna, center frequency, sample rate, sample format, UTC authority, clock-reset ID, and sample counter.
- Start a new reset ID after clock/device restart.
- Make a target-neutral QA capture and checksum it.

### Calibration

- Open a dedicated CALIBRATION session UUID.
- Record naturally mixed transmitter activity; do not class-balance by labels.
- Record explicit start/end UTC, counters, gaps/drops, site/campaign/day, and provenance.
- Freeze the source namespace and checksum.

### Query

- Open a physically separate QUERY session and source namespace.
- Do not copy or random-split calibration records.
- Do not expose query samples to adaptation.
- Freeze the checksum.

### Annotation and end-of-day freeze

- Add labels only to the separate annotation table; never rename raw paths.
- Validate schema, episode boundaries, path neutrality, source disjointness, proxy risk, diversity, and provenance.
- Hash the raw tree and reports before transport/upload.

A synthetic PASS means the implementation behaves correctly. It does not authorize scientific training, prove proxy safety in real data, or establish a receiver-calibration effect.
