# Technical appendix: completed static-relational negative pilot

## Why it was run

PR #80 found only coarse equality metadata: JamShield station and ElectroSense
receiver/date. PR #81 therefore tested whether those deployment-plausible,
label-independent equality groups improved frozen Paper 1 domain holdouts.
DeepSense remained an independent M0 reference. This appendix records the
negative evidence without presenting it as publication novelty.

## Frozen design

The whitelist was JamShield `rx_id`; ElectroSense `rx_id` and
`source_date_id`; DeepSense none. `domain_id`, labels, OOD, frequency, paths,
target-pure scenario/capture identities, predictions, and correctness were
forbidden. Relations never crossed partitions and relation values were not
embedded.

The 140-run suite comprised 50 primary M0/M1/M2 runs, 15 shuffled-relation
controls, 60 additional non-100% retention runs, and 15 ElectroSense component
ablations. Five paired seeds were fixed: 829, 1829, 2829, 3829, and 4829.

## Headline results

Five-seed held-out macro-F1 means (sample standard deviation in parentheses):

| Protocol | M0 | M1 | M2 | M2 − M0 |
|---|---:|---:|---:|---:|
| JamShield scenario | 0.555165 (0.075781) | 0.480810 (0.028689) | 0.476876 (0.040576) | -0.078289 |
| JamShield reactive family | 0.682252 (0.043125) | 0.659341 (0.040645) | 0.662984 (0.040606) | -0.019267 |
| ElectroSense sensor | 0.452858 (0.033506) | 0.450970 (0.028290) | 0.446144 (0.045065) | -0.006714 |
| DeepSense cross-day | 0.217815 (0.000767) | not run | not run | not applicable |

M2-minus-M0 source-validation changes were -0.003094, -0.003336, and
+0.004292 for JamShield scenario, JamShield reactive, and ElectroSense.

## Shuffled relation and corruption evidence

Actual-minus-shuffled held-out M2 was -0.018510, -0.039320, and +0.001947.
None cleared the frozen +0.005 margin on both source validation and held-out
data. Hence the relation-specific mechanism criterion failed across protocols.

Held-out M2 means at 0%, 25%, 50%, 75%, and 100% relation retention were:

- JamShield scenario: 0.568432, 0.598605, 0.614393, 0.536988, 0.476876.
- JamShield reactive: 0.704566, 0.706112, 0.679284, 0.680369, 0.662984.
- ElectroSense: 0.450806, 0.458260, 0.442196, 0.465086, 0.446144.

No retention level or favorable component was selected. Full station retention
was harmful on source validation; ElectroSense's orderly source dependence did
not yield a relation-specific held-out gain.

## Decision and lesson

JamShield scenario: NO-GO. JamShield reactive: NO-GO. ElectroSense: at most
CONDITIONAL GO. Overall static-relational hypothesis: **NO-GO**. M3 dynamic,
M4 uncertainty gating, and M5 symbolic reasoning were not started.

The result shows that coverage and efficient typed aggregation do not establish
useful relational information. Prospective data must preserve target-neutral
sessions, clocks, order, receiver/site, frequency, and provenance before another
relational experiment is justified.

The frozen suite completed 140/140 runs; prediction reconciliation and pre/post
artifact hashes passed. Paper 1 and Paper 2 remained unchanged.
