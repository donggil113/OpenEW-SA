# Submission-candidate PDF audit

These are formatting candidates, not human-approved submissions. Authors,
affiliations, ORCIDs, correspondence, funding, conflicts, exact AI disclosure,
release wording, and venue choice remain blocking human decisions.

Build root (new, external, not committed):
\`/mnt/d/openew_sa_data/paper3/submission_finalization/20261001T150527Z_Tckvdh/\`.
The frozen presentation figure manifest and official IEEE Access template were
hash-checked by the builder; no RF payload or model evaluation was run.

| Candidate | Pages | SHA-256 | Final TeX log / references / boxes / fonts |
|---|---:|---|---|
| TMLCN main: \`paper3_tmlcn_submission/main_tmlcn.pdf\` | 9 | \`cd7a3995b70e790d44890b43609ea341706d44d9aae9c076c507f4020e516219\` | PASS |
| IEEE Access main: \`paper3_access_submission/main_access.pdf\` | 10 | \`4a088a8eecdf32f99f3446edc8bf81f7a205e06f01d5777af395b6c55acabf52\` | PASS |
| Supplement: \`paper3_supplement_submission/supplementary.pdf\` | 12 | \`db00e5e2bac6bf89aa50272069595e0229089e795c5df57468e20556cc58cc92\` | PASS |

The final (not intermediate latexmk-pass) TeX logs show zero compile errors,
undefined references or citations, and overfull boxes. Poppler reports no
Type 3 fonts and every font embedded. The text lint finds none of the
internal-review banner, PR numbers, local filesystem paths, TODO,
HUMAN_REQUIRED, placeholder, or draft-only language in the submission PDFs.
The scientific term *post-hoc* remains. The detailed machine-readable report
is \`pdf_audit_final.json\` at the external build root. The first audit file
\`pdf_audit.json\` used the aggregate latexmk stdout, which includes transient
first-pass undefined-reference warnings; the corrected audit reads final TeX
\`.log\` files. No PDF or scientific source was altered in that audit correction.

All 9 TMLCN, 10 Access, and 12 supplement pages were rendered with Poppler and
inspected as complete contact sheets. Full-size checks covered both main title
and abstract pages, Table V's oracle composition values and nondeployable
caption, probability-quality figures, supplementary all-receiver coverage,
and both reference endings. No clipping, overlapping text, or missing page
was visible. The Access last page has ample whitespace after references, not
content loss. Unresolved human identity fields are suppressed rather than
fabricated, so the front matter must be filled and visually re-reviewed before
submission.

Internal builds were generated separately at
\`paper3_tmlcn_internal/\` and \`paper3_access_internal/\` under the same
external root; they retain the OpenEW-SA Internal Review identity. Both
submission venues use the same frozen abstract, numerical macros, scientific
tables and figure inputs. The supplementary provenance wording is staged
without PR/commit chronology while preserving the post-hoc evidence status.

The [scientific freeze manifest](scientific_freeze_manifest.json) checks 74
tagged scientific files against commit
\`676b01ea946dbeff21322db328e4851fbb00e1c4\`; it passed after the build.
Numerical/scientific changes: **none**.
