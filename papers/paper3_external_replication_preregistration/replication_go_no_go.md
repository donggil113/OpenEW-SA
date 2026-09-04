# External replication GO/NO-GO decision

Status: **QUALIFICATION DECISION COMPLETE; SCIENTIFIC REPLICATION NOT STARTED**

## Current decision

| Path | Verdict | Reason |
|---|---|---|
| Existing public dataset | **NO-GO AS CURRENTLY RELEASED** | No inspected release satisfies independence, at least 12 physical receivers, explicit target-neutral calibration episodes, acquisition-disjoint query episodes, annotation separation, exact input/task compatibility, and licence/provenance together. |
| Public-data conversion/QA | **NOT AUTHORIZED** | No candidate passed the acquisition-episode gate; conversion would not cure missing acquisition semantics. |
| Prospective collection | **CONDITIONAL GO FOR COLLECTION AND QA** | The protocol is concrete and target-neutral, but no data exist yet. |
| P0/T3A/P2 training | **NOT AUTHORIZED** | Data, proxy, split, support, method-hash, and statistics gates are not yet instantiated and frozen. |
| Dynamic/temporal/hypergraph/neuro-symbolic modeling | **NO-GO** | Outside this replication and unsupported by the fixed methods. |

## Why public candidates fail

WiSig is not independent and lacks an acquired calibration episode. OSU
Bluetooth and OSU LoRa are the closest independent fingerprinting releases,
but they expose only two receivers and device-specific acquisition containers,
not target-neutral calibration/query episodes. POWDER, WIDEFT, INRIA PLA-AP,
and the NIST release lack the required multi-receiver episode structure.
OPERAnet has meaningful sessions and multiple sensors, but it changes the task
and input representation and therefore cannot replicate the frozen methods.

This negative qualification is not evidence that public RF datasets are poor;
it is evidence that they do not answer this narrowly preregistered question.

## Sequential authorization gates

All gates fail closed and are evaluated without target model results.

1. **Q0 — provenance/licence:** official source, version, citation, lawful
   research use, redistribution plan, and immutable raw hashes.
2. **Q1 — schema:** opaque IDs, physical receiver/hardware provenance, separate
   annotations, target-neutral paths, deterministic 256-IQ conversion.
3. **Q2 — episode:** explicit acquired calibration/query roles, open/close
   semantics, and capture/source-record disjointness.
4. **Q3 — safety:** label-permutation invariance, proxy/missingness/path audits,
   mixed calibration traffic, and annotation-free support construction.
5. **Q4 — split:** at least 12 LOSO receivers, source-validation separation,
   class support, identical method query IDs, and split hashes.
6. **Q5 — method:** merged V2 code ledger, exact P0/T3A/P2 procedures, support
   128, k 32, five fixed seeds, and clean committed adapter code.
7. **Q6 — statistics/blinding:** receiver-level estimands, three-comparison Holm
   family, 10,000 receiver bootstrap replicates, 100,000 sign flips, prediction
   blinding, and create-once unblinding manifest.

Training becomes authorized only when Q0--Q6 all pass in a committed review.

## Predeclared future scientific verdict

The future data-backed decision separates two questions.

### Receiver-calibration information

- **GO:** at least one same-information calibration method (T3A or P2) has a
  positive mean receiver-level difference from P0, a 95% receiver-bootstrap
  interval with lower bound above zero, a Holm-adjusted two-sided sign-flip
  result below 0.05, positive differences on a
  majority of receivers, and no integrity failure.
- **CONDITIONAL GO:** the mean is positive but uncertainty crosses zero or the
  effect is heterogeneous across receivers/campaigns.
- **NO-GO:** neither calibration method improves P0, or an integrity gate fails.

### P2 mechanism

- **GO:** P2 meets the calibration-information GO rule against P0 and also has
  a positive P2-minus-T3A mean, lower bootstrap bound above zero, Holm-adjusted
  sign-flip result below 0.05, and a majority of receivers positive for both
  comparisons.
- **CONDITIONAL GO:** P2 improves P0 reproducibly but does not establish an
  advantage over T3A, or the receiver/campaign pattern is heterogeneous.
- **NO-GO:** P2 does not improve P0 or is reproducibly inferior to T3A.

These rules are deliberately demanding because WiSig V2 already showed that a
context method can distinguish matched support yet fail to beat a simpler
same-information adapter.

## Current final verdict

**PUBLIC EXISTING-DATA REPLICATION: NO-GO.**

**PROSPECTIVE REPLICATION INFRASTRUCTURE: DESIGN-READY, DATA-NOT-READY.**

**NEXT MODEL EXPERIMENT: NOT AUTHORIZED.**

The next action is a target-neutral acquisition dry run followed by the full
12-receiver, two-campaign collection if the dry run passes. No WiSig V2 model,
split, prediction, or result is modified or rerun.
