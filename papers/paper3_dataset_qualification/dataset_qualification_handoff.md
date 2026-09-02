# Paper 3 Public Dataset Qualification Handoff

## Executive decision

| Decision | Verdict |
|---|---|
| WiSig overall adoption | **CONDITIONAL GO** for one bounded conversion/QA step |
| WiSig licence | **RESTRICTED** (CC BY-NC-SA 4.0) |
| WiSig temporal/dynamic | **NO-GO / NO-GO** |
| Top external candidate | **WiSig — CONDITIONAL GO** |
| Public-data Paper 3 | **CONDITIONAL GO** for a static receiver-context question only |
| New prospective collection | **REQUIRED** for a temporal/dynamic Paper 3 |
| Next model experiment | **NOT AUTHORIZED** |

The machine-readable gate reports WiSig's raw/current adoption state as static-relational **NO-GO** because official source paths are target-bearing. Independently, the frozen structural scorecard reaches **STATIC_RELATIONAL** on `receiver_id`. Therefore the dataset-level verdict is conditional: a converter must replace path-derived identity with opaque sample IDs and prove annotation separation before static adoption can pass. This is not permission to train.

## VERIFIED FACT

### Frozen history

- Remote `main` started at PR #82 merge commit `0261d1a536356d75c2da318cb793094b4408c483`.
- PR #81 remains a 140-run overall NO-GO. No M0/M1/M2 rerun, no M3/M4/M5 run, and no target-visible optimization occurred.
- Read-only final integrity comparison passed for Paper 1 external data, Paper 2 external data, PR #81 analysis/experiment data, the three processed datasets, and the raw-tree structural fingerprint.
- Git path diffs against `main` are empty for Paper 1, Paper 2, PR #80/#81 paths, and PR #82 infrastructure paths.

### WiSig evidence

- Official scale: 174 transmitters, 41 USRP receivers, four captures in March 2021, and approximately 10 million extracted packets.
- Official acquisition: Wi-Fi channel 13, 2462 MHz center, 20 MHz Wi-Fi bandwidth, 25 MS/s, approximately 0.512 s per transmitter/receiver raw capture.
- Official metadata indexes represent 9,976,477 packets. Aggregate safety audit found receiver target-purity 0.022712 and NMI diagnostic 0.022617 across 41 receiver groups; receiver coverage is 1.0. Day has four groups and is split-only.
- Target is transmitter identity. Transmitter IDs, target-bearing paths, raw target-specific capture IDs, same-target groupings, and target/prediction/OOD/correctness fields are forbidden.
- Explicit acquisition timestamps were not found. Packet order exists only inside one-transmitter captures; receiver captures are not synchronized. Temporal verdict is **TARGET_NESTED_SEQUENCE**.
- Official dataset licence is CC BY-NC-SA 4.0. It permits research reuse subject to attribution/noncommercial/share-alike constraints; it is not classified CLEAR.
- Four official Git repositories and small official indexes were acquired under the metadata-only allowance. Manifest: 201 files, 11,233,143 bytes, repository commits and SHA-256 entries recorded. RF payload bytes downloaded: 0.

### Candidate survey

Seventeen public candidates were screened. Five were deep-audited: WiSig, OSU LoRa RFFP, OPERAnet, Antwerp LPWAN localization, and POWDER Data Commons. The ranked top three are WiSig, OPERAnet, and OSU LoRa.

- **WiSig:** best RF task fit and receiver diversity; no valid temporal context.
- **OPERAnet:** strongest clock/session evidence and multiple RF receivers, but human activity/localization task, co-located annotation columns, and unresolved item-level licence/size.
- **OSU LoRa:** strong fingerprinting task and metadata sidecars; target-pure transmissions, only limited receiver diversity per setup, >1.2 TB collection, and unclear redistribution terms.

### Acquisition/download status

- `/mnt/d` had 1,892,516,126,720 free bytes at preflight. The automatic 10% cap was therefore much larger than the fixed 5 GB sample cap; the fixed cap remained controlling.
- No RF payload or large archive was downloaded. A WiSig Google Drive request reached the official interstitial but was not converted into an unattended payload fetch.
- No converter pilot ran, because no candidate passed access, licence, target-path separation, split freeze, and adoption gates simultaneously.
- No `candidate_experiment_preregistration.md` was created because no candidate reached GO for static relational adoption.

## INFERENCE

- WiSig can plausibly support a scientifically distinct **receiver-context RF fingerprinting under receiver/day domain shift** study, but only after a successful metadata conversion gate. This inference is not a model result.
- OPERAnet could support genuine temporal infrastructure, but its task may be too remote from electromagnetic spectrum situation assessment to anchor Paper 3.
- Public data may support a static Paper 3; current evidence does not remove the need for new prospective collection if temporal/dynamic reasoning remains the goal.

## PROPOSED DESIGN

1. Obtain human institutional approval for WiSig CC BY-NC-SA obligations.
2. Download only official ManyRx (approximately 1.2 GB) into the designated external root; record URL, bytes, timestamp, SHA-256, and archive members.
3. Use a restricted parser. Produce separate acquisition metadata and transmitter annotations. Generate opaque sample IDs that do not preserve target-bearing paths.
4. Repeat sample-level path-token, purity, NMI, missingness, and receiver/day coverage audits using labels only in the audit process.
5. Freeze receiver/day split roles and a `receiver_id`-only relation whitelist before model evaluation.
6. Obtain independent review. Only then may a static M0/M1/M2 preregistration be drafted. Temporal/dynamic stages remain prohibited.

If that gate fails, execute the hardware-neutral prospective collection plan with at least two receivers/two campaigns, target-neutral UUIDs, explicit UTC/reset semantics, separate labels, and mixed-target episodes.

## UNRESOLVED

- Institutional interpretation of WiSig derived-artifact redistribution under CC BY-NC-SA.
- Stable unattended access and publisher-provided checksum for the selected compact archive.
- Sample-level preservation/coverage after restricted pickle conversion.
- A frozen, leakage-safe receiver/day holdout with adequate transmitter support in every partition.
- Whether receiver equality alone is a sufficiently strong contribution distinct from Paper 1.
- OPERAnet item-level licences, exact sizes, and task-fit decision.
- POWDER item-level licence/schema/session semantics.

## Implementation and external outputs

The new package provides strict candidate schemas, official-evidence validation, payload-licence and storage gates, frozen-readiness adaptation, temporal and target-proxy gates, adoption decisions, checksum manifests, storage estimation, and structural-coverage planning. Unknown fields fail closed; no model metrics are accepted.

External generated outputs:

- `/mnt/d/openew_sa_data/paper3/candidate_metadata/wisig/metadata_manifest.json`
- `/mnt/d/openew_sa_data/paper3/candidate_metadata/wisig/official_metadata_summary.json`
- `/mnt/d/openew_sa_data/paper3/dataset_qualification/wisig_metadata_index_proxy_audit.csv`
- `/mnt/d/openew_sa_data/paper3/dataset_qualification/wisig_qualification_report.json`
- `/mnt/d/openew_sa_data/paper3/dataset_qualification/external_candidate_matrix.csv`
- `/mnt/d/openew_sa_data/paper3/dataset_qualification/post_qualification_integrity.json`

## Validation

- New dataset-qualification tests: **93/93 PASS**.
- PR #82 prospective metadata tests: **84/84 PASS**.
- Earlier Paper 3 relational/static tests: **25/25 PASS**.
- Paper 2 regression tests: **17/17 PASS**.
- New source/script/test `compileall`: **PASS**.
- `git diff --check`: **PASS**.
- Frozen content/tree integrity: **PASS**.

## Exact next action

Request human licence/task-scope approval for a one-archive official WiSig ManyRx import. If approved, perform conversion and sample-level QA only; do not train until a separate frozen split and experiment preregistration pass independent review.
