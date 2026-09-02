# WiSig ManyRx conversion and quality gate

Status: **PASS**, completed before split construction or model evaluation.

## Source and conversion

- Official archive: `ManyRx.pkl.zip`, 1,249,528,063 bytes.
- Archive SHA-256: `d2b23108c3f6f63a10ebbb149d7b08d6e1c1961cf5184926fbab452def3049de`.
- Extracted object SHA-256: recorded externally in `RAW_SHA256SUMS.txt`; the payload is not distributed through Git.
- Safety inspection: one regular, non-executable member; no absolute path, traversal component, or symlink.
- Restricted load: NumPy reconstruction only; arbitrary pickle globals and persistent IDs are rejected.
- Selected representation: official non-equalized variant (`equalized_index=0`), matching the official ManyRx receiver-shift example. The source arrays are finite `float64` I/Q with shape `(packets, 256, 2)`; converter output is deterministic `float32` with shape `(packets, 256, 2)`.
- Converted packets: 249,666 in 31 shards. Acquisition metadata and transmitter annotations are separate.
- Source load peak RSS: approximately 2.1 GiB. The compact pickle itself is a single object and cannot be streamed safely; shard assembly remains bounded to 8,192 packets.

## Official-index reconciliation

The official non-equalized full-universe aggregate index contains 9,976,477 packets across 174 transmitters, 41 receivers, and four capture days. ManyRx selects 10 transmitters and 32 receivers with a per-cell cap of 200. The selected cells represent 1,320,455 full-index packets before capping. For all 1,280 selected transmitter–receiver–day cells, the compact payload count equals `min(full-index count, 200)`. This yields exactly 249,666 payload-resolvable packets, zero mismatched cells, zero duplicate packet keys, and no orphan member records. The remaining full-universe packets are excluded by official subset design and are not conversion failures.

## Determinism and sample-level QA

Pass A and a fresh Pass B each produced 156 deterministic files. Relative paths, sample IDs, acquisition CSVs, annotation CSVs, restricted provenance, feature arrays, shard manifests, and the dataset manifest are byte-identical. Runtime timestamps and state files are explicitly excluded from byte comparison.

All-row QA passed:

- unique acquisition and annotation sample IDs;
- one-to-one acquisition/annotation coverage;
- finite features with the frozen shape and dtype;
- valid 32-receiver and four-day universes;
- no transmitter column in acquisition metadata;
- no exact source path or filename column;
- no outer identifier whitespace;
- shard hashes complete and matching.

## Target-proxy result

Annotations were joined only inside the audit process. `receiver_id` passes as `RELATION_ALLOWED`: NMI 0.005639, weighted target purity 0.102537, and zero near-deterministic target mass. `day_id` passes only as `SPLIT_ONLY` (NMI 0.000032). `packet_index` remains `AUDIT_ONLY` and is not interpreted as time.

The audit explicitly identifies `source_record_index` as a forbidden target proxy because deterministic conversion is target-nested. Feature-shard coordinates are storage-only and also show strong target association. Neither field is exposed to the model or context builder. This is a quarantine result, not a reason to reorder data post hoc.

## Support cube

There are 1,251 nonzero cells among 1,280 possible transmitter–receiver–day combinations (97.734375% coverage). Cell support ranges from 68 to 200 packets with median 200. Every transmitter occurs on all four days and at 31 or 32 receivers; every receiver contains 9 or 10 transmitters. The full cube and QA outputs remain external.
