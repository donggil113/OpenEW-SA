# Paper 3 fallback research direction after static-relational NO-GO

## Decision

**VERIFIED RESULT.** The frozen static relational M0–M2 pilot is overall NO-GO: both JamShield protocols are NO-GO and ElectroSense is CONDITIONAL GO. Actual relations did not clear the shuffled-control criterion on any protocol. Therefore the current equality metadata do not warrant a positive paper outline, dynamic hypergraph model, uncertainty-gated extension, or neuro-symbolic extension.

## Recommended fallback

Pause model escalation and establish a **prospective metadata-enriched RF domain-generalization protocol**.

The next data phase should record, at acquisition time and independently of target annotations:

- monotonic capture/session identifiers and within-session order;
- reliable timestamps or bounded acquisition windows;
- receiver/station/site identity with explicit deployment availability;
- channel, center frequency, and band descriptors whose relationship to the target is audited;
- operational context identifiers that do not encode jammer/class/scenario state;
- missingness and reset semantics for every context field.

The objective is not to add more relations to the present target-visible experiment. It is to create a new evidence base in which relation meaning, coverage, and deployment availability can be verified before model design.

## Required safeguards before another relational experiment

1. Audit every candidate field against target purity, domain leakage, inference availability, and missingness.
2. Demonstrate at least two non-target-derived relation types with adequate within-partition variation.
3. Demonstrate defensible order/time information before using “dynamic” or “temporal.”
4. Freeze all context, chunking, split, seed, and model choices using source data only.
5. Retain shuffled-relation and incidence-retention controls as mandatory primary diagnostics.
6. Predeclare how a target-neutral or negative result will be interpreted.

## What not to do

- Do not select ElectroSense `receiver_only` because it had the best target mean in the completed ablation.
- Do not reinterpret station/scenario identifiers or frequency as permissible relations.
- Do not optimize context size or retention against the frozen held-out domains.
- Do not start M3, M4, or M5 on the current metadata.
- Do not reuse Paper 2 OOD scores as relation definitions.

## Possible future question

**PROPOSED DESIGN.** After a successful new audit, ask: “Does prospectively recorded acquisition context provide reproducible source-validation and unseen-domain benefit beyond independent RF encoders and shuffled-context controls?”

This future wording is deliberately neutral about graph family. Static graph, hypergraph, or temporal modeling should be selected only after the new metadata establish the required structure.

## Near-term action

Write and review an acquisition metadata specification and a leakage-oriented data collection plan. Do not train another relational model until that specification is implemented and audited on data not used in the completed pilot.

## Human decision

**UNRESOLVED.** Decide whether to preserve the completed negative pilot as a standalone cautionary study (“when acquisition equality metadata do not generalize”) or treat it solely as an internal gate for a future prospectively collected Paper 3 dataset. Neither choice changes the frozen NO-GO result.
