# Reproducibility levels for the Paper 3 PR #90 closure

Evidence check: 2026-09-28. This document describes executable paths and their evidence boundary. It does not claim a new scientific rerun.

| Level | Inputs and output | Current evidence | Missing proof |
|---|---|---|---|
| **A. RF-data-absent reporting** | Git-tracked small aggregates, code, LaTeX and verified references produce tables, figures and PDF. | **PASS for this closure on the installed WSL host.** The versioned snapshot SHA-256 is `e5ff9adf329aeb6bee002aca9c1b45a60f19bd1931df196baf130f3ee5999f6e`; the isolated run report records three PDFs, regenerated figures/tables matching the snapshot, no RF payload and no target evaluation. The composition table appears on page 6 of both main PDFs. The historical PR #90 fresh-clone result (1,724 tests) remains separate. | This is not proof of lawful raw-data reconstruction, model retraining, prediction reproduction, or portability to a new host. Prior PR #90 checksums remain historical evidence. PDF binary hashes can vary with TeX build metadata. |
| **B. Lawful raw-data split/support reconstruction** | Authorized official ManyRx payload and converter reproduce separated acquisition metadata/annotations and the frozen LOSO split and support/query IDs. | Conversion code, fixed six-class/32-receiver split rules, all 32 split hashes and support algorithm are present. Prior PR #90/local integrity checked the frozen raw/conversion artifacts, but no independent new receipt/reconstruction was run for this closure. | Lawful official RF source, licence confirmation, independently verified archive hash, clean output root, per-split and support-ID comparisons. Mark NOT EXECUTED here. |
| **C. Full checkpoint/prediction/analysis rerun** | Original data plus the frozen source training, bounded-support adaptation, blinded prediction and one-time analysis pipeline recreate all run records. | Exact CLIs and configs exist; original 2,080 V2 primary records and PR #90 2,400 derived records are closed and separately hashed. | A second full run was **not executed**. Reproducibility across a new GPU/driver/OS, optimizer nondeterminism and numerical intervals remain untested. New run roots and new one-time manifest are mandatory; never overwrite original records. |

## Level A: executable reporting path

From repository root, in the observed Linux/WSL Python 3.12 environment with the pinned observed lock and TeX Live:

    PYTHONPATH=src python scripts/paper3/reviewer_remediation/reproduce_public.py --output NEW_EMPTY_OUTPUT_DIR

The optional --access-template path points to the official IEEE Access ZIP with the frozen expected SHA. The command checks method/evidence/release hashes, runs Paper 3 and Paper 2 tests, compiles Python, regenerates figures and tables, builds TMLCN and supplement PDFs (and Access when template supplied), audits PDFs and checks Git whitespace. Expected outputs: report.json, step_*.log, tests.xml, figures/, pdf/, pdf_audit/. It does not load RF data.

**Version rule:** The command above belongs to the PR #90 snapshot. Its expected_checksums.json binds the old shared TeX source and remains frozen. The closure uses a separate create-once manifest and reproducer, so changing the manuscript does not rewrite the old ledger.

The finalized canonical main text, supplement, composition table and closure scripts were frozen in a new create-once reporting snapshot using:

    PYTHONPATH=src python scripts/paper3/pr90_closure/reproduce_reporting.py freeze --manifest papers/paper3_pr90_closure/reporting_snapshot_manifest.json

For a subsequent isolated Level-A rerun into a new external directory, supply the official Access template if that venue PDF is wanted:

    PYTHONPATH=src python scripts/paper3/pr90_closure/reproduce_reporting.py run --manifest papers/paper3_pr90_closure/reporting_snapshot_manifest.json --output NEW_EXTERNAL_EMPTY_DIRECTORY --access-template OFFICIAL_ACCESS_ZIP

The versioned checker validates the frozen scientific method hashes and old checksum-ledger hash, stages a copy of the manuscript and small evidence, regenerates existing figures/tables only in that copy, checks exact staged bytes against the new manifest, builds TMLCN main and supplement PDFs, checks fonts/references/overflow and records the actual page containing the composition table. It does not write to canonical manuscript or load RF data. Same-host success proves Level A only.

**Executed closure run:** `papers/paper3_pr90_closure/reporting_snapshot_manifest.json` has SHA-256 `e5ff9adf329aeb6bee002aca9c1b45a60f19bd1931df196baf130f3ee5999f6e`. The report at `/mnt/d/openew_sa_data/paper3/pr90_closure/20260928T110826Z/reporting_final_v1/report.json` records `status=PASS`, `scope=A_PAYLOAD_ABSENT_REPORTING_ONLY`, `rf_payload_loaded=false`, `new_target_evaluation=false`, and `full_scientific_reproduction=false`. TMLCN main: 9 pages, SHA-256 `12af5e41366078a8809104e00a366443e3349b2030df33f8764bce154383b5fd`; Access main: 10 pages, SHA-256 `f82cb162857724342fad1d57f7881fe55fd234144cd7282492081a54f67e5b2a`; supplement: 11 pages, SHA-256 `ac7d455cbde5dfac92e65334bd894c285f1f8537116064584bd9948283db9f07`. Both main PDFs have the composition table on page 6. The report records embedded fonts, zero Type 3 fonts, undefined citations/references, and overfull boxes in all three PDFs. This checks reporting reproducibility only, not B/C.

## Level B: split/support reconstruction path

Required inputs are a legitimately obtained official ManyRx compact archive, the source pickle identified by inspected archive manifest, an operator-supplied empty output root, the exact extraction/conversion code revision, and the frozen receiver hardware mapping. The frozen archive SHA-256 reported in the release is d2b23108c3f6f63a10ebbb149d7b08d6e1c1961cf5184926fbab452def3049de. The converted manifest SHA-256 is ffd98dcb8182435c1aaf416c3bb137e6f56f353811e7d1d7a6fc0cc4817ae4b6. Verify these against local, lawful source artifacts; their presence in documentation does not grant data access.

Actual entry points, with caller-supplied paths:

1. scripts/paper3/wisig/prepare_manyrx_source.py: --archive, --extraction-root, --analysis-root, --download-utc, --official-page, --official-view-url, --resolved-url. It inspects/extracts into a new root and writes archive/raw manifests.
2. scripts/paper3/wisig/convert_wisig_manyrx.py: --source-pickle, --output-root, --source-archive-sha256, --equalized-index 0, --shard-size 8192. Run independent pass A/B in new roots. Expected dataset_manifest.json and shards/shard_*/{acquisition_metadata.csv,annotations.csv,features.npy,manifest.json,restricted_provenance.jsonl}; compare deterministic contents.
3. scripts/paper3/wisig_v2/build_v2_splits.py: --converted-root, --output-root, --hardware-map configs/paper3/wisig_v2/receiver_hardware_v1.json. Expected split_freeze_manifest.json plus receiver_loso_00..31/split_manifest.csv and split_summary.json. Compare all 32 hashes and class/receiver counts with papers/paper3_receiver_adaptation_manuscript/reproducibility_release/split_hashes.json.
4. The support builder is src/openew/paper3/wisig_v2/support.py: freeze_support_query with opaque sample ID, receiver ID, seed and fixed budget. Primary 128 and sensitivity 256 use different query universes. Reconstructed support and query IDs must match frozen run-record hashes. No transmitter annotation may choose support.

This is a structural/data-reconstruction workflow, not an invitation to execute new held-out evaluations in this closure. Filesystem mtime does not prove acquisition time.

## Level C: full scientific execution contract (documented, NOT EXECUTED)

Environment: papers/paper3_receiver_adaptation_manuscript/reproducibility_release/{requirements-observed.lock,environment.json}; Python 3.12.3, torch 2.11.0+cu128, CUDA 12.8, RTX 4090/driver 591.86 were observed. Source models use configs/paper3/wisig_v2/methods_v2.yaml and papers/paper3_wisig_methods_remediation/model_config_freeze_v2.md. PR #90 methods use configs/paper3/reviewer_remediation/protocol.json and the preregistration frozen at f30b658ff40f4d8ec3770be4c7c2b4692e5814da. Hash ledgers: reproducibility_release/{method_hashes.json,split_hashes.json,execution_freeze.json}. These are provenance and compatibility gates, not permission to reuse one-time manifests.

1. **Source checkpoint training and blind V2 predictions:** scripts/paper3/wisig_v2/run_v2_suite.py --repository CHECKOUT --converted-root NEW_CONVERTED_PASS_A --split-root NEW_FROZEN_SPLITS --run-root NEW_V2_RUN_ROOT --phase primary_loso --blind-target-metrics. It trains source models, selects checkpoints on source-validation receivers, and writes runs/<protocol>__<method>__s<seed>__b128__k32__r100__raw/{run.json,checkpoint.pt,history.json,predictions_blind.npz} as applicable. The frozen original registry has 2,080 primary records. A fresh run must use a **new** root, with its own Git SHA and hashes.
2. **Blind-run audit and one-time V2 analysis:** scripts/paper3/wisig_v2/freeze_before_unblinding.py and unblind_and_analyze_v2.py, with the flags documented verbatim in papers/paper3_wisig_methods_remediation/execution_runbook.md. The first creates an immutable pre_unblinding_freeze.json after a clean committed code tree; the second creates a one-time unblinding_manifest.json and receiver-level CSV/statistics. Never point either at the original frozen V2 root for a new run.
3. **PR #90 post-hoc derived addendum:** scripts/paper3/reviewer_remediation/run_blind.py --data-root CALLER_DATA_ROOT --output-root NEW_ADDENDUM_ROOT --repository CHECKOUT --source-only-smoke first. After code/protocol commit, baseline integrity and freeze, scripts/paper3/reviewer_remediation/freeze_and_analyze.py freeze --data-root CALLER_DATA_ROOT --output-root NEW_ADDENDUM_ROOT --repository CHECKOUT; then run_blind.py without smoke. This loads the compatible V2 P0/P2 checkpoints. Each of 32 receivers × 5 seeds writes source_validation.json and blinded method/budget run records; expected primary 480 and budget 1,920, total 2,400. Code enforces clean Git and compatibility hashes.
4. **PR #90 analysis:** freeze_and_analyze.py preflight followed once by unblind; write prediction_manifest.json, unblinding_manifest.json, analysis/receiver_seed_metrics.csv, receiver_averaged_metrics.csv, receiver_inference.json and core_analysis_manifest.json. Calling unblind a second time must fail. A separate independent rerun gets its own timestamp/hash lineage. The established core package SHA-256 b3989f7dad6b561957d7de887c100d7fe90f7baedf3119e5c7fb55c045568953 is a historical original-artifact comparison, not a promised bitwise match across changed hardware.

Operational caveat: freeze_execution requires frozen_before.json reporting PASS; new operator must run the relevant immutable baseline integrity audit into the **new** root first. The old code may enforce historical SHA or data-manifest compatibility: honor that failure and document a separately versioned replication protocol rather than patching a frozen script in place. This document identifies the pipeline; it does not certify a new full-science reproduction.

## Exact scope of this closure

No new raw download, WiSig conversion, split build, V2 model fit, PR #90 model fit or target metric rerun is authorized by this closure. Level A is PASS for the frozen closure snapshot above; any further manuscript edit requires a new versioned snapshot and Level-A rerun. Levels B/C remain NOT EXECUTED unless a separate lawful replication is commissioned.
