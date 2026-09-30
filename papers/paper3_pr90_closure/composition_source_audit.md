# PR #90 composition-stress source audit

Status: **VERIFIED TABLE LINEAGE; POST-HOC ORACLE DIAGNOSTIC; NOT A DEPLOYABLE SUPPORT RULE**

## Frozen sources and checksum verification

The new table is derived from the frozen V2 primary receiver–seed CSV and the
frozen PR #87 composition CSV. The latter was independently reconciled against
its two frozen progenitors, the V2 P2 oracle CSV and the PR #87 T3A/RX-NORM
oracle CSV. All four files matched their own frozen analysis manifests before
aggregation.

| Source | SHA256 |
|---|---|
| V2 primary_receiver_seed_results.csv | 59e7f4ccabd9dbfc97a7a696a2cd711c1b0e9288ca1b3ca8e62a2c5571238890 |
| V2 composition_oracle_results.csv | 5b0fa8249a87e01c59652e7f6f23d60904d22d127c3049b4fc19141960324f73 |
| PR #87 analysis_composition_stress.csv | a192b131d8a40aa773915c9b2410655c29986043d6772c2b638729aa5d6e49cc |
| PR #87 tta_rxnorm_composition_receiver_seed_results.csv | f5aee6690988fd9edb1c64f01fe4db52208ece81c01084f0ff9088f55859c64a |

V2 manifest SHA256:
10ecae25fec123be839b11ea9c44334e41877dfa1eb261665c4d437870172d43.
PR #87 manifest SHA256:
62e9e7e3ee44a356f978841b3d599d6ece0d3e73bcb8c11a6bcc94672677c678.

Derived CSV and table hashes, plus the reconstructed query-set digest, are in
the create-once external
paper3/pr90_closure/20260928T110826Z/composition/composition_source_manifest.json.
No PR #87 or V2 source file was edited, and no new model inference was run.

## Aggregation and actual result

Each method/condition has 160 rows: 32 receivers by five frozen seeds. There
are no duplicate receiver/seed/method/condition keys, no missing receiver or
seed, and no nonfinite macro-F1 values. Five seed values are averaged within
each receiver, then the 32 receiver means are weighted equally. Query count
ranges from 3,962 to 4,672 per receiver–seed. Each condition evaluates
738,015 of 738,015 receiver–seed query records (100%). This count repeats
query observations across seeds; it is not a count of unique packets.

| Support condition | T3A macro-F1 | P2 | RX-NORM | Target label needed for support |
|---|---:|---:|---:|---|
| Natural | 0.833692 | 0.806726 | 0.800769 | No |
| Same class excluded | 0.338352 | 0.825916 | 0.784342 | Yes, query label |
| Same class only | 0.835474 | 0.608450 | 0.793608 | Yes, query label |
| Transmitter pure | 0.405748 | 0.763193 | 0.785748 | Yes, support labels |

The reviewer-supplied approximations for T3A correspond to receiver-equal
macro-F1 from these frozen rows. EMB-STD and SAR-GN were **NOT EVALUATED** under
the oracle composition conditions; no result was imputed.

## Query and information contract

The original P2 and PR #87 TTA oracle code both call the same frozen,
label-free support/query constructor with support budget 128 and the frozen
receiver LOSO split. The derivation checked all 480 natural P2, T3A and
RX-NORM prediction archives against independently reconstructed ordered query
sample IDs: 480/480 exact matches across 160 receiver–seed query sets. Query
counts agree at each receiver–seed across methods and conditions. The original
oracle CSVs store query counts but no per-query ID arrays, so archived oracle
query IDs cannot be directly compared byte-for-byte; the frozen code path and
full count agreement establish the available lineage. The source code is
src/openew/paper3/wisig_v2/diagnostics.py and
src/openew/paper3/v2_addendum/composition.py; the new read-only derivation is
scripts/paper3/pr90_closure/build_composition_evidence.py.

Natural T3A and RX-NORM use the complete 128-packet support bank. Natural P2
draws 32 peers from the bank. The oracle conditions derive their support from
the same frozen bank but select at most 32 peers; some same-class-only and
transmitter-pure selections have fewer. The minimum mean peer count for a
transmitter-pure receiver–seed record is 1. Consequently a natural-versus-
oracle difference for T3A or RX-NORM changes support quantity as well as class
composition. The table is a sensitivity diagnostic, not a causal estimate of
composition in isolation.

Same-class-excluded and same-class-only require each query's true
transmitter identity. Transmitter-pure selects one target class using support
annotations and a frozen hash. These three policies are nondeployable. None
was used to select support for the deployable benchmark. The result does not
change the frozen V2 or PR #90 decisions.

## Manuscript placement and checks

The source-backed table is now input by the actual PR #90 shared manuscript
body at tables/composition_oracle.tex, in the Results section, with the exact
caption **POST-HOC ORACLE COMPOSITION DIAGNOSTIC**. The companion supplement
identifies each frozen source and records the query-alignment limitation.
PDF page placement and visual fit must be confirmed after the root task's
fresh main/supplement build; a TeX edit alone is not the final PDF verification.
Nine focused source/grain tests passed locally. The full regression result
belongs to the final parent task gate.
