# Acquisition metadata and annotation separation

## Mandatory two-object architecture

### A. `acquisition_metadata.parquet`

One row per `sample_id`, containing only acquisition facts: session, capture,
order/time, clock, receiver/site, frequency/sample-rate, hardware, and
field-level quality indicators.

### B. `annotations.parquet`

Long-form task records:

| Field | Meaning |
|---|---|
| `sample_id` | foreign key to acquisition table |
| `task_name` | versioned task definition |
| `target_label` | semantic target |
| `annotation_source` | human, instrument, rule, or adjudication source |
| `annotation_time` | optional UTC time at which annotation was assigned |

Annotations may be many-to-one with a sample across tasks. They are loaded by
supervision/evaluation code only after graph structure has been frozen.

## Enforced access boundary

Relation, episode, temporal-neighbor, hypergraph-incidence, and dynamic-snapshot
builder signatures accept only `AcquisitionRecord` objects. They do not accept
annotation objects. Field eligibility and an experiment-specific whitelist are
both required. Unknown fields fail closed, and grouping is partition-local.

The safety audit may join acquisition and annotation tables by `sample_id` to
measure purity, NMI, conditional entropy, and missingness association. That
audit output is `AUDIT_ONLY`; it is not written back into acquisition rows and
cannot be a model feature.

## Required processing sequence

1. Freeze raw capture hashes and target-free acquisition metadata.
2. Validate schema, provenance, timestamps, and target-neutral filenames.
3. Construct candidate sessions/relations without annotations loaded.
4. Load annotations in the isolated safety-audit process and reject proxies.
5. Freeze dataset-specific relation whitelist and split policy.
6. Construct train/validation/test partitions by capture/session-safe rules.
7. Build relations separately within each partition.
8. Train with source labels; freeze predictions before target evaluation.

Loading annotations must never mutate acquisition metadata. Tests enforce that
separation and inspect builder signatures.
