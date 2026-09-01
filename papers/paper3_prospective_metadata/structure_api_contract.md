# Metadata-to-structure API contract

The implemented layer creates structures only; it contains no predictive model.

| API | Contract |
|---|---|
| `build_equality_relations` | typed group incidence from explicitly whitelisted acquisition fields |
| `build_frequency_overlap_relations` | O(N log N) interval components; disabled by default policy |
| `build_episodes` | stable-hash, deterministic target-free grouping/chunking |
| `to_typed_hypergraph` | relation-type-separated incidence arrays without clique expansion |
| `build_temporal_neighbors` | session/reset-local ordered neighbors; causal mode excludes future samples |
| `build_dynamic_snapshots` | fixed temporal windows; refuses anything below `VALID_TEMPORAL_CONTEXT` |

All builders preserve sample IDs and isolated nodes, reject duplicate sample
IDs, and keep partition keys in group identity so no relation crosses train,
validation, or test. Relation type IDs are distinct from hashed relation value
IDs. Value embeddings are not part of this layer.

Labels and annotations are absent from signatures. Missing/unknown identifiers
are isolated rather than merged into a universal “unknown” group. Equality and
incidence construction are O(N) after field access; interval overlap and time
ordering are O(N log N). No O(N²) clique or dense adjacency is materialized.

Dynamic availability is an evidence gate, not a parser convenience. The
caller may pass `VALID_TEMPORAL_CONTEXT` only after a reviewed temporal audit
establishes physical order, session/reset semantics, gap meaning,
inference-time availability, and mixed-target episodes.
