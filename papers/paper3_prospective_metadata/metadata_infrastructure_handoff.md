# Paper 3 prospective metadata infrastructure handoff

## 1. Current scientific status

**VERIFIED FACT.** PR #80 is frozen at merge
`3b2159c897b58b538c05b01de2feb23c34fa8fac`; PR #81 is frozen at merge
`b2b59d54515f601e5f88156a0d4adc38bbf77016`. The completed 140-run static
relational pilot remains overall **NO-GO**. JamShield scenario and reactive
protocols were NO-GO, ElectroSense was at most CONDITIONAL GO, and all
protocols failed the shuffled-relation specificity criterion. M3/M4/M5 were
not run.

This workstream is prospective infrastructure, not an optimization or
reinterpretation of M0–M2.

## 2. Source locations inspected

The deterministic source inventory inspected 1,464 files totaling
40,883,166,382 bytes outside the new Paper 3 output root:

- `/mnt/d/openew_sa_data/raw/{jamshield,deepsense,electrosense}`;
- `/mnt/d/openew_sa_data/processed/{jamshield,deepsense,electrosense,tiny}`;
- existing Paper 1/Paper 2/Paper 3 experiment and documentation snapshots;
- repository converters/configs/manifests for JamShield, DeepSense,
  ElectroSense, WiSig, and RadioML.

Raw structural inspection covered 20 JamShield CSVs, 32 DeepSense SDR binary
captures, 10 DeepSense simulated-LTE HDF5 files, and 232 ElectroSense NPY
arrays. Filesystem mtimes were classified `SYSTEM_METADATA_ONLY`.

## 3. Retrospective recovery result

| Dataset | Recovery verdict | Newly recovered valid relation/time |
|---|---|---|
| JamShield | **NO** | none; `station` was already retained/tested; `sample` is target-nested row identity |
| DeepSense | **NO** | none; day is split-only and file/window order is occupancy-pure |
| ElectroSense | **PARTIAL, not experiment-enabling** | upstream sensor/date/frequency context is evident, but sensor/date were already tested, frequency/path are target proxies, and time was not retained |

**NEWLY RECOVERED FACT.** No field is both newly recovered and eligible to
authorize another current-data relational experiment. No field meets
`VALID_TEMPORAL_CONTEXT`.

## 4. Rejected target proxies

The aggregate audit predeclared and rejected four candidate source-derived
proxies: JamShield `domain_id`, DeepSense `source_file_id`, ElectroSense
`frequency_band`, and ElectroSense `source_file_id`. All annotation, label,
attack, occupancy, OOD, prediction, correctness, performance, and target-state
fields are separately forbidden by policy. Target-bearing path tokens and
four-bit occupancy filenames are automatically flagged.

Targets were loaded only in the audit process to compute coverage, group sizes,
conditional entropy, normalized mutual information, group purity,
near-deterministic mapping, missingness association, domain correlation, and
split correlation. These diagnostics never enter relation builders.

## 5. Temporal and episode feasibility

**VERIFIED FACT.** `temporal_feasibility.csv` contains zero
`VALID_TEMPORAL_CONTEXT` rows. Findings are `TARGET_NESTED_ORDER`,
`COARSE_DATE_ONLY`, `SYSTEM_TIMESTAMP_ONLY`, or `NO_TEMPORAL_METADATA`.

No current episode candidate combines target-neutral definition, documented
session/reset semantics, valid time/order, deployment plausibility, and new
mechanism evidence. Existing station/receiver/date groupings are preserved as
audit facts but cannot motivate another target-visible current-data experiment.

## 6. Proposed acquisition standard

**PROPOSED STANDARD.** Schema v1.0.0 stores opaque sample/session/capture IDs,
source order, UTC/clock provenance, receiver/station/site/sensor, hardware,
antenna, frequency/sample-rate/channel, privacy-safe location, campaign and
target-neutral operational context, raw-source linkage, and explicit
missingness/quality flags. Identifiers are strings; numeric coercion is rejected.

Task annotations are a separate long-form table. Relation, episode, temporal,
hypergraph, and dynamic builders accept only acquisition records. Unknown
fields fail closed; every relation requires both a policy state and an explicit
experiment whitelist.

## 7. Provenance and QA implementation

Every populated field can carry source type/record, parser version, extraction
method, official verification, confidence, and transformation history in
`metadata_provenance.json`. The validator checks schema compliance, duplicate
sample and session/capture/index keys, timestamp parsing/monotonicity/resets,
frequency/sample-rate plausibility, session cardinality, receiver coverage,
target-neutral source IDs, and provenance completeness. When annotations are
separately supplied, it also runs aggregate proxy diagnostics.

The metadata-to-structure layer implements deterministic O(N) equality groups,
O(N log N) frequency-overlap components behind a stricter policy, deterministic
episodes, typed hypergraph incidence without clique expansion, causal temporal
neighbors, and evidence-gated dynamic snapshots. It preserves isolated nodes
and partition boundaries.

## 8. Readiness scorecard

Readiness is based only on metadata structure, not predictive performance. The
committed synthetic fixture validates all software branches and reaches
`DYNAMIC_HYPERGRAPH` in the external scorecard. This proves API readiness only.

| Item | Verdict |
|---|---|
| Current JamShield new relational experiment | **NO-GO** |
| Current DeepSense new relational experiment | **NO-GO** |
| Current ElectroSense new relational experiment | **NO-GO** |
| Existing local alternative dataset | **NONE** |
| Prospective static relational infrastructure | **READY** |
| Prospective temporal infrastructure | **READY** |
| Prospective dynamic-hypergraph infrastructure | **READY** |
| Current scientific data for temporal/dynamic use | **NOT READY** |
| New data collection required | **YES** |

## 9. Candidate datasets

No fourth local dataset is scientifically ready. Local DeepSense LTE is
simulated and has no physical context; `processed/tiny` is a software fixture;
WiSig and RadioML payloads are absent.

Official-source reconnaissance found four external candidates. WiSig is
**PROMISING** for receiver/day static DG but requires raw timestamp/session and
licence audit. Historical ElectroSense collection/API and DeepSense 6G are
**MAYBE** with availability/task-fit gaps. The UC SmartHome RF fingerprinting
source is **REJECTED** for this question absent new evidence. None is declared
experiment-ready and nothing was downloaded.

## 10. Reproducibility and generated outputs

External outputs (not committed):

- `/mnt/d/openew_sa_data/paper3/source_forensics/source_inventory.csv`
- `/mnt/d/openew_sa_data/paper3/source_forensics/source_inventory_summary.json`
- `/mnt/d/openew_sa_data/paper3/source_forensics/raw_metadata_forensics.json`
- `/mnt/d/openew_sa_data/paper3/metadata_audit/candidate_field_audit.csv`
- `/mnt/d/openew_sa_data/paper3/metadata_audit/target_proxy_summary.csv`
- `/mnt/d/openew_sa_data/paper3/metadata_audit/group_purity_summary.csv`
- `/mnt/d/openew_sa_data/paper3/metadata_audit/missingness_summary.csv`
- `/mnt/d/openew_sa_data/paper3/metadata_audit/temporal_feasibility.csv`
- `/mnt/d/openew_sa_data/paper3/metadata_audit/episode_candidates.csv`
- `/mnt/d/openew_sa_data/paper3/metadata_audit/local_candidate_dataset_inventory.csv`
- `/mnt/d/openew_sa_data/paper3/prospective_validation/metadata_readiness_scorecard.json`
- `/mnt/d/openew_sa_data/paper3/prospective_validation/{pre,post}_workstream_integrity.json`
- test logs under `/mnt/d/openew_sa_data/paper3/prospective_validation/`

## 11. Test and integrity result

**VERIFIED FACT.** New metadata tests: 84/84 passed. Existing Paper 3 tests:
25/25 passed (6 feasibility-audit and 19 static-relational contract tests).
Paper 2 regression tests: 17/17 passed. `git diff --check` passed before each
commit and is rerun for final handoff.

The post-workstream integrity report matches every pre-workstream value:

- processed JamShield, DeepSense, and ElectroSense content hashes;
- external frozen Paper 1 and Paper 2 content hashes;
- PR #81 experiment (983 files) and pilot-analysis (27 files) hashes;
- all four Git tree IDs for Paper 1, Paper 2, PR #80, and PR #81;
- raw structural fingerprint: 317 files, 39,371,760,930 bytes,
  `6a64798a9249a41a10b6ada65aa23a3f179ba11f03245fe1c678ff819e6785fc`.

No model training, bootstrap, dataset download, target-visible relation
optimization, or frozen artifact write occurred.

## 12. Recommended next action

Approve and execute a small prospective pilot collection—not a model
experiment—with at least two receivers, two sites or campaigns, target-neutral
session/capture UUIDs, verified clock/reset metadata, frequency/sample-rate
context, and separately assigned annotations. Run the supplied QA and readiness
scorecard before freezing any predictive protocol. In parallel, a human may
request access to WiSig solely for a licence/schema audit; do not start training.

## 13. Human decisions required

1. Whether resources permit a new prospective RF collection and which task is
   sufficiently distinct from Papers 1 and 2.
2. Receiver/site/campaign coverage, clock authority, session open/close rules,
   maximum idle gap, and privacy-safe location precision.
3. Salt/key governance for hardware serial hashes and release redaction.
4. Dataset and code licensing/redistribution review, particularly JamShield,
   ElectroSense, and any prospective WiSig access.
5. Whether the PR #81 negative pilot belongs as a cautionary appendix in a
   future data-enriched paper; recommended yes only if genuinely new evidence
   is added, otherwise keep it as an internal gate.
6. Venue/collection timeline and the independent reviewer who signs off field
   provenance and eligibility before labels or target results are opened.

## 14. Evidence labels

- **VERIFIED FACT:** directly checked in local files, generated aggregate
  audits, official primary sources, tests, or integrity reports.
- **NEWLY RECOVERED FACT:** none that authorize a new experiment; partial
  ElectroSense upstream context is documented but not enabling.
- **PROPOSED STANDARD:** schema, collection, split, converter, provenance, QA,
  and preregistration design for new data.
- **UNRESOLVED:** owner-only logs, final licensing, privacy governance, candidate
  access, task choice, and human scientific sign-off.
