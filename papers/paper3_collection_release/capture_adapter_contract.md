# External SDR adapter and metadata contract

## Boundary

The SDR-specific adapter owns device control, gain, streaming, dropped-sample detection and clock measurements. It must finish and close a local payload before calling capture-register. It supplies byte count, sample counter and UTC acquisition start from documented acquisition semantics—not filesystem mtime. Keep the source file stable until registration succeeds. The runtime copies it to a new opaque destination and checks size, SHA256 and SigMF SHA512.

Supported formats: ci8 (2 bytes/complex), ci16_le (4), cf32_le (8), cf64_le (16). One complex channel per registered capture. Multi-channel adapters must separate channels with explicit receiver/channel provenance before use; do not reshape silently. A capture cannot span a UTC day boundary.

## Tables/objects

| Object | Required acquisition-only fields |
|---|---|
| Campaign | campaign_uuid, site_id, start_utc, operator pseudonym, schema_version, approved_receivers, frequency_hz, sample_rate_hz, task, annotation_policy=SEPARATE, synthetic |
| Receiver | receiver_uuid, manufacturer, model, serial_hash, firmware, driver, antenna, host pseudonym, clock_source; optional notes |
| Session | session_uuid, receiver_uuid, campaign_uuid, CALIBRATION or QUERY role, start_utc, clock_reset_id, sample_counter_start; close adds end_utc, counter_end, capture list |
| Capture registration | capture_uuid, session_uuid, receiver_uuid, start_utc, sample_counter_start, sample_count, sample_format, source_path (input-only) |
| Annotation | capture_uuid, target, annotation_source, annotation_timestamp, separate CSV |

Identifiers are canonical UUID strings. Receiver identity denotes a physical receiver, not transmitter/class identity. Use random UUIDs for real captures; synthetic UUID5 fixtures are test-only. Hash physical serials in a controlled registry; prefer an institution-managed keyed/salted mapping outside the release tree where privacy warrants it. Avoid operator names, IP addresses, precise private locations or unnecessary free-text secrets.

Unknown schema keys fail closed. Explicit labels, predictions, correctness and OOD fields cannot enter acquisition schemas. Vocabulary checks flag target-bearing path tokens, but cannot prove arbitrary UUIDs were generated independently of labels; acquisition design and provenance review remain necessary.

## SigMF-compatible output

raw/<campaign_uuid>/<session_uuid>/<capture_uuid>.sigmf-data
raw/<campaign_uuid>/<session_uuid>/<capture_uuid>.sigmf-meta

Metadata uses core:datatype, core:sample_rate, core:version=1.2.0, core:sha512, capture sample_start/frequency/datetime and a namespaced openew:record. SigMF annotations is empty. Task annotations live outside raw. No SigMF dependency is required; this is a compatibility contract, not certification against every SDR/SigMF consumer.

The original absolute source path is not emitted; only its SHA256 is audit provenance. Exported acquisition CSV/Parquet excludes annotation columns and source paths. The runtime works when no annotation file exists.
