# Freeze-tag-to-finalization diff audit

Baseline: annotated tag \`paper3-scientific-freeze-20260929\`, peeled to
\`676b01ea946dbeff21322db328e4851fbb00e1c4\`. The checked branch is
\`paper3/submission-finalization\`. This table classifies every intended file
in this branch's diff; the final commit must be rechecked against it.

| Changed file | Classification | Boundary |
|---|---|---|
| \`papers/paper3_reviewer_remediation/manuscript/shared/submission_metadata.tex\` | HUMAN_METADATA / DISCLOSURE / AVAILABILITY | New include; no frozen scientific body edit. |
| \`scripts/paper3/reviewer_remediation/build_pdfs.py\` | VENUE_FORMATTING / BUILD_QA | Staged presentation/metadata substitutions and PDF identity lint only. |
| \`tests/paper3/reviewer_remediation/test_build_pdfs_audience.py\` | BUILD_QA | Staging tests; no model/data operation. |
| \`papers/paper3_submission_finalization/HUMAN_SUBMISSION_CHECKLIST.md\` | HUMAN_METADATA | Blocking author/release decisions. |
| \`papers/paper3_submission_finalization/ai_use_disclosure_draft.md\` | DISCLOSURE | Draft, human verification required. |
| \`papers/paper3_submission_finalization/availability_policy.md\` | AVAILABILITY | Proposed wording and artifact boundaries. |
| \`papers/paper3_submission_finalization/build_modes.md\` | VENUE_FORMATTING | Five explicit build modes. |
| \`papers/paper3_submission_finalization/cover_letter_access.md\` | COVER_LETTER | Unsent, human approval required. |
| \`papers/paper3_submission_finalization/cover_letter_tmlcn.md\` | COVER_LETTER | Unsent, human approval required. |
| \`papers/paper3_submission_finalization/reference_audit.md\` | BUILD_QA | Bibliographic verification, no BibTeX edit. |
| \`papers/paper3_submission_finalization/release_inventory.md\` | AVAILABILITY | Proposed statuses; no publication. |
| \`papers/paper3_submission_finalization/reproducibility_levels.md\` | AVAILABILITY | Levels A/B/C kept distinct. |
| \`papers/paper3_submission_finalization/scientific_freeze_manifest.json\` | BUILD_QA | Frozen tag bytes for 74 scientific files. |
| \`papers/paper3_submission_finalization/submission_pdf_audit.md\` | BUILD_QA | External build/visual inspection report. |
| \`scripts/paper3/submission_finalization/audit_pdf_package.py\` | BUILD_QA | Final-log/font/text checks. |
| \`scripts/paper3/submission_finalization/make_contact_sheets.py\` | BUILD_QA | PDF page visualization only. |
| \`scripts/paper3/submission_finalization/scientific_freeze.py\` | BUILD_QA | Rejects drift from tagged scientific bytes. |
| \`tests/paper3/submission_finalization/test_pdf_audit.py\` | BUILD_QA | Technical PDF lint tests. |
| \`tests/paper3/submission_finalization/test_scientific_freeze.py\` | BUILD_QA | Freeze and tamper-detection tests. |
| \`papers/paper3_submission_finalization/final_diff_audit.md\` | BUILD_QA | This classification. |

UNEXPECTED_SCIENTIFIC_CHANGE: **0**. The frozen source abstract, shared body,
\`numbers.tex\`, all scientific tables and figures, numerical traceability,
and analysis evidence summaries pass bytewise SHA-256 comparison against the
tag. Paper 1 and Paper 2 have no changed file in this branch. Submission-stage
edits to availability, acknowledgment, front matter, and supplementary
repository chronology are metadata/presentation changes in external build
copies only, not changes to tagged scientific evidence.

The external venue packages and PDFs are deliberately not committed. Their
official IEEE template, rendered figures, and build logs remain under the new
external root documented in [submission_pdf_audit.md](submission_pdf_audit.md).
