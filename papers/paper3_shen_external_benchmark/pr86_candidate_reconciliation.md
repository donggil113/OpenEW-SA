# PR #86 reconciliation for the Shen candidate

PR #86 concluded that public existing-data **exact acquired-calibration
replication is NO-GO**. This review does not reverse that decision.

## A. Acquired-calibration replication

This requires a physically acquired, target-neutral receiver calibration
episode that precedes and is capture-disjoint from query acquisition. The Shen
paper/release documents train and test receiver files and labeled fine-tuning,
but not a target-neutral calibration episode with operational open/close
semantics. A hash split of packets cannot create that missing provenance.

**Verdict: NO-GO.**

## B. Bounded unlabeled receiver-support benchmark

A scientifically narrower independent benchmark may partition an eligible
receiver's released packets into a fixed unlabeled support bank and disjoint
query set by stable sample-ID hashing. It must be described as a benchmark
information regime, not deployment-realistic acquired calibration. Receiver ID
is the only support relation; transmitter labels and target-nested packet order
are forbidden.

The dataset appears structurally promising for this question because it has 20
physical receivers, six hardware models, and a transmitter-fingerprinting task.
It remains ineligible until licence/access, payload schema, exact 256-IQ
conversion, target-proxy, class-support, and split-integrity gates pass.

**Verdict: CONDITIONAL GO IN PRINCIPLE; NOT AUTHORIZED IN THIS WORKTREE.**

This distinction preserves PR #86: path A remains closed, while path B is a
newly bounded benchmark question whose limitations are explicit.
