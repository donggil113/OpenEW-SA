# Frozen Future Experiment Protocol for Paper 3

Status: design only; no training was performed in this feasibility phase.

## Scientific endpoint

The primary endpoint is **macro-F1 on the prespecified unseen-domain holdout**, with model/relation selection performed only on training and source-domain validation data.

Secondary endpoints are balanced accuracy, per-domain macro-F1, expected calibration error (ECE), and—only if uncertainty gating is activated—selective risk/coverage. Relation incidence/coverage and any predeclared symbolic-violation rate must be reported as mechanism diagnostics, not selected after viewing target-domain results.

## Preserved domain protocols

### VERIFIED FACT

- JamShield: preserve the Paper 1 scenario holdout and reactive-jammer-family holdout, including the prespecified benign control domain. `domain_id` is split-only.
- DeepSense: preserve day1 training/source validation and day2 held-out evaluation, but run M0 only unless a future audit verifies safe relations.
- ElectroSense: preserve the Paper 1 sensor holdout. Use `rx_id` only as an equality relation within a deployment episode; do not use a learned categorical embedding that assumes the held-out receiver was seen during training.

No split may be simplified or revised after observing held-out performance.

## Staged model matrix

| Stage | Design | Current status |
| --- | --- | --- |
| M0 | Existing independent-sample, dataset-specific RF encoder/baseline | Required control; reuse protocol, retrain only in the future experiment phase |
| M1 | Pairwise graph baseline using the same explicit allowed-field whitelist; optional train-fitted feature-similarity comparator reported separately | Feasible for JamShield/ElectroSense |
| M2 | Static typed hypergraph: JamShield station; ElectroSense receiver, date, and receiver-date types | **Next recommended experiment** |
| M3 | Dynamic state update over verified temporal neighbors | Not permitted by current audit; NO-GO until new evidence |
| M4 | Frozen M2/M3 plus train/validation-fitted uncertainty-aware gating | Premature; condition on M2 benefit |
| M5 | Full model plus independently justified symbolic consistency | Premature; no valid rule currently verified |

M1 and M2 must use identical encoder capacity, optimizer budget, seeds, and train/validation splits where architecture permits. Hyperedge batching/sampling limits must be fixed from source-domain resource constraints, not target performance.

## Relation construction contract

Each run serializes an explicit whitelist:

```yaml
jamshield: [rx_id]
deepsense: []
electrosense: [rx_id, source_date_id]
```

Graph construction must:

1. validate requested fields with `validate_relation_fields`;
2. construct no edge across train/validation/test partitions;
3. use no target, OOD, correctness, prediction, or performance field;
4. preserve symbolic identifiers as strings;
5. define the deployment episode/batch before model evaluation;
6. fit any feature scaling or similarity metric on training data only; and
7. record relation coverage, hyperedge sizes, isolated nodes, and whitelist in run metadata.

Target-domain labels may be read only after predictions are frozen for metric computation.

## Ablations

| Ablation | JamShield | DeepSense | ElectroSense |
| --- | --- | --- | --- |
| Remove receiver/station relation | Required | Not applicable; none allowed | Required |
| Remove frequency relation | Not applicable; constant | Not applicable; constant | **Safety negative control only: relation is forbidden and must remain absent** |
| Remove temporal relation | Not applicable; current temporal relation forbidden/unresolved | Not applicable; current temporal relation forbidden | Not applicable; current temporal relation unresolved |
| Remove acquisition-date relation | Not available | Not available | Required |
| Remove uncertainty gating | Required only if M4 is activated | Not applicable | Required only if M4 is activated |
| Remove symbolic consistency | Required only if M5 is activated after a new rule audit | Not applicable | Same condition |

Unavailable/forbidden ablations must be reported as not applicable rather than implementing unsafe relations to fill the matrix.

## Relation-corruption test

For each allowed relation type, retain **100%, 75%, 50%, 25%, and 0%** of relation incidences using deterministic seeds. Retention masks are created independently of labels and held-out performance. The 0% condition collapses to the relation-removed control. Preserve nodes and features; remove only incidences so the test measures reliance on relation availability rather than changing sample support.

Report mean and standard deviation over the same prespecified seeds as the primary comparison. Do not choose a retention level based on target-domain performance.

## Model selection and statistics

- Fix architecture families and relation types before target evaluation.
- Select hyperparameters on source-domain validation macro-F1, with ECE as a secondary diagnostic.
- Use identical seeds and splits for paired comparisons.
- Report per-seed and aggregate metrics; predeclare any confidence interval or paired test before running.
- Do not reuse Paper 2 OOD labels to gate or tune Paper 3 relations.
- Treat DeepSense as M0-only evidence unless a separate metadata audit changes the contract.

## Stop/go gate after M2

Proceed beyond M2 only if the prespecified static relational model shows a reproducible improvement in source validation and does not degrade the primary unseen-domain macro-F1 beyond a predeclared tolerance. A target-only gain may be reported but cannot be used to redesign relations or select M3/M4/M5.
