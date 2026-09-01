# Paper 3 Relational Feasibility Audit Handoff

Audit date: 2026-09-01

## 1. Exact artifacts inspected

### VERIFIED FACT

- `/mnt/d/openew_sa_data/processed/jamshield/{metadata.csv,labels.json,features.npy}`
- `/mnt/d/openew_sa_data/processed/deepsense/{metadata.csv,labels.json,features.npy}`
- `/mnt/d/openew_sa_data/processed/electrosense/{metadata.csv,labels.json,features.npy}`
- local raw README files and source file names/CSV headers under `/mnt/d/openew_sa_data/raw/{jamshield,deepsense,electrosense}`
- Paper 1 data/train configs and manuscript protocol descriptions
- Paper 2 manifest configuration, per-dataset manifests, and frozen split summaries

The frozen Paper 1 and Paper 2 sources select the same three processed artifact directories. Experiment-output directories were inventoried but not used as alternative metadata sources.

## 2. Exact scripts/code added

- `scripts/paper3/audit_relational_metadata.py`
- `src/openew/paper3/relational_audit.py`
- `src/openew/paper3/__init__.py`
- `configs/paper3/relational_feasibility_audit.yaml`
- `tests/paper3/test_relational_audit.py`

The audit is deterministic, preserves strings, verifies source signatures before/after, memory-maps feature arrays only for shape, and writes no sample-level output.

## 3. Generated external output paths

- `/mnt/d/openew_sa_data/paper3/audits/relational_metadata_audit.csv`
- `/mnt/d/openew_sa_data/paper3/audits/relation_coverage_summary.csv`
- `/mnt/d/openew_sa_data/paper3/audits/dataset_relation_summary.csv`

These aggregate outputs are intentionally outside Git.

## 4. Dataset-level relational feasibility

| Dataset | Rows / features | Allowed relations | Verdict |
| --- | --- | --- | --- |
| JamShield | 92,486 / 37 tabular metrics | `rx_id` as station equality, 100% coverage | **CONDITIONAL GO** |
| DeepSense | 32,000 / `2 x 1024` I/Q | none | **NO-GO** |
| ElectroSense | 45,750 / 512 PSD | receiver and coarse acquisition date, 100% coverage | **CONDITIONAL GO** |

## 5. Temporal feasibility

### VERIFIED FACT

- JamShield counters are monotonic only inside target-pure scenario files and lack timestamps.
- DeepSense windows are ordered inside target-pure occupancy captures; capture filenames encode the target.
- ElectroSense row indices are local to target-pure technology/band files; exact timestamps and cross-file order are absent.

### CONCLUSION

**DYNAMIC HYPERGRAPH: NO-GO.** Day membership alone is not dynamics. No current dataset has both reliable order/time and a target-independent session boundary.

## 6. Principal leakage risks

- JamShield `domain_id` and file stems encode benign/jammer scenario and are target-pure.
- DeepSense capture identity/path encodes the leading-zero occupancy target and is target-pure.
- ElectroSense frequency bands, derived bounds/centers, captures, and paths are exact or near-exact technology proxies.
- All ground-truth, OOD, split, correctness, threat, and human-review fields are forbidden.
- Endpoint/receiver identity can still be a shortcut; report purity, field removal, and relation corruption.

## 7. Proposed allowable relation types

### PROPOSED DESIGN

- JamShield `station_edge` from `rx_id`.
- ElectroSense `receiver_edge` from `rx_id`.
- ElectroSense static `acquisition_date_edge` from `source_date_id`.
- ElectroSense static `receiver_date_edge` from the joint allowed fields.

No same-class, same-OOD, frequency, source-capture, scenario, or temporal hyperedge is allowed.

## 8. Overall verdict

| Component | Verdict |
| --- | --- |
| Static hypergraph | **CONDITIONAL GO** |
| Dynamic hypergraph | **NO-GO** |
| Uncertainty-aware gating | **PREMATURE** |
| Neuro-symbolic component | **PREMATURE** |

The minimum two-dataset condition is met only for a narrow static relational design. The preferred paper framing is **Relational Domain Generalization for RF Situation Assessment**.

## 9. Recommended next experiment only

Run a prespecified M0/M1/M2 comparison on JamShield and ElectroSense under the unchanged Paper 1 scenario/reactive-family and sensor holdouts. Use only the hard whitelist, include field-removal and 100/75/50/25/0% relation-retention tests, and make unseen-domain macro-F1 the primary endpoint. Keep DeepSense at M0 only. Do not activate M3/M4/M5 yet.

## 10. UNRESOLVED human decisions

1. Is a two-dataset static relational contribution sufficient for the intended venue?
2. Should DeepSense appear as a documented relational NO-GO/M0 control or be excluded from the primary model table?
3. What deployment episode and maximum hyperedge size should be frozen before training?
4. Can dataset owners verify JamShield sampling intervals or ElectroSense exact timestamp semantics from already-held documentation?
5. What non-label symbolic rule, if any, is defensible enough to justify a later M5 stage?

## Integrity statement

No model was trained, no bootstrap was rerun, no dataset was downloaded, no target/test relation was selected from performance, and no Paper 1/Paper 2 source file was edited during this audit. Final hash and Git-status confirmation is recorded in the branch/PR handoff after tests.

Pre/post SHA-256 tree digests matched exactly:

- processed JamShield (3 files): `480d9f20343015e88937a894cd68f1812b66dd177cee51a3fb86b9e44fa3c7da`
- processed DeepSense (3 files): `fa735802e970681ea78b992ec2ed503bb1d6374b2f4d93ae37f40e6205c1e77e`
- processed ElectroSense (3 files): `780e07ff230079bce31629dc8f458a168c89dcf20ba33618b84a65cc2cf5e029`
- external frozen Paper 1 tree (10 files): `b8e29b3b4743e997262866b083fdbdd4dc49ee2abe96db7dd489a2933883650a`
- external frozen Paper 2 tree (716 files): `4685b9e202d648f0b3c5f5eafde49753c69dfcefeb9cd2eee493f1e3357997fc`
