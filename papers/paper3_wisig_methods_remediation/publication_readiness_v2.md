# WiSig V2 publication-readiness assessment

Status: **PRE-UNBLINDING STRUCTURE; VERDICT WITHHELD**

## Decision boundary

The eventual verdict is one of `READY_FOR_MANUSCRIPT`, `CONDITIONAL`, or `NOT_READY`. It is based on the frozen GO rule, receiver-level effect and uncertainty, mechanism-specific controls, information-matched adaptation baselines, deployment realism, integrity, and reproducibility. Target performance cannot alter a method, receiver, seed, support budget, context size, class set, or comparison.

## Evidence domains

| Domain | Required evidence | Pre-unblinding status |
|---|---|---|
| Novelty | Distinct test-time receiver-context question versus Papers 1 and 2 | Framing frozen |
| Effect size | Equal-weight 32-receiver P2 comparisons | Withheld |
| Mechanism specificity | Shuffled, mismatched, null, and composition controls | Design frozen |
| Baseline coverage | ERM/capacity, source DG, RX-NORM, and T3A | Methods frozen |
| Statistical rigor | Seed-average within receiver; receiver bootstrap/sign flip; Holm family | Analysis frozen |
| Deployment realism | Disjoint bounded support/query; no session/temporal claim | Contract frozen; residual limitation acknowledged |
| Compute/information fairness | Support access, updates, parameters, FLOPs, latency, memory | Audit code frozen |
| License/reproducibility | External CC BY-NC-SA payload; code/splits/hashes releasable | Constraint retained |
| Integrity | Paper 1/2 and PR #80--#84 immutability | Interim PASS; final pending |

## VERIFIED RESULT

To be populated only from validated external analysis outputs.

## INTERPRETATION

Withheld until all preregistered receiver-level evidence is complete.

## UNRESOLVED

- No independently observed receiver-calibration episode exists in WiSig.
- Raw and converted payload redistribution remains license-constrained.
- No faithful RF-specific receiver-robust method was implementable without inventing missing cross-dataset choices; the official equalized variant is a separate diagnostic.
