# External replication split protocol

Status: **FROZEN BEFORE DATA COLLECTION/CONVERSION AND TARGET RESULTS**

## Primary domain protocol

The primary design is leave-one-physical-receiver-out (LOSO). A qualified
dataset must provide at least 12 receiver units. Each receiver serves exactly
once as the held-out test receiver. Within a protocol:

- one receiver is test;
- three non-test receivers are source validation; and
- every remaining receiver is source training.

Source-validation receivers are chosen deterministically from opaque receiver
IDs, receiver hardware family, and preregistered sample/class-support counts.
Model performance is forbidden. Where hardware metadata permit, the three
validation receivers cover the available source hardware families. A mapping
file and SHA-256 are committed before any target prediction.

## Calibration and query roles

Every receiver/campaign has acquisition-designated calibration and query
episodes. Their raw captures are disjoint. For the held-out receiver:

- calibration samples are unlabeled to every method and provide the fixed
  128-packet bank to T3A and P2;
- query samples are never used as support or adaptation input; and
- query annotations are withheld until all predictions are frozen.

P0 is evaluated on the identical query IDs but ignores the calibration bank.
T3A and P2 receive exactly the same 128 support IDs. P2 uses at most 32 of them
per query. No method receives day, campaign, site, hardware, or receiver value
as a learned input.

## Source roles

Source-training annotations may train P0 and P2. Source-validation receiver
episodes simulate the full calibration/query procedure for early stopping and
T3A `filter_K` selection. A source-validation receiver is not part of source
training in the same LOSO protocol. Test receiver records never enter either
source role.

## Class eligibility

Labels may be used once for split feasibility, not for support selection or
performance tuning. The eligible transmitter set is the intersection meeting
all of the following in every LOSO protocol:

- at least 100 labeled source-training query packets per class;
- at least 20 labeled source-validation query packets per class;
- at least 20 held-out query packets per class; and
- at least 128 total unlabeled, QA-passing held-out calibration packets.

The eligible set and counts are frozen before model execution. Classes are not
removed after results. Calibration class balance is not an eligibility rule;
its composition is audited only after support IDs are fixed.

## Campaign handling

The prospective design contains two independently opened campaigns. The same
LOSO mapping is applied to both. A method is applied separately to each
receiver/campaign calibration bank and query episode. Campaign outcomes are
averaged within receiver before the receiver-level primary analysis, so the
receiver—not packet, campaign, or seed—remains the inferential unit.

If a public dataset exposes only one qualifying campaign, it may pass the
minimum external split gate but cannot support the campaign-repeat robustness
claim. It must still meet every receiver/episode/disjointness requirement.

## Non-overlap audit

Before execution, verify and hash:

1. unique `sample_id` values;
2. no source-record or derived-window overlap across train, validation, and
   test;
3. no receiver overlap across roles within a protocol;
4. no capture or acquisition session split across roles;
5. no calibration/query capture overlap;
6. identical query IDs for P0, T3A, and P2;
7. identical support IDs for T3A and P2;
8. no annotation column or target-bearing path in a model manifest; and
9. deterministic reconstruction from the frozen source and seed.

Any failure stops the complete experiment suite. It is not repaired by dropping
a receiver, seed, class, or packet after target results.

## Secondary analyses

Hardware-family and campaign effects are descriptive/robustness analyses. A
cross-family statement is allowed only when at least two verified receiver
hardware families have multiple held-out receiver units. There is no day,
temporal, dynamic, graph, hypergraph, or neuro-symbolic analysis in this
replication.
