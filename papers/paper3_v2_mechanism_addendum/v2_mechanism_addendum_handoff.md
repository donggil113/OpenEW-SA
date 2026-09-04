# WiSig V2 post-hoc mechanism-addendum handoff

Status: **COMPLETE — POST-HOC MECHANISTIC EVIDENCE ONLY**

This addendum does not modify the frozen PR #85 primary result, its
`CONDITIONAL_GO` mechanism classification, or its `NOT_READY` publication
decision. It adds no confirmatory comparison and does not support temporal,
dynamic, graph, hypergraph, or neuro-symbolic claims.

## VERIFIED RESULT — execution and evidence boundary

The addendum preregistration was committed before any addendum metric was
opened. The only newly trained condition used the exact frozen V2 P2
architecture, optimizer, epoch limit, patience, source-validation selection,
32 receiver LOSO protocols, and five seeds. Its sole declared change was
label-free shuffling of source-training context donors across source receivers.
All 160 source models completed with zero failures and yielded 480 fixed
evaluations: natural receiver support, shuffled support, and null support.

The complete external analysis contains 480 query-coupling rows, 1,600
support-budget rows, 1,440 composition-stress rows, and 480 shuffled-training
evaluation rows. The create-once analysis manifest covers 23 files and has
aggregate SHA-256
`cf015dc36cffdd948d989c62c67e225786cb6b8d85c3854e4304130f76924790`.

The final integrity gate passed. The WiSig raw archive, two raw conversion
manifests, and frozen V2 analysis manifest retained their expected hashes.
Paper 1, Paper 2, and PR #80--#86 Git paths were unchanged. Although workers
recorded three documentation-era Git SHAs, the four executable method files
were byte-identical at all three revisions. No Shen payload or Shen model run
exists, and no frozen V2 output was overwritten.

## VERIFIED RESULT — query-coupling diagnostic

| Inference access | Equal-weight receiver macro-F1 | Delta from disjoint |
|---|---:|---:|
| Frozen disjoint natural support/query | 0.806726 | reference |
| PR #84-style query-coupled hash chunk | 0.806848 | +0.000122 |
| Full receiver-partition upper diagnostic | 0.809951 | +0.003225 |

The chunk-minus-disjoint receiver bootstrap interval was
`[-0.000732, 0.000990]`, with 16/32 receivers positive. The full-partition
upper diagnostic interval was `[0.002324, 0.004158]`, with 28/32 receivers
positive. A PR #84-style chunk therefore produces essentially no change in
this V2 checkpoint/split diagnostic, while nondeployment access to the entire
receiver partition yields a small increase. This does not reconstruct PR #84
and cannot identify every cause of the V1/V2 difference.

## VERIFIED RESULT — shuffled-context source training

| Test support supplied to shuffled-trained P2 | Macro-F1 |
|---|---:|
| Natural same-receiver support | 0.794149 |
| Shuffled support | 0.786987 |
| Null support | 0.782946 |

Natural-minus-shuffled was `+0.007162`, receiver-bootstrap interval
`[0.004879, 0.009776]`, with 29/32 receivers positive. Natural-minus-null was
`+0.011203`, interval `[0.006737, 0.016062]`, with 28/32 positive. Thus the
architecture remains sensitive to matched receiver information even after
label-free shuffled-context source training. However, its natural-support
macro-F1 remains below both frozen P0 (`0.805679`) and frozen original P2
(`0.806726`). This is mechanistic sensitivity, not a performance success.

## VERIFIED RESULT — composition diagnostics

The deployable natural-support references remain P2 `0.806726`, T3A
`0.833692`, and RX-NORM `0.800769`. The following label-dependent conditions
are **ORACLE DIAGNOSTICS ONLY**:

| Method | Same class excluded | Same class only | Transmitter pure |
|---|---:|---:|---:|
| P2 | 0.825916 | 0.608450 | 0.763193 |
| T3A | 0.338352 | 0.835474 | 0.405748 |
| RX-NORM | 0.784342 | 0.793608 | 0.785748 |

Composition sensitivity is not unique to P2. T3A is strongest with natural
and same-class-only support but collapses when the query class is excluded and
under transmitter-pure support. P2 improves when the query class is excluded
but is strongly harmed by same-class-only support. RX-NORM is comparatively
stable. These oracle outcomes cannot be promoted to deployable methods or
used to redesign support.

## VERIFIED RESULT — support-budget efficiency

| Unlabeled support packets | P2 | T3A |
|---:|---:|---:|
| 16 | 0.803529 | 0.719644 |
| 32 | 0.806289 | 0.795558 |
| 64 | 0.806618 | 0.822783 |
| 128 | 0.806712 | 0.833617 |
| 256 | 0.806788 | 0.838273 |

P2 is nearly flat across budgets. T3A is poor with 16 packets, crosses P2
between 32 and 64, and increases through 256. The frozen 128-packet reference
is unchanged; no target-best budget is selected.

## VERIFIED RESULT — hardware and equalization

Frozen hardware-family summaries remain descriptive. P2-minus-P0 family means
were `-0.001337` (B210), `-0.000010` (N210), and `+0.004782` (X310). T3A-minus-
P0 means were `+0.032419`, `+0.025349`, and `+0.029325`, respectively. P2 was
below T3A in every family mean.

The raw conversion contains 249,666 sample IDs; both equalized passes contain
247,684 identical IDs, but their exact opaque-ID intersection with raw is zero.
The preregistered matched-intersection gate therefore returned `INELIGIBLE`.
No equalized model diagnostic was run.

## POST-HOC INTERPRETATION

The addendum narrows, rather than reverses, V2. Same-receiver support produces
repeatable changes inside P2 relative to broken/absent support, and the
PR #84-style query-coupling approximation is not a material inflation source
under V2. Yet P2 remains approximately equal to P0, its shuffled-trained
variant is worse than P0, and T3A remains the best same-information method at
the primary support budget. Receiver support matters, but method choice matters
more in these data.

## LIMITATIONS / UNRESOLVED

- All addendum evidence is post-hoc and uses the same WiSig dataset as V2.
- WiSig still lacks a verified target-neutral acquired calibration episode.
- The full-partition condition is transductive and nondeployment.
- Oracle composition conditions use labels and are nondeployable.
- Exact raw/equalized sample matching is unavailable under the frozen opaque
  identifiers; inventing a retrospective mapping would violate the gate.
- No independent external replication was possible in this workstream.

The external evidence package is
`/mnt/d/openew_sa_data/paper3/v2_addendum/`; generated checkpoints,
predictions, tables, and figures remain outside Git.
