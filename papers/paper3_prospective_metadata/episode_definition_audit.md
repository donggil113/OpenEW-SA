# Deployment episode definition audit

Episodes below are defined from metadata first. Labels are used only afterward
to measure purity and mixed-label variation. Aggregate values are generated in
`/mnt/d/openew_sa_data/paper3/metadata_audit/episode_candidates.csv`.

| Dataset | Candidate episode | Coverage | Episodes | Median / max size | Mixed-label episode fraction | Leakage classification | Decision |
|---|---|---:|---:|---:|---:|---|---|
| JamShield | station (`rx_id`) | 1.0 | 7 | 11,150 / 24,823 | 0.714286 | structurally allowed, already tested | reject as basis for another current-data experiment |
| DeepSense | day | 1.0 | 2 | 16,000 / 16,000 | 1.0 | split-only | not a deployment episode |
| DeepSense | source capture | 1.0 | 32 | 1,000 / 1,000 | 0.0 | target-bearing filename and target-pure | forbidden |
| ElectroSense | receiver | 1.0 | 40 | 1,000 / 4,800 | 1.0 | structurally allowed, already tested | no new experiment |
| ElectroSense | coarse date | 1.0 | 19 | 1,200 / 15,000 | 1.0 | semantics only partially verified | unresolved/new collection required |
| ElectroSense | receiver-date | 1.0 | 45 | 1,000 / 1,800 | 1.0 | already tested in PR #81 | no new experiment |
| ElectroSense | source file | 1.0 | 229 unique IDs across 232 arrays | 200 / 200 in converted subset | 0.0 | technology-bearing and target-pure | forbidden |

The JamShield station sizes in the external CSV are computed from the frozen
92,486-row artifact. Five station groups are mixed-label and two are
single-target. That purity is an audit fact, never a relation feature.

## Session criteria

A valid prospective episode must have a target-neutral session identifier,
documented open/close semantics, known clock-reset boundaries, inference-time
availability, and adequate within-episode target variation. It must be built
independently inside train, validation, and test partitions.

No current dataset satisfies all criteria. A day, file, class folder, or
technology-specific NPY array is not silently relabeled as a session.
