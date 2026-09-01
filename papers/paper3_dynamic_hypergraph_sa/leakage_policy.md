# Paper 3 Relation Leakage Policy

This policy applies to all future Paper 3 graph and hypergraph construction. The executable contract is in `src/openew/paper3/relational_audit.py`; the configured whitelist is in `configs/paper3/relational_feasibility_audit.yaml`.

## Classes

- **A. ALLOWED MODEL RELATION**: plausibly available at acquisition/inference time, explicitly whitelisted, and not a target or forbidden holdout proxy.
- **B. SPLIT-ONLY**: valid for constructing the frozen train/validation/test protocol, forbidden to graph construction and model inputs.
- **C. DIAGNOSTIC-ONLY**: usable for alignment, provenance, or audit but not graph construction.
- **D. FORBIDDEN / TARGET LEAKAGE**: target, target-derived value, correctness/OOD value, target-bearing source identifier, or empirically exact target proxy.
- **E. UNRESOLVED**: semantics or deployment availability are insufficiently established. Treat as forbidden until resolved and reviewed.

## Global rules

### VERIFIED FACT

The graph contract rejects label, OOD, target, correctness, and ground-truth patterns before whitelist validation. A configured whitelist may narrow the reviewed whitelist but cannot expand it. The frozen reviewed whitelist is:

```yaml
jamshield: [rx_id]
deepsense: []
electrosense: [rx_id, source_date_id]
```

`domain_id` is never a model relation. Source filenames, capture IDs, source paths, labels, OOD flags, split names, test correctness, and performance-derived fields are never permitted. Relation selection and all preprocessing must be fitted or fixed without target-domain labels.

The audit reports weighted target purity, majority-class baseline, single-target group fraction, target tokens in values, coverage, and cardinality. These are diagnostic flags: a field is not declared safe merely because its name lacks `label`.

## JamShield classification

| Field | Class | Reason |
| --- | --- | --- |
| `rx_id` (raw `station`) | **A** | Acquisition-time endpoint identity, seven values and 100% coverage. Two values are single-target in the frozen sample, so shortcut monitoring is mandatory. |
| `domain_id` | **B** | Defines Paper 1/Paper 2 scenario/family holdouts; stems encode benign/jammer types and are 100% target-pure. |
| `time_index` / raw `sample` | **E** | Monotonic within a file, but no documented timestamp; safe temporal use requires a source-file session that is target-pure. |
| `frequency_band` | **C** | Constant placeholder `wifi_unknown`; no relational content. |
| source file/capture/path | **D** | Every file is target-pure and the name identifies benign/jammer scenario. |
| benign/jammer grouping | **D** | It is the recognition target, not independent operational context. |
| `abnormal_event_label`, `situation_label`, `threat_level`, `human_review_required` | **D** | Ground truth or deterministically target-derived. |
| 37 RF/network metrics | **C for metadata audit** | Valid model features, not verified identity/session relations. A train-fitted similarity graph may be a separately controlled M1 comparator, never a metadata hyperedge claim. |

## DeepSense classification

| Field | Class | Reason |
| --- | --- | --- |
| `domain_id` / source day | **B** | Exactly the day1-to-day2 holdout definition. |
| `rx_id` | **C** | One constant receiver value; no usable grouping. |
| `frequency_band` | **C** | One constant four-channel/20 MHz descriptor; no per-channel metadata. |
| `time_index` / source row index | **C** | Verified within-file window order, but it repeats across 32 class-pure captures and lacks a safe capture key. |
| source capture/path | **D** | Each capture is one target occupancy class; filename begins with the four-bit target. |
| occupancy/channel-state code | **D** | Recognition target. Preserve it as a string for evaluation only. |
| exact timestamp/session/site | **E** | Not present in the selected artifact. |

## ElectroSense classification

| Field | Class | Reason |
| --- | --- | --- |
| `rx_id` | **A** | Physical receiver/sensor identity, 40 values, 100% coverage, and every receiver has multiple target classes. |
| `source_date_id` | **A** | Coarse acquisition-date folder, 19 values, 100% reconstructable coverage, and not target-pure. Static grouping only. |
| `domain_id` | **B** | Exact duplicate of receiver identity used for the frozen sensor holdout. The equality relation must use the separately whitelisted `rx_id`, not the split field. |
| `frequency_band`, source band, band lower/upper/center | **D** | All 125 full bands are target-pure; derived bounds/center remain near-exact or exact proxies for technology. |
| `time_index` / source row index | **E** | Local order inside one target-pure technology/band file, no clock or cross-file order. |
| source capture/path/technology | **D** | Capture and path encode technology; every source file is target-pure. |
| source sensor ID | **C** | Duplicate provenance for `rx_id`; not separately whitelisted to prevent duplicate relation definitions. |
| site/location coordinates | **E** | Sensor names exist but independent location coordinates/site entities are absent. |

## Automated safeguards

The code and tests enforce:

1. target/outcome fields are rejected even if placed in a user whitelist;
2. a requested relation must appear in an explicit dataset whitelist;
3. the configured whitelist cannot exceed the reviewed hard whitelist;
4. source capture expansion must exactly match metadata row counts;
5. symbolic string IDs retain leading zeros;
6. missing/empty metadata and feature-row mismatches fail explicitly;
7. output directories inside a source artifact are rejected; and
8. source file size/mtime signatures must be unchanged before and after audit.

## PROPOSED DESIGN

Every future graph configuration should carry the whitelist verbatim and serialize it with the run metadata. Any expansion requires a new audit, train/validation-only justification, and human approval before running on a held-out domain.
