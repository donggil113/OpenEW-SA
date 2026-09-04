# Receiver-calibration episode contract

Status: **FROZEN BEFORE COLLECTION OR TARGET RESULTS**

## Definition

A receiver-calibration episode is a bounded acquisition interval opened for
unlabeled receiver calibration before query acquisition. Its boundary is an
operational fact, not a class boundary or a row grouping invented after data
collection. Every episode has an opaque `calibration_episode_id`, one physical
`receiver_id`, one `campaign_id`, declared clock/reset semantics, and one or
more immutable raw captures.

A query episode is a later or separately triggered acquisition interval from
the same receiver/campaign. Calibration and query episodes are disjoint by raw
capture, source record, packet, and derived window. A query packet is never a
support packet for any query.

## Required acquisition fields

| Field | Role | Model-visible? | Constraint |
|---|---|---:|---|
| `sample_id` | Opaque join identity | Addressing only | Target-neutral and immutable |
| `receiver_id` | Physical receiver identity | Addressing only | No learned value embedding |
| `campaign_id` | Acquisition campaign | No | Split/audit only |
| `acquisition_session_id` | Session boundary | No | Target-neutral open/close rule |
| `calibration_episode_id` | Calibration bank boundary | No | Present only for calibration records |
| `query_episode_id` | Evaluation boundary | No | Present only for query records |
| `capture_id` | Raw-capture boundary | No | Cannot cross calibration/query or split roles |
| `source_record_index` | Physical source order | No | Nonnegative and unique within capture |
| clock/reset fields | Provenance and order QA | No | Missing values explicitly flagged |
| RF settings | Conversion provenance | No, except the complex window itself | Consistent with frozen converter rule |

`transmitter_id` and all semantic labels live only in the annotation table.
They are not accepted by episode/support APIs.

## Primary support rule

For every held-out receiver and seed, the eligible set is all QA-passing samples
from the receiver's preregistered calibration episode or episodes in the
evaluated campaign. Rank candidates with the existing V2 stable SHA-256
primitive using `(seed, receiver_id, sample_id)` and namespace
`wisig-v2-support`. Select the first **128**. The selected IDs are frozen before
annotations are made available to the audit process.

The primary P2 context for each query contains at most **32** peers from that
fixed bank. Peer ranking uses the existing V2 tuple
`(seed, receiver_id, query_sample_id, support_sample_id)` and namespace
`wisig-v2-query-context`. The query anchor is excluded. No support-budget or
context-k sweep is authorized in the replication.

If a receiver/campaign has fewer than 128 valid calibration packets, it fails
the confirmatory gate. The budget is not reduced to rescue the dataset. Extra
calibration packets remain unused except for QA; target labels cannot choose
which 128 are retained.

## Acquisition-disjointness requirements

- Calibration and query must have different episode IDs and capture IDs.
- A raw packet key and any of its derived windows belong to exactly one role.
- Duplicate waveform hashes across roles are investigated; deterministic
  retransmissions are not silently treated as independent.
- Calibration is complete before query inference starts.
- Query collection cannot alter the frozen support bank.
- Support banks are receiver- and campaign-local; they never cross a receiver,
  campaign, source-validation, or test boundary.

## Label-free invariance tests

Before training authorization, the future implementation must demonstrate:

1. permuting annotation rows or transmitter labels leaves support IDs unchanged;
2. deleting the annotation file leaves episode and support construction usable;
3. changing query labels leaves all peer matrices unchanged;
4. no target token appears in the acquisition table, raw relative path exposed
   to the model, sample ID, episode ID, or support manifest; and
5. identical input manifests and seed yield byte-identical support/query IDs.

## Post-freeze audit only

After support IDs are immutable, a quarantined audit may join labels to compute
class count, entropy, majority fraction, same-class presence, purity, mutual
information diagnostics, and missingness association. These values cannot
rebuild support. A calibration episode that is target-pure by design fails; a
chance realization with low diversity is reported and retained unless it trips
a threshold frozen before collection.

## What this contract does not claim

Episodes are not temporal sequences for model input. P2 is permutation
invariant and receives no timestamp or position. The contract establishes a
deployment-plausible calibration event and disjoint query event; it does not
authorize dynamic, temporal, graph, hypergraph, or neuro-symbolic claims.
