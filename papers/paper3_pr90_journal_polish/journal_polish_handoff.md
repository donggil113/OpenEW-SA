# PR #90 journal-presentation polish: handoff

Status: presentation-only follow-up to the frozen PR #90 closure. This edit changes no model, split, support bank, receiver/seed inclusion, prediction, statistical result, numeric macro, or evidence export. The title and all authorship, affiliation, ORCID, corresponding-author, funding, and COI placeholders remain for human approval. PR #90 must remain draft.

## Canonical sources and exact changed paths

The main TMLCN and Access PDFs share `papers/paper3_reviewer_remediation/manuscript/shared/{abstract,body,preamble}.tex`; the supplementary source is `papers/paper3_reviewer_remediation/manuscript/supplementary.tex`. The journal-display tables are `manuscript/tables/{benchmark_journal,composition_oracle_journal}.tex`. The original `benchmark.tex`, `composition_oracle.tex`, `receiver_deltas.pdf`, numerical macros, frozen evidence, and reporting figure manifest are unchanged. The new main Figure 2 is `manuscript/figures/receiver_delta_summary.{pdf,png,provenance.json}`. Its source-backed renderer and numerical guard are under `scripts/paper3/pr90_journal_polish/`, with tests under `tests/paper3/pr90_journal_polish/` and a small P2 inference snapshot under `configs/paper3/pr90_journal_polish/`. Lineage details are in `numerical_guard.md` and `probability_supplement_lineage.md`.

## Wording and presentation

- Title: retain “Unlabeled Receiver Adaptation for RF Fingerprinting Under Unseen-Receiver Shift: An Information-Matched Comparison on WiSig” as a **proposal pending author approval**; no title or author-field change was made.
- Abstract body (second TeX line, `wc -w`): **202 → 166 words**, a 17.8% reduction. It now emphasizes the 32-receiver LOSO information-matched comparison, P0/T3A/P2, EMB-STD, oracle composition stress, and single-dataset limitation.
- Main Introduction: exact internal PR/commit/date chronology removed. It says the frozen receiver analysis preceded outcome-informed post-hoc baseline/sensitivity work, which is not independent confirmation. Dates and commits appear only under supplementary “Study provenance and analysis chronology.”
- Section IV: “Post-hoc Baseline and Sensitivity Analyses.” The opening sentence says its design followed knowledge of frozen receiver outcomes.
- Table II: SAR-GN dagger and caption identify a bounded post-hoc application with **293/320** recovery-triggered updates, not a general SAR finding. Main prose retains 320 updates, 293 resets, 146/160 two-batch resets, 147 exact final-tensor/probability matches, and 25/32 receiver metric ties; these identity claims are not conflated.
- SAR learning rate: the inspected official SAR commit `20f6e24b17525f34503510afccedc0629b67b7c4` sets `2.5e-4` for its GroupNorm ResNet-50 branch at batch size at least 32 and scales smaller batches. The manuscript now states that this **reference configuration was transferred** to a different RF backbone. It retains the official and local hard-coded EMA recovery threshold 0.2.
- SHOT-IM: technically executable on this backbone, not a faithful full original source recipe; intentional scope exclusion, **not** technical impossibility. Abstract/Introduction state selected procedures rather than an exhaustive benchmark.
- Table V: five columns (condition, T3A, P2, RX-NORM, label-dependent); the twelve frozen F1 values are unchanged. Caption says **POST-HOC ORACLE COMPOSITION DIAGNOSTIC**, 32 receivers/five seeds, common query universe/100% coverage, bank 128, at most 32 oracle peers, query-label dependence, non-deployability, and EMB-STD/SAR-GN **NOT EVALUATED**. Discussion states the observed T3A stress failure is not a causal class-composition estimate because peer count changes and oracle query labels are used.
- Main Figure 2: compact frozen-inference paired-delta summary, **not** receiver performance sorting or a new joint Holm test. The unchanged 32-receiver, identity-ordered plot is Supplement Figure 1.
- Figure 3: caption states the apparent change around 64 packets is descriptive for this fixed dataset/support construction, not a validated minimum; 128 remains reference.
- Supplement: raw and source-validation-temperature ECE, adaptive ECE, NLL, Brier, mean confidence, and confidence-minus-accuracy gap are fully tabulated using the frozen `numbers.tex` macros. The two tables share page 4; reliability pages follow without an orphaned page.
- References: **zero additions, zero removals**; 31 numbered references remain. No citation was added merely to meet a count.

## Final PDFs and QA

Create-once output root: `/mnt/d/openew_sa_data/paper3/pr90_journal_polish/20260928T150540Z/pdf/`.

| Variant | Pages | SHA-256 | Composition Table V | Main Figure 2 |
|---|---:|---|---:|---:|
| TMLCN | 9 | `068d6511bae860cb9714b57c7d7d31a975d3fc3133ca77320f5a53f148ab799e` | 7 | 6 |
| Access | 10 | `f4572dac7ea7e033d7ae7167cca144aeb1fadcbfdeb8081aa3e2c318b1128b09` | 7 | 6 |
| Supplement | 12 | `d09fc66308320e2336a9fc6fc687aef224cecd7418d02e04ad75d0f77b2fd117` | n/a | full 32-receiver plot, 3 |

All three PDFs built with zero LaTeX errors, zero undefined citations/references, zero overfull boxes/warnings, zero Type 3 fonts, and all fonts embedded. All main pages were rendered and inspected at approximately 100% display size: title/abstract, SAR table dagger, Table V numerals/caption, compact Figure 2 and fixed-order supplement plot, budget warning, probability plots, and reference endings are legible without clipping or overlap. Supplement probability tables are on page 4; its first receiver-reliability panel begins on page 5.

## Numeric and regression checks

The read-only journal numerical guard **PASS** report is `/mnt/d/openew_sa_data/paper3/pr90_journal_polish/20260928T150540Z/numeric_lineage.json`. It checks 276 frozen numeric macros, all seven original non-composition tables (316 numeric cells), the journal benchmark table (60 numeric cells), twelve composition F1 cells, 18 frozen evidence exports, 14 original figure hashes, and the new Figure 2 against pinned receiver inference. The PR #87 oracle exports do not contain per-query IDs; matching archived query counts and frozen construction code support, but do not byte-prove, oracle query-ID identity.

Fresh WSL venv tests: **1,790 passed, seven subtests passed** across Paper 3 and Paper 2 (Paper 2 separately: 17/17). There were six pre-existing warnings, no test failures. `python -m compileall` and `git diff --check` passed. No training or target inference was performed. The frozen Paper 1, Paper 2, PR #80–#89 outputs, PR #90 predictions/checkpoints/analysis, and original figures/tables were not edited.

Human decisions remain: title and journal selection; authorship, affiliation, ORCID, corresponding author, funding, COI; final AI-use disclosure; licence/release approval; and whether one-dataset evidence is sufficient for submission. This formatting pass alone does **not** change publication readiness.
