# Paper 3 Relational Metadata Specification

## VERIFIED FACTS

Only three nonconstant field uses survive the current hard whitelist: JamShield `rx_id`, ElectroSense `rx_id`, and ElectroSense `source_date_id`. Coverage is 100% for each. DeepSense has no allowed nonconstant relation.

Observed group cardinalities are:

- JamShield station groups: 7 groups; 1,533--24,823 nodes per group; mean 13,212.286.
- ElectroSense receiver groups: 40 groups; 400--4,800 nodes; mean 1,143.750.
- ElectroSense date groups: 19 groups; 400--15,000 nodes; mean 2,407.895.
- ElectroSense receiver-date groups: 45 groups; 400--1,800 nodes; mean 1,016.667.

Large hyperedges must be sampled or pooled deterministically using training/validation-fixed limits; an implementation must not use target labels to trim them.

## PROPOSED STATIC SCHEMAS

### JamShield `station_edge`

| Property | Specification |
| --- | --- |
| Name | `station_edge` |
| Source field(s) | `rx_id` (raw source field `station`) |
| Meaning | Observations reported for the same Wi-Fi station/endpoint |
| Availability at inference | Plausibly yes; station MAC is collected with each row |
| Expected node cardinality | 1,533--24,823 per station in the frozen data |
| Estimated coverage | 92,486/92,486 = 1.000000 |
| Leakage risk | Medium: two of seven station groups are single-target in the frozen rows; station purity must be monitored |
| Static vs dynamic | Static |
| Status | VERIFIED metadata availability; PROPOSED hyperedge |

This edge must not be combined with `domain_id`, source file, benign/jammer family, or raw filename. The source README calls the field a transmitting station, so the paper should not overstate it as a verified receiver entity.

### ElectroSense `receiver_edge`

| Property | Specification |
| --- | --- |
| Name | `receiver_edge` |
| Source field(s) | `rx_id` |
| Meaning | PSD rows acquired by the same ElectroSense sensor/receiver |
| Availability at inference | Yes; receiver identity is known to the acquisition system |
| Expected node cardinality | 400--4,800 per receiver |
| Estimated coverage | 45,750/45,750 = 1.000000 |
| Leakage risk | Low-to-medium shortcut risk; all receivers are multi-class, target purity 0.248087 versus 0.195628 majority baseline |
| Static vs dynamic | Static |
| Status | VERIFIED metadata availability; PROPOSED hyperedge |

The sensor holdout remains unchanged. Equality grouping can operate for an unseen receiver without learning its categorical identity; a learned receiver-ID embedding is not implied.

### ElectroSense `acquisition_date_edge`

| Property | Specification |
| --- | --- |
| Name | `acquisition_date_edge` |
| Source field(s) | `source_date_id`, reconstructed from ordered `labels.json:source_files` descriptors and row counts |
| Meaning | Measurements stored under the same coarse acquisition-date folder |
| Availability at inference | Plausibly yes at collection time |
| Expected node cardinality | 400--15,000 per date token |
| Estimated coverage | 45,750/45,750 = 1.000000 |
| Leakage risk | Medium; date is not target-pure but lacks year/time-of-day and may encode collection campaigns |
| Static vs dynamic | Static only |
| Status | VERIFIED reconstructability; PROPOSED hyperedge |

### ElectroSense `receiver_date_edge`

| Property | Specification |
| --- | --- |
| Name | `receiver_date_edge` |
| Source field(s) | `rx_id` + `source_date_id` |
| Meaning | Same receiver on the same coarse acquisition date |
| Availability at inference | Plausibly yes |
| Expected node cardinality | 400--1,800 per joint group |
| Estimated coverage | 45,750/45,750 = 1.000000 |
| Leakage risk | Medium; avoids global date mixing but remains campaign-specific |
| Static vs dynamic | Static |
| Status | VERIFIED component fields; PROPOSED joint hyperedge |

## REJECTED OR UNRESOLVED SCHEMAS

| Candidate | Dataset(s) | Decision | Evidence |
| --- | --- | --- | --- |
| `frequency_band_edge` / band-overlap edge | ElectroSense | FORBIDDEN | All 125 bands are target-pure; lower/upper/center remain near-exact or exact target proxies. |
| `capture_session_edge` | All | FORBIDDEN | Every reconstructed source file/capture is target-pure; paths encode class or jammer context. |
| `temporal_neighbor_edge` | JamShield | UNRESOLVED, do not implement | Counter is monotonic inside a target-pure scenario file; no timestamp or safe session key. |
| `temporal_neighbor_edge` | DeepSense | FORBIDDEN for current task | True window order exists only inside one occupancy-class capture. |
| `temporal_neighbor_edge` | ElectroSense | UNRESOLVED, do not implement | Row order is local to a target-pure band/technology file; no exact timestamp or cross-file order. |
| `site_edge` | ElectroSense | UNRESOLVED | Receiver names exist, but independent site/location metadata are absent. |
| `same_day_edge` | DeepSense | SPLIT-ONLY | Day is exactly the held-out domain definition. |
| same-class/same-OOD edge | All | FORBIDDEN | Direct target leakage. |

## INFERENCE

The current evidence supports metadata-conditioned static relational learning on JamShield and ElectroSense, not a dynamic hypergraph claim. Feature-similarity pairwise graphs may be evaluated as an M1 comparator if the distance metric, scaling, and neighbor count are fitted on training/validation data only, but they are not verified metadata relations.
