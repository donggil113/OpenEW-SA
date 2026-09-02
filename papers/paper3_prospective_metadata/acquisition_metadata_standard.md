# OpenEW-SA acquisition metadata standard v1.0.0

## Purpose and scope

This standard records facts known at RF acquisition time. It deliberately
excludes semantic task labels. Its goal is to make future receiver/site/session/
time relations reviewable before model training and to preserve enough clock
and provenance information for legitimate temporal experiments.

The normative Python record is `openew.paper3.metadata.schema.AcquisitionRecord`;
the machine-readable companion is
`configs/paper3/metadata/acquisition_metadata_schema_v1.json`. Identifiers are
strings and numeric identifiers are rejected rather than coerced. Leading zeros
are therefore preserved.

## Field catalog

| Field | Required | Type / units | Meaning and constraints |
|---|---:|---|---|
| `schema_version` | yes | string | exactly `1.0.0` |
| `sample_id` | yes | opaque string | immutable row identity; never a label |
| `acquisition_session_id` | yes | opaque string | target-neutral interval with documented open/close semantics |
| `capture_id` | yes | opaque string | raw capture UUID |
| `within_capture_index` | yes | nonnegative integer | physical source-record order |
| `timestamp_utc` | conditional | ISO-8601 UTC string | acquisition time; explicit UTC offset required |
| `timestamp_source` | conditional | string | GNSS/PTP/device/host/software source |
| `timestamp_resolution_ns` | optional | nonnegative integer | nominal quantization |
| `timestamp_uncertainty_ns` | optional | nonnegative integer | estimated error bound |
| `clock_domain` | optional | string | clock identity, not receiver label |
| `clock_reset_id` | conditional | string | changes on discontinuity/reboot/resynchronization |
| `receiver_id`, `station_id`, `sensor_id` | optional | opaque strings | acquisition endpoint identities; record applicable terms |
| `site_id` | optional | privacy-safe string | acquisition site, separate from receiver |
| `hardware_model` | optional | string | hardware family; split-only by default |
| `hardware_serial_hash` | optional | salted/hash string | non-reversible unit identity; salt governance required |
| `firmware_version` | optional | string | acquisition firmware; split-only by default |
| `antenna_id` | optional | opaque string | antenna identity |
| `antenna_configuration` | optional | controlled string | gain/polarization/array state, without task semantics |
| `center_frequency_hz` | optional | finite nonnegative number | tuned center frequency |
| `lower_frequency_hz`, `upper_frequency_hz` | optional | finite nonnegative numbers | physical observed bounds; lower must not exceed upper |
| `bandwidth_hz` | optional | positive number | acquisition bandwidth |
| `sample_rate_hz` | optional | positive number | complex or real sampling rate, documented in provenance |
| `channel_id` | optional | string | physical/configured channel, not semantic class |
| `location_id` | optional | privacy-safe string | location bucket or token |
| `location_precision_class` | optional | controlled string | e.g. `site`, `building`, `region`; never exact coordinates by default |
| `campaign_id` | optional | opaque string | acquisition campaign; split-only by default |
| `environment_context_id` | optional | opaque string | context recorded before annotation; independent of target |
| `operational_context_id` | optional | opaque string | mission/operating context; must pass proxy audit |
| `source_file_id` | optional | opaque capture UUID only | not a path and not a class/scenario name |
| `source_record_index` | optional | nonnegative integer | index in immutable raw source |
| `metadata_missing_mask` | optional | string list | explicitly names unavailable schema fields |
| `metadata_quality_flags` | optional | string list | controlled QA flags |

Timestamp resolution/uncertainty require `timestamp_source`. A temporal-ready
row needs a timestamp, clock domain/reset identity, session, and source order;
population alone does not establish scientific validity.

## Eligibility states

Every field is explicitly assigned one state: `RELATION_ALLOWED`,
`MODEL_FEATURE_ALLOWED`, `SPLIT_ONLY`, `AUDIT_ONLY`, `FORBIDDEN_LABEL`,
`FORBIDDEN_TARGET_PROXY`, or `UNRESOLVED`. Unknown fields fail closed. The
versioned default policy is `configs/paper3/metadata/eligibility_policy_v1.yaml`.

`RELATION_ALLOWED` is necessary but not sufficient. Each experiment must also
freeze a dataset-specific whitelist after source-semantics, coverage,
missingness, and label-proxy audits. Frequency is a model feature—not a relation
by default—because band/task coupling is common in RF datasets.

## Target-free storage contract

Preferred storage is `acquisition_metadata.parquet`, with CSV/JSON supported
when Parquet dependencies are unavailable. The acquisition object must never
contain class, attack, occupancy, OOD, prediction, correctness, threat, or
performance fields. Those belong to the annotation table.

## Versioning and immutability

- Any semantic or required-field change increments the schema version.
- Raw capture and metadata tables are frozen by SHA-256 manifest before split
  creation.
- Corrections are append-only transformations with a provenance history; they
  do not silently overwrite the original record.
- Capture UUIDs and sample IDs never encode class, jammer, occupancy,
  technology, scenario target state, or split membership.
