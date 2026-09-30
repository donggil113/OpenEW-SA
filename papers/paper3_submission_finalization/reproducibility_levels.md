# Paper 3 reproducibility levels for a submission package

The scientific freeze tag paper3-scientific-freeze-20260929 fixes the evidence and numerical conclusions. This document states what different reconstruction claims require; it neither runs nor authorizes new science.

| Level | Inputs and operation | What a successful check supports | What it does not support |
|---|---|---|---|
| A — payload-absent reporting | Tracked small aggregates, frozen scientific tables/figures, manuscript and TeX dependencies; run the release/package build and PDF audit. | Reproduction of reviewed presentation artifacts from frozen summaries on the tested host. | Independent raw-data conversion, split generation, training, prediction, or external-dataset replication. |
| B — lawful data-present reconstruction | Official WiSig ManyRx obtained lawfully, source archive hash/provenance, frozen converter and acquisition/annotation separation, deterministic split/support rules and hash comparisons. | Structural reconstruction of data manifests, eligible receiver/class mapping, disjoint support/query IDs, and specified hashes if actually executed and matched. | A claim that model checkpoints or published statistics were independently reproduced. |
| C — full scientific rerun | Level B inputs plus frozen code/configuration, compatible environment, new isolated experiment root, receiver-level blind evaluation and one-time analysis. | A new, auditable model/prediction/analysis reproduction only if actually executed and validated. | Automatic bitwise equivalence across new GPU/driver/OS, licence permission to redistribute payload, or validation on another dataset. |

The existing [PR #90 closure account](../paper3_pr90_closure/reproducibility_levels.md) reports an executed Level-A reporting check and documents B/C entry points. That historical same-host Level-A result must not be relabeled as full scientific reproduction on this submission-finalization branch. The current final PDF/package check should report its own command, environment, outputs, hashes, and technical QA.

The Level-B/C entry points and frozen inputs are documented in the closure account and the [payload-absent release README](../paper3_receiver_adaptation_manuscript/reproducibility_release/README.md). These require a new, empty external output root and lawful official data. They must never overwrite frozen checkpoints, prediction archives, unblinding manifests, or analysis outputs. This submission-finalization task executes Level A only; B and C remain NOT EXECUTED here.
