# Future metadata-enriched experiment preregistration (draft; not executed)

This protocol becomes active only after a new dataset passes the structural
metadata readiness scorecard. Ineligible stages are omitted, not approximated
with weaker metadata.

## Scientific question

Can prospectively recorded, leakage-audited acquisition context improve RF
situation assessment under a prespecified unseen receiver/site/campaign/time/
hardware shift without target-domain label leakage?

## Model stages

| Stage | Eligibility gate | Definition |
|---|---|---|
| P0 | any labeled dataset | independent-sample baseline |
| P1 | `STATIC_RELATIONAL` | pairwise/group relational baseline with frozen allowed fields |
| P2 | `STATIC_HYPERGRAPH` | typed multi-relation incidence aggregation |
| P3 | `TEMPORAL_RELATIONAL` | session-local causal temporal neighbors |
| P4 | `DYNAMIC_HYPERGRAPH` | time-windowed typed relational snapshots |
| P5 | separate uncertainty protocol | uncertainty-aware extension after P1/P2/P3/P4 mechanism support |
| P6 | separately validated non-label rules | symbolic consistency; never a re-encoding of ground truth |

Passing metadata readiness does not imply that the predictive hypothesis is
true. It only permits a stage to be tested.

## Endpoints and seeds

Primary endpoint: macro-F1 on the prespecified unseen-domain holdout. Secondary:
balanced accuracy, accuracy, per-domain macro-F1, ECE, and selective risk only
if P5 is separately activated. Use exactly five seeds, frozen before training;
the candidate set is 829, 1829, 2829, 3829, and 4829 unless a future hardware
preregistration replaces the whole set before any target evaluation. No seed is
discarded.

## Selection and target policy

Preprocessing, relation fields, episode size, context window, architecture,
optimization, and early stopping are chosen from source documentation,
resource profiling, and source-only validation. The target partition is opened
once after predictions/configs are frozen. No target result can trigger relation
or split redesign in the same study.

## Mandatory controls

- label-independent shuffled-relation control preserving group-size structure;
- relation-retention curve at 100%, 75%, 50%, 25%, and 0%;
- field/type removal ablations declared before target evaluation;
- P0 capacity-matched control;
- causal/no-future checks for P3/P4;
- exact capture/session/partition non-overlap audit.

## Negative-result interpretation and gates

A relation mechanism requires reproducible source-validation improvement,
held-out non-degradation within absolute 0.01, and meaningful separation from
the shuffled control. Retention should exhibit interpretable dependence rather
than arbitrary instability. Failure yields NO-GO for that stage. A target-only
gain cannot authorize redesign. P5/P6 are never automatically started after a
positive P2/P4 result.

## Data freeze prerequisites

Before training, commit the schema version, source hashes, provenance sidecar,
eligibility decisions, target-proxy audit, metadata scorecard, split hashes,
relation whitelist, episode semantics, time/reset semantics, seeds, budgets,
and automatic GO/NO-GO rule.
