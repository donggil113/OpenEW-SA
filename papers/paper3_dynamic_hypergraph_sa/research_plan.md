# Paper 3 Research Plan

## Proposed scientific question

Can deployment-available static relational context improve RF situation assessment under unseen sensor and scenario shifts without target-domain label leakage?

The original dynamic question is not supported by the current metadata audit and is retained only as a future conditional direction.

## Hypothesis

### PROPOSED DESIGN

Typed equality hyperedges over acquisition-time station, receiver, and coarse date metadata can provide complementary context to independent RF encoders and improve unseen-domain macro-F1 under the frozen Paper 1 protocols. Gains should decline predictably as relation incidences are corrupted. This hypothesis is intentionally narrower than a universal dynamic-hypergraph claim.

## Distinction from prior papers

- **Paper 1** establishes the benchmark and the generalization gap under random versus scenario/day/sensor holdouts. Paper 3 would keep those holdouts frozen and test whether relational inductive bias changes unseen-domain assessment.
- **Paper 2** studies post-hoc uncertainty and feature-distance OOD behavior. Paper 3 would not redefine OOD splits or optimize Paper 2 scores. Uncertainty would enter only as a later, validation-fitted gate after a relational benefit is established.

## Expected novelty

The defensible novelty is a leakage-audited, typed relational domain-generalization protocol for heterogeneous public RF datasets, including an explicit relation whitelist, relation-retention stress test, and evidence that distinguishes useful acquisition context from label-bearing collection structure.

The current audit does not justify novelty claims about dynamic temporal reasoning or neuro-symbolic consistency.

## Conceptual architecture

1. Dataset-specific RF encoder produces one node representation per observation.
2. A pairwise graph or static typed hypergraph aggregates only whitelisted acquisition relations.
3. A task head predicts the original Paper 1 label under the original unseen-domain holdout.
4. Optional uncertainty gating may modulate messages only after M2 is frozen and only from train/validation-fitted uncertainty.
5. Optional symbolic consistency is deferred until a non-label rule is independently verified.

No final dynamic hypergraph model is implemented in this phase.

## Primary endpoint

Unseen-domain holdout macro-F1 under the preserved Paper 1 protocols.

Secondary endpoints: balanced accuracy, per-domain macro-F1, ECE, relation coverage/cardinality, and—conditional on M4—selective risk/coverage.

## Ablation logic

- M0 independent observations establishes whether relations add value.
- M1 pairwise relations distinguishes ordinary graph propagation from hyperedge aggregation.
- M2 typed hyperedges tests station/receiver/date complementarity.
- Field-removal ablations isolate each allowed relation.
- Relation retention at 100/75/50/25/0% tests graceful degradation.
- M4/M5 removals are required only if those stages pass their independent go gates.

## Leakage controls

- Hard per-dataset whitelist enforced in code and run configuration.
- `domain_id` is split-only; labels, OOD flags, source paths, target-pure capture IDs, correctness, and performance are forbidden.
- No cross-partition edges.
- Any train-fitted similarity relation uses source training features only.
- All identifiers stay strings.
- Relation types and hyperparameters freeze before target-domain evaluation.
- Test-domain performance cannot select relations, splits, retention levels, or model stages.

## Major risks

1. Relation richness is low: one allowed JamShield field and two allowed ElectroSense fields.
2. Large equality hyperedges may require sampling and introduce batch sensitivity.
3. Station/receiver metadata may support shortcuts rather than transferable physical reasoning.
4. ElectroSense coarse dates may encode collection campaigns; frequency cannot be used because it is an exact target proxy.
5. DeepSense provides no leakage-safe relation, preventing a uniform three-dataset method claim.
6. A transductive deployment episode may not match operational streaming constraints unless explicitly defined.

## Fallback direction

Recommended title/direction:

> **Relational Domain Generalization for RF Situation Assessment**

Do not use “Dynamic” unless a future audit verifies timestamp/order and target-independent session identity. Do not use “Neuro-Symbolic” unless a rule independent of ground-truth labels and target proxies is identified and validated.

## UNRESOLVED human decisions

- Whether a two-dataset static relational paper is sufficient for the target venue.
- Whether to treat DeepSense as a documented M0-only negative control or omit it from relational claims.
- How to define deployment episodes and maximum hyperedge size before training.
- Whether upstream owners can verify JamShield sampling intervals or ElectroSense exact timestamps without downloading or changing the current datasets.
