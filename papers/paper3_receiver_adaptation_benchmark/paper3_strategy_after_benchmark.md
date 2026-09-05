# Paper 3 strategy after the receiver-adaptation benchmark

Status: **DECISION RECORD**

## Answer first

The WiSig benchmark is methodologically complete enough to support a bounded single-dataset methods result: T3A reliably improves unseen-receiver transmitter recognition with 128 unlabeled packets, whereas P2 and the source-DG baselines do not materially exceed P0. It is not yet a strong cross-dataset Paper 3 because lawful Shen data remain unavailable and no physically acquired calibration/query dataset has been evaluated.

Publication gate: **CONDITIONAL**.

Maximum defensible claim:

> On the WiSig 32-receiver LOSO benchmark, unlabeled receiver calibration through T3A improves receiver-equal macro-F1 over source-only ERM by 0.0280, with improvement on 31/32 receivers and a receiver-bootstrap interval excluding zero; frozen P2 context conditioning does not materially improve P0. Generalization beyond WiSig and deployment-realistic acquired calibration episodes remains unresolved.

## Ranked options

1. **Option C — prospectively collect then write a cross-dataset paper.** Highest scientific strength and reviewer resistance; medium time and operational risk; strongest metadata provenance and episode realism.
2. **Option B — wait for lawful Shen access.** Useful independent multi-receiver benchmark and lower acquisition effort, but licence/access and acquired-episode limitations remain high-risk.
3. **Option A — WiSig receiver-adaptation benchmark paper.** Lowest time and a clear benchmark result, but single-dataset evidence and hash-partitioned rather than acquired support are material reviewer risks.
4. **Option D — WiSig + Shen + prospective collection.** Strongest ultimate package but currently infeasible because Shen access is blocked and it has the highest time/data risk.

## Recommendation

Run a real SMALL-tier prospective acquisition pilot first. Require eight physical receivers, three hardware families, two sites, and physically separate calibration/query sessions. Freeze target-proxy and split gates before any model. Keep seeking lawful Shen access in parallel, but do not make it the critical path.

If a rapid venue deadline requires a paper before new data, frame WiSig as a receiver-adaptation benchmark and methods caution: adaptation choice matters more than adding a learned context module. Do not claim P2 novelty, temporal reasoning, acquired calibration realism, or cross-dataset generality.
