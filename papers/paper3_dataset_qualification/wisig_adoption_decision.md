# WiSig Adoption Decision

## Verdicts

| Question | Verdict | Basis |
|---|---|---|
| WiSig access | **GO** for metadata/code; **CONDITIONAL GO** for payload | Official page and repositories are public. Compact payloads are hosted on Google Drive; unattended retrieval was not validated beyond the official interstitial. |
| WiSig licence | **RESTRICTED** | CC BY-NC-SA 4.0 is verified and research-compatible, but attribution, noncommercial, and share-alike constraints require institutional review for derived-payload distribution. |
| Static receiver/day DG | **CONDITIONAL GO** | Receiver and day axes are verified, but the exact receiver/day holdout, converter, and sample-level QA are not yet frozen. Day remains split-only. |
| Static relational | **NO-GO in the raw/current path; CONDITIONAL GO after a conversion gate** | `receiver_id` passes the frozen structural/proxy evidence, but official source paths expose the transmitter target. An opaque-ID, annotation-separated conversion and repeat audit are required. |
| Temporal | **NO-GO** | No explicit packet clock; source order is nested inside one-transmitter captures. |
| Dynamic | **NO-GO** | Valid mixed-target temporal episodes and two independent validated relation types are absent. |

## Frozen readiness result

Applying the PR #82 thresholds without adjustment yields **STATIC_RELATIONAL** as the highest metadata-structure level: receiver coverage and repeated grouping exceed 0.80 and 0.50 respectively, and the receiver-field proxy audit is negative. The end-to-end adoption gate nevertheless returns static-relational **NO-GO** for the current raw representation because the official source path is target-bearing. The dataset does not reach static-hypergraph readiness because only one independently verified relation type is available. Temporal readiness is rejected.

## Authorization decision

**NEXT MODEL EXPERIMENT: NOT AUTHORIZED.** Before authorization, a human must accept the licence obligations, import one official compact subset, convert it into separated acquisition/annotation tables, repeat the target-proxy and readiness audits at sample level, and freeze a receiver/day domain-generalization split without inspecting model results.

No RF payload was downloaded and no model was trained in this workstream.
