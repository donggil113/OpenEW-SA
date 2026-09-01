# Metadata-only relation readiness framework

Readiness is determined without model performance.

| Highest level | Structural requirements |
|---|---|
| `INDEPENDENT_SAMPLE_ONLY` | valid samples; no relation required |
| `STATIC_RELATIONAL` | at least one independently verified, proxy-rejected relation with ≥0.80 coverage and ≥0.50 repeated-node fraction |
| `STATIC_HYPERGRAPH` | at least two such relation types, or one independently verified true multi-node relation |
| `TEMPORAL_RELATIONAL` | `VALID_TEMPORAL_CONTEXT` plus repeated mixed-target episodes |
| `DYNAMIC_HYPERGRAPH` | temporal criteria plus at least two independently verified safe relation types |

Thresholds are conservative defaults and must be frozen before a dataset is
evaluated. A field can be fully populated and still fail because it is
target-pure, a split variable, or semantically unresolved.

The synthetic fixture produces
`/mnt/d/openew_sa_data/paper3/prospective_validation/metadata_readiness_scorecard.json`
and reaches `DYNAMIC_HYPERGRAPH`; this validates software branches only.

Current scientific data verdicts remain:

- JamShield: no new experiment; station equality already failed the frozen
  mechanism gate.
- DeepSense: independent-sample only; no safe varying relation.
- ElectroSense: no new experiment; receiver/date were already tested and no
  valid temporal field was recovered.

Therefore the infrastructure is software-ready for static, temporal, and
dynamic structures, while current data remain scientifically not ready. New
prospective collection is required.
