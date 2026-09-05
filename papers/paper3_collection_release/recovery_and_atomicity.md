# Durability, recovery and limits

Each state mutation runs under a POSIX file lock. A full-state journal envelope is written to a create-exclusive .partial, flushed/fsynced and renamed to .pending.json. State is similarly replaced; the envelope becomes .committed.json after successful persistence. Directory fsync follows renames. Before further mutations, pending transitions require explicit recover. State hash must match the latest committed journal.

| Interruption | Recovery behavior |
|---|---|
| After durable journal, before state | Replay exactly next revision after SHA validation |
| After state, before journal commit | Verify identical state and finalize event |
| Partial state write | Preserve under recovery with content hash; never promote partial bytes |
| During payload copy / simulated disk full | Partial file remains invalid |
| Payload complete, no metadata | Orphan payload reported; no auto-registration |
| Payload and metadata complete, no journal | Orphan pair reported; operator provenance review |
| Unclosed session | Report explicitly; no invented end time/counter |
| Partial day freeze | Report and block; no overwrite |
| Changed finalized freeze | Manifest hash differs from journal binding: FAIL |
| Changed capture / symlink replacement | Hash/metadata/symlink validation: FAIL |

Synthetic tests inject these boundaries, including a subprocess that exits with os._exit after journal persistence. This tests software failure paths, not real loss of power to a controller/cache. WSL /mnt/d honors observed calls, but on-device durability must be measured.

The journal stores full snapshots and grows approximately quadratically with capture count. Stress validation covers bounded campaigns (500 captures per calibration cycle), not millions of tiny captures. Use larger bounded capture files, site/day campaigns and explicit storage monitoring. Do not prune scientific journals ad hoc. A future compact journal format would require versioning/migration tests before deployment.

Recovery never authorizes training, fixes targets or changes acquisition boundaries from labels. Local hashes detect accidental drift only relative to a trusted journal/backup; coordinated malicious rewriting of every local hash is outside this tool's guarantee.
