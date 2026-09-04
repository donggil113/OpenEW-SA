# External receiver-calibration replication requirements

Status: **FROZEN BEFORE NEW-DATA ACCESS, CONVERSION, OR TARGET RESULTS**

## Technical summary

The replication asks whether receiver-specific unlabeled calibration improves
RF transmitter identification on a dataset independent of WiSig, and whether
the frozen attentive context method P2 improves on the frozen same-information
T3A baseline. The merged WiSig V2 evidence is prior evidence only: P2 was
approximately equal to P0, distinguished real receiver support from shuffled
and mismatched support, and was clearly worse than T3A. This workstream cannot
tune P2 in response.

| Frozen WiSig V2 quantity | Receiver-level macro-F1 / delta |
|---|---:|
| P0 | 0.805679 |
| P2 | 0.806726 |
| T3A | 0.833692 |
| P2 minus P0 | +0.001047 |
| P2 minus P2-SHUFFLED | +0.018364 |
| P2 minus P2-MISMATCHED-RX | +0.019637 |
| P2 minus T3A | -0.026966 |

These values and the V2 publication-readiness verdict `NOT_READY` are frozen
at PR #85 merge commit `48cec06645736bd45c455a64841f3f50e0368b40`.

No examined public release currently satisfies every mandatory requirement.
The public-data path is therefore **NO-GO AS RELEASED**. A prospectively
collected dataset is the active design path, but training remains unauthorized
until its acquired metadata and samples pass every gate below.

## Primary question

> Does receiver-specific unlabeled calibration information provide
> reproducible benefit on an independent dataset, and does the frozen P2
> attentive receiver-context method provide any advantage over the frozen
> same-information T3A method?

The evaluation protocol is an unseen-receiver domain-shift protocol. P2 is a
test-time receiver-context method and T3A is test-time adaptation; neither is
described as pure source-only domain generalization.

## Mandatory dataset gates

| Gate | Required evidence | Failure consequence |
|---|---|---|
| Independence | No sample, receiver, transmitter, capture, or derived signal from WiSig | Dataset rejected |
| Physical receivers | At least 12 independently identifiable receiver units for the confirmatory receiver-level analysis | Dataset may support engineering QA only, not confirmatory replication |
| Receiver identity | Opaque physical-unit ID with field-level provenance | Dataset rejected |
| Calibration episodes | Explicit receiver-specific episode IDs and open/close semantics declared during acquisition | Dataset rejected |
| Query episodes | Query captures are separate acquisition events, not a hash split of one recording | Dataset rejected |
| Acquisition disjointness | No raw capture, packet, window, or source record appears in both calibration and query | Dataset rejected |
| Annotation separation | Transmitter labels reside in a separate object and can be withheld from support/context construction | Dataset rejected |
| Label-free support | The 128-packet support bank is chosen using only seed, receiver ID, episode eligibility, and opaque sample ID | Dataset rejected |
| Target-neutral storage | No class, transmitter, attack, occupancy, or split token is model-visible through paths, IDs, or metadata | Dataset rejected or quarantined pending a clean conversion |
| Signal compatibility | Deterministic, label-independent conversion to 256 complex samples represented as `[256, 2]` real/imaginary values | Dataset rejected for exact-method transfer |
| Target task | Closed-set physical transmitter/device identification with the same eligible class set across receiver protocols | Dataset rejected for this replication |
| Support | At least 128 valid calibration packets per receiver and adequate preregistered query support for every eligible class | Dataset rejected |
| Receiver holdout | Every qualified receiver can serve once as an unseen test receiver while source-train and source-validation receivers remain distinct | Dataset rejected |
| Hardware provenance | Receiver hardware family recorded; at least two families is strongly preferred and required for a cross-family secondary claim | Missing family prevents hardware-stratified claims but not the receiver-only primary claim |
| Licence and provenance | Official source, version, citation, licence, access terms, immutable hashes, and lawful research use | Dataset rejected |

The threshold of 12 receivers is a design requirement for this confirmatory
workstream, not a claim of statistical power. It provides 12 independent
receiver units for receiver-level paired inference; packet count cannot replace
missing receiver units.

## Mandatory structural QA

Before split freezing, a candidate must pass all of the following without
consulting model performance:

1. acquisition and annotation tables have unique, matching opaque sample IDs;
2. calibration and query source-capture hashes are disjoint;
3. receiver, capture, episode, campaign, and hardware provenance is complete;
4. support IDs are invariant to label permutation;
5. support construction succeeds with annotations physically unavailable;
6. path-token and metadata proxy audits find no model-visible target proxy;
7. calibration episodes contain operationally mixed traffic and are not
   target-pure by acquisition design;
8. all eligible transmitter classes meet the predeclared split-support rules;
9. conversion is deterministic across two passes; and
10. no test receiver or query record enters source training or validation.

Labels may be joined only inside a quarantined safety audit and for documented
class-support feasibility. They may not select support members, transformations,
receivers, hyperparameters, or methods.

## Allowed and forbidden information

Model-visible input is limited to the complex RF window. `receiver_id` is used
only to address the calibration bank and is not embedded. Calibration episode
role, query episode role, hardware family, campaign, site, and split ID are
split/audit metadata. Transmitter identity is annotation-only.

Forbidden inputs include transmitter/class labels, target-bearing path tokens,
same-class grouping, query predictions, correctness, confidence, OOD status,
target performance, day/campaign embeddings, receiver-value embeddings, and
query-query context.

## Authorization boundary

Passing this document is necessary but not sufficient. Training is authorized
only after the selected dataset, conversion QA, target-proxy audit, split
manifest, method hashes, support/query manifest, and statistical protocol are
committed and independently reviewable. Current authorization: **NO TRAINING**.
