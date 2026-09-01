# Paper 3 Relational Feasibility Report

Audit date: 2026-09-01

## Executive decision

| Scope | Verdict |
| --- | --- |
| JamShield | **CONDITIONAL GO** |
| DeepSense | **NO-GO** |
| ElectroSense | **CONDITIONAL GO** |
| Static hypergraph | **CONDITIONAL GO** |
| Dynamic hypergraph | **NO-GO** |
| Uncertainty-aware gating | **PREMATURE** |
| Neuro-symbolic component | **PREMATURE** |

The audit does not support calling the next Paper 3 model dynamic. The evidence supports a narrower feasibility experiment in **Relational Domain Generalization for RF Situation Assessment** using static, typed, inference-available relations on JamShield and ElectroSense. DeepSense should remain an independent-sample baseline/negative control unless a new leakage-safe mixed-label sequence artifact is independently verified; no new data were downloaded in this phase.

## Decision criteria

### VERIFIED FACT

Two datasets have meaningful, fully covered, inference-plausible relational metadata:

- JamShield: one station equality field (`rx_id`), seven groups, 100% coverage.
- ElectroSense: receiver equality and coarse acquisition-date grouping, 100% coverage.

All relations can be constructed without target or OOD labels under the hard whitelist. Existing Paper 1 scenario/reactive-family, day2, and sensor holdouts can be preserved. However, no dataset has a defensible leakage-safe temporal sequence under the current task and artifact schema.

## Dataset decisions

### JamShield — CONDITIONAL GO

**VERIFIED FACT:** Raw station identity is present on all 92,486 rows. The source `sample` counter is monotonic within each of the 20 CSVs, but each CSV/domain is target-pure and its name identifies benign or jammer context. There is no documented timestamp or independent session ID.

**INFERENCE:** A static station hyperedge is defensible because station identity is acquisition-time metadata. Its effect may include station-specific shortcuts: five stations are mixed-label and two are single-target in the frozen rows.

**CONDITION:** Use only equality relations from `rx_id`, preserve the original holdouts, prohibit scenario/file identity, and report station-removal and relation-corruption results.

### DeepSense — NO-GO

**VERIFIED FACT:** The data have true within-file signal order, but all 32 files are target-pure occupancy captures. `time_index` repeats 0--999 in each file; the safe metadata contain one receiver, one band descriptor, and split-only day. File names begin with the target occupancy string.

**INFERENCE:** Any capture/session or within-capture temporal edge would reproduce same-class grouping created by the data collection design. Calling day1/day2 alone dynamic would be scientifically misleading.

**DECISION:** Do not construct a Paper 3 graph/hypergraph for DeepSense from the current artifact. Retain M0 as a cross-day reference only.

### ElectroSense — CONDITIONAL GO

**VERIFIED FACT:** Receiver identity (40 groups) and coarse source date (19 groups) cover all 45,750 rows and are not target-pure. Frequency band (125 values), source capture (229 values), and derived band bounds/centers are target-pure or near-exact proxies. No exact timestamp or cross-file order is available.

**INFERENCE:** Receiver, date, and joint receiver-date hyperedges support static relational learning under the existing sensor holdout. Date tokens are coarse and may represent collection campaigns rather than a general time variable.

**CONDITION:** Prohibit frequency/capture/path relations, preserve sensor holdout, report receiver/date ablations, and treat date edges as static.

## Overall decisions

### Static hypergraph — CONDITIONAL GO

The minimum suggested GO criterion of two datasets with fully covered, inference-plausible relations is met narrowly by JamShield and ElectroSense. Relation diversity is limited, and graph batches must not cross train/validation/test boundaries. The first experiment should therefore compare M0/M1/M2 only and require a positive validation-supported relational benefit before expanding scope.

### Dynamic hypergraph — NO-GO

No dataset supplies a safe combination of timestamp/order and target-independent session identity. DeepSense order is nested in class-pure files; JamShield order is nested in scenario/target-pure files; ElectroSense order is nested in technology/band-pure files and lacks a clock. “Dynamic” should not appear in the next paper title or primary claim under current evidence.

### Uncertainty-aware gating — PREMATURE

Paper 2 establishes uncertainty/OOD context, but the feasibility phase has not shown that a static relational model improves unseen-domain macro-F1. Gating should be tested only after M2 is frozen and only with train/validation-fitted uncertainty, never target-OOD labels.

### Neuro-symbolic component — PREMATURE

No defensible symbolic rule was found that is both deployment-available and independent of ground-truth labels. Spectrum-band-to-technology rules would simply re-encode an exact target proxy in ElectroSense. A neuro-symbolic claim would be premature.

## UNRESOLVED

1. Whether JamShield `sample` has a physical time interval rather than being only a row identifier.
2. Whether ElectroSense source arrays retain calibrated temporal spacing and whether date tokens include omitted year/time metadata upstream.
3. Whether a future artifact can expose target-independent capture/session identifiers without class-bearing filenames.
4. How deployment episodes/batches will be defined without using held-out-domain labels.
