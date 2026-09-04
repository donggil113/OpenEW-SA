# WiSig methods-remediation V2 handoff

Status: **COMPLETE**

Frozen mechanism verdict: **CONDITIONAL_GO**

Publication readiness: **NOT_READY**

## Scientific question and information regimes

V2 asks whether a fixed RF fingerprinting model conditioned on a bounded, unlabeled support bank from an unseen receiver improves transmitter identification beyond capacity-matched ERM, source-only domain-generalization methods, and test-time adaptation given the same support. It separates:

- **R0, pure inductive:** query packet and trained source model only;
- **R1, test-time receiver context/calibration:** 128 unlabeled receiver support packets, disjoint from every query;
- **R2, test-time adaptation:** the same 128-packet support bank may update permitted statistics or prototypes without labels.

P1 and P2 are test-time context methods, not pure domain-generalization methods. V2 makes no temporal, dynamic, graph, hypergraph, or neuro-symbolic claim.

## Power-loss recovery

The interrupted worktree was preserved against the existing backup at `/mnt/d/openew_sa_data/paper3/wisig_v2/recovery/worktree_20260904_210457/`; the backup was not modified. A source audit found 99 nonempty, UTF-8, newline-terminated V2 files, with all Python and YAML files parseable and no merge/patch markers. All intended pre-unblinding source, documentation, tests, and configs were committed as `da07219a018d4c10eb365e9cd2a847fe59520eda` before any target labels were joined.

The immutable pre-unblinding freeze was created at `2026-09-04T12:45:26.457185+00:00`; its SHA-256 is `705f723b7af65564a17af04ec2cc63b6a33627c2db96fdf7425ffc23a889959e`. The single primary unblinding occurred at `2026-09-04T12:49:29.489216+00:00`. No prior unblinding artifact existed, and no second unblinding was attempted.

## VERIFIED RESULT — blind compute and integrity

| Suite | Planned | Complete | Failed | Incomplete | Blind archives |
|---|---:|---:|---:|---:|---:|
| Primary receiver LOSO | 2,080 | 2,080 | 0 | 0 | 2,080 |
| Day secondary | 260 | 260 | 0 | 0 | 260 |
| Grouped receiver secondary | 180 | 180 | 0 | 0 | 180 |
| **Total** | **2,520** | **2,520** | **0** | **0** | **2,520** |

A final read-only reconciliation re-derived the same primary prediction manifest `9e80ed7a25ddcf3d9aa3365d0a687eb9549257cbf789040cdc71c20391c2e1f1`, checkpoint manifest `159a7c8df1a283addd7e713e48b7ee0d1afbaa8177324255cc9c51c7fca74bf6`, and history manifest `5e81b3c4844266be6128e4e86a0004f8b5545b5c4e4d5b0c9514220ef9d9a387`. Day and grouped manifests also matched their recovery snapshots. Every archive contained only `sample_ids` and `probabilities`; query IDs, probability simplexes, split/data/config hashes, checkpoint lineage, and support/query disjointness passed.

The raw WiSig archive hash remains `d2b23108c3f6f63a10ebbb149d7b08d6e1c1961cf5184926fbab452def3049de`. Paper 1, Paper 2, and PR #80--#84 paths passed immutable-history checks. No model was retrained during recovery.

## VERIFIED RESULT — primary receiver-level metrics

Five seeds were averaged within each of 32 held-out receivers before equal-weight aggregation.

| Method | Regime | Mean macro-F1 | Receiver SD |
|---|---|---:|---:|
| P0 | R0 | 0.805679 | 0.084300 |
| P0-WIDE | R0 | 0.801535 | 0.090017 |
| DG-CORAL | R0 | 0.805071 | 0.082638 |
| DG-DANN | R0 | 0.800926 | 0.084789 |
| DG-GROUPDRO | R0 | 0.761754 | 0.078898 |
| SOURCE-NORM | R0 | 0.805976 | 0.086385 |
| P1 | R1 | 0.809384 | 0.085958 |
| P2 | R1 | 0.806726 | 0.082039 |
| P2-SHUFFLED | R1 control | 0.788362 | 0.086526 |
| P2-MISMATCHED-RX | R1 control | 0.787088 | 0.084843 |
| P2-NULL | R1 control | 0.782610 | 0.083633 |
| RX-NORM | R1 | 0.800769 | 0.086944 |
| T3A | R2 | 0.833692 | 0.078929 |

T3A was selected as the same-information TTA comparator using source validation only. DG-CORAL was selected analogously as the strongest source-DG comparator.

## VERIFIED RESULT — fixed comparison family

| Comparison | Mean receiver delta | 95% receiver-bootstrap interval | Sign-flip p | Holm-adjusted p |
|---|---:|---:|---:|---:|
| P2 minus P0 | +0.001047 | [-0.006660, 0.008857] | 0.793472 | 0.793472 |
| P2 minus P0-WIDE | +0.005191 | [-0.003300, 0.013471] | 0.234208 | 0.468415 |
| P2 minus P2-SHUFFLED | +0.018364 | [0.013924, 0.023171] | 0.000010 | 0.000040 |
| P2 minus T3A | -0.026966 | [-0.038002, -0.016769] | 0.000010 | 0.000040 |

P2-minus-P0 was positive for 15 receivers and negative for 17. Hardware-family mean differences were -0.001337 for B210, -0.000010 for N210, and +0.004782 for X310. Only one of three family means was positive.

Descriptive comparisons were P2-minus-P2-MISMATCHED-RX +0.019637, P2-minus-P2-NULL +0.024116, P2-minus-RX-NORM +0.005957, P2-minus-P1 -0.002658, and P2-minus-DG-CORAL +0.001655. These were not added to the Holm family.

## VERIFIED RESULT — source validation and secondary analyses

Source-validation macro-F1 was 0.822618 for P0, 0.823429 for P2, 0.822234 for DG-CORAL, and 0.850511 for T3A. Selection used no target metric.

- **Coarse-day secondary:** P0 0.869983, P2 0.876531, T3A 0.904627. Day is a coarse acquisition domain, not time or temporal context.
- **Repeated grouped receiver secondary:** P0 0.730877, P2 0.732534, P2-SHUFFLED 0.718119. This is descriptive robustness only; LOSO remains primary.
- **Support budget:** means at 16/32/64/128/256 packets were 0.803529/0.806289/0.806618/0.806712/0.806788. The preregistered primary remains 128.
- **Context k:** means at k=8/16/32/64 were 0.798217/0.803696/0.806726/0.808631. The preregistered primary remains k=32.

No favorable budget or k was selected.

## VERIFIED RESULT — composition and oracle diagnostics

All natural support banks contained all six classes. Same-class-excluded oracle support achieved 0.825916 macro-F1 and was +0.020237 above P0 with full coverage. Same-class-only support achieved 0.608450 (-0.197229 versus P0); transmitter-pure support achieved 0.763193 (-0.042485 versus P0). These conditions use labels and are nondeployable diagnostics.

The findings do not support the claim that P2's natural-support behavior is driven only by seeing the query class. They do show that homogeneous support composition can strongly harm the fixed context model.

## VERIFIED RESULT — information and compute fairness

P2 and T3A consumed the identical unlabeled 128-packet target-receiver support bank. Median standardized test-time latency was 0.557081 s for P2, 0.020513 s for P0, and 0.024697 s for T3A. P2 therefore cost approximately 27.2 times P0 and 22.6 times T3A in this benchmark. All 416 standardized benchmark archives reproduced their frozen blind probabilities exactly; target labels were not read.

## Equalized diagnostic

No equalized model run was launched. The frozen conversion audit passed deterministic and sample-level QA but failed the required raw-structure match: 247,684 equalized samples versus 249,666 raw samples. The equalized diagnostic therefore remained gated out exactly as preregistered.

## Decision

The frozen rule returned **CONDITIONAL_GO**. P2 passed positive-mean checks versus P0, P0-WIDE, shuffled, and mismatched support; same-class-excluded context survived; integrity and disjointness passed. It failed competitiveness with T3A, majority-receiver support, and multiple-hardware-family support.

## INTERPRETATION

V2 preserves a mechanism-specific signal relative to broken or absent context, but the practical P2-versus-P0 benefit is near zero and P2 is decisively worse than the simpler same-information T3A baseline. PR #84 is reconciled as outcome D: P2 does not exceed standard TTA. The V2 evidence is not sufficient for a P2-centered Paper 3 manuscript.

## UNRESOLVED / next action

- Publication readiness is `NOT_READY`; no manuscript outline is created.
- WiSig has no verified deployment receiver-calibration episode.
- The next scientific step is an independent, prospectively recorded receiver-calibration dataset and a frozen replication of P0, T3A, and P2 without V2-driven target tuning.
- Raw/converted WiSig payloads and predictions remain external and license-constrained.

## Reproducibility outputs

The external analysis root is `/mnt/d/openew_sa_data/paper3/wisig_v2/analysis/confirmatory_v2/`. It contains the receiver/seed tables, fixed inference, day/grouped analyses, composition audits, support and k sweeps, compute audits, five publication tables, supplementary receiver-by-seed results, nine PNG/PDF figures, quality/integrity reports, and the immutable analysis manifest.

Final test status: **PASS** — V2 304/304; root Paper 3 6/6; static-relational 19/19; metadata 84/84; dataset qualification 93/93; PR #84 WiSig 152/152; Paper 2 17/17. Python `compileall` and `git diff --check` passed. The legacy suites were invoked from their own discovery roots because a monolithic `tests/paper3` discovery does not satisfy their historical local-import layout.

Final analysis-manifest SHA-256: `a7489420a82e04bf4a14e34e2056f1428e235b2803c703a24637d7616a9fe796` (64 files, 6,704,149 bytes).
