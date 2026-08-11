# Paper 2 Submission Strategy

Based on `target_journal_matrix.md` (official sources, accessed 2026-08-11), `reviewer_risk_register.md`, and the R1–R17 verification in `reference_verification_matrix.md`. No scientific result is changed by anything below.

## Recommended targets

### 1st choice — IEEE Transactions on Machine Learning in Communications and Networking (TMLCN)

**Why:** It is the only IEEE Transactions whose official editorial policy explicitly advocates reproducibility and public artifact sharing, and whose scope (ML for signal detection, interference mitigation, spectrum management) is a bullseye for this paper. The paper's distinguishing strengths — frozen leak-audited protocol, numerical traceability matrix, paired bootstrap with prespecified roles, honest negative result — are *selling points* to this reviewer pool rather than apologies. Fully OA (CC BY, US$2,160 for 2026) with author-retained copyright fits the open-artifact posture of OpenEW-SA. It carries Transactions-level standing without TCCN's communication-theory novelty culture.

**Changes needed for TMLCN:**
- Send the invited pre-submission query (eictmlcn@gmail.com) to confirm page limits — not stated on official pages — and, optionally, to gauge fit of an evaluation-protocol contribution.
- Reframe contributions per RISK-N1/N2: lead with the leak-resistant protocol and the cross-shift empirical findings; state explicitly that the fusion is deliberately simple and prespecified.
- Retitle to drop "Multi-View" (RISK-T1 recommendation; decision owner: authors).
- Add prevalence/no-skill AUPR anchors and the DeepSense trivial-baseline note (RISK-D4/C2).
- Prepare the public code/dataset-conversion link for the camera-ready (strongly encouraged by the journal; the repo scripts + frozen-artifact manifests already exist).
- Risk to manage at review: a request for at least one external OOD baseline (RISK-N3). Decide in advance whether to defend scope or run a clearly-labeled post-protocol energy-score baseline if required.

### 2nd choice — IEEE Access

**Why:** The official review criterion (technically sound, not necessarily highly novel) and the explicit "Negative Result" and "Methods" article types make it the highest-probability home for the paper as it stands, with no page limit, ~4-week decisions, and APC US$2,160. It is the correct fallback if TMLCN reviewers demand ML novelty or new experiments the project does not want to run. Two considerations: field-specific prestige is lower than a Transactions, and Paper 1 already targets IEEE Access (`papers/paper1_openew_sa/ieee_access/`) — publishing both there is acceptable but venue diversification favors trying TMLCN first for Paper 2.

**Changes needed for IEEE Access:**
- Reformat to the IEEE Access template (double-column Access layout differs from the generic IEEE Transactions template); submit source + PDF.
- Choose article type deliberately: "Research Article" with the negative result integrated (recommended — the paper is not *primarily* a negative result), rather than the "Negative Result" type.
- Same content fixes as above (prevalence anchors, contribution framing); title change still recommended.
- Compliance pass on template/grammar — Access desk-returns for format issues.

### 3rd choice — IEEE Open Journal of the Communications Society (OJ-COMS)

**Why:** ComSoc branding with fully-OA, rapid review (2-week reviewer deadlines), no page limits, APC US$2,160, and a scope that names ML for communications and cognitive/intelligent networks. A sensible middle path if the authors want ComSoc identity without TCCN's novelty bar.

**Changes needed for OJ-COMS:**
- Prepare a **mandatory graphical abstract** (new artifact; can be adapted from the pipeline figure).
- Use the IEEE Open Journals template.
- Same content fixes as above.

**Honorable mentions:** TCCN if the authors value classical prestige and accept higher rejection variance plus ~1 page of mandatory overlength charges at publication (13-page submission cap is met); OJSP if a Code Ocean capsule is acceptable — its *mandatory* reproducibility policy is philosophically the best match, but the audience is general signal processing.

## Main paper vs. supplementary allocation

Current draft content mapped to a Transactions-style submission:

**Keep in main paper:**
- Table 1 (protocols/counts) — add OOD-prevalence / no-skill AUPR column (arithmetic from existing counts).
- Table 2 (primary CIs) — keep AUROC, AUPR-OOD, FPR95. Consider demoting the detection-accuracy column to supplementary (RISK-S3); if kept, retain the evaluation-descriptive flag in the caption.
- Table 3 (paired interval decisions) — keep as the paper's statistical core.
- Figures 1–5 — all five earn their place; Figure 5's POST-HOC DIAGNOSTIC label must survive editing.

**Move to supplementary (or cite-as-available in the repository):**
- Table 4 (full v0–v3 stage-wise summary CSV) — contextual, large, and already machine-readable; a two-sentence summary in the main text suffices.
- Exact paired difference values and bounds behind Table 3 (`paper2_v3_paired_differences.csv`).
- Reproducibility details beyond one paragraph: SHA256 manifests, validator behavior (leading-zero occupancy checks), seed metadata.
- Tie-prevalence / AUPR-convention sensitivity note if produced (RISK-S5).
- Detection-accuracy columns, if demoted.

At IEEE Access or OJ-COMS (no page limits) the same allocation still improves readability; "supplementary" can simply be an appendix plus the repository.

## Is the current 11-page IEEE-style draft structurally reasonable?

Yes. The structure (Abstract → Introduction → Related Work → Datasets/Protocols → Methods → Experimental Setup → Results → Discussion → Limitations → Conclusion → Reproducibility Statement) is a standard and complete empirical-paper skeleton, with unusually strong Limitations and Reproducibility sections. Structural notes:

- ~11 pages fits TCCN/TWC 13-page submission caps and is comfortable everywhere else; no structural surgery is needed for any recommended venue.
- The separate "Experimental Setup" section overlaps Methods (artifact/split pipeline vs. score definitions); at a page-constrained venue these could merge, but this is optional.
- A dedicated pipeline figure (data → splits → classifier → calibration → distances → normalization → fusion → metrics) is currently absent and would be a high-value addition for any venue, and doubles as the OJ-COMS graphical abstract.
- The References Placeholder section must be replaced by the verified bibliography before any submission (see below).

## Mandatory before submission (blocking)

1. **Replace all 17 `[REFERENCE NEEDED: Rx]` tokens** with verified citations from `references_verified.bib`, honoring the drafting cautions in `reference_evidence_notes.md` (notably: entropy not attributable to Hendrycks & Gimpel alone; Mahalanobis regularization is the manuscript's detail, not Lee et al.'s; JamShield must cite ICC 2025, not arXiv; ElectroSense class taxonomy cites the framework paper/code, not the Zenodo record). Then re-run the repository search to confirm no token remains.
2. **Resolve the two PARTIALLY_VERIFIED items** (R12, R13) as written — cite them within their verified support only (R12: underpinnings, not the exact composite procedure; R13: acknowledge the class-taxonomy provenance and the `unkn` label or scope the claim to the converted subset).
3. **Title decision** on "Multi-View" (RISK-T1) — recommended change; owner decision required.
4. **Prevalence anchors + DeepSense trivial-baseline note** (RISK-D4/C2) — three sentences and a caption; prevents the most avoidable reviewer "gotcha."
5. **Dataset licensing/attribution compliance:** ElectroSense Zenodo custom license requires specific citation wording; JamShield has *no stated license* — the data-availability statement must say how the converted artifacts respect these terms (JamShield especially: cite IEEE DataPort DOI 10.21227/5hzf-w161 and note the absence of an explicit license).
6. **Venue-specific packaging:** template, (TMLCN) pre-submission query, (OJ-COMS) graphical abstract, ORCID for all authors.
7. **Internal consistency pass** after edits: figure/table numbering, TRACE comments vs. `numerical_traceability_matrix.md`, no numerical value altered.

## Recommended but not blocking

- Prespecification evidence sentence + audit-trail pointer (RISK-L1).
- Tie-prevalence check for the stable-order AUPR convention (RISK-S5; read-only on frozen score files).
- Descriptive analysis of the DeepSense inversion mechanism from frozen artifacts (RISK-D3).
- Pipeline overview figure (also serves as graphical abstract).
- Selection-rule sentences for held-out scenarios/days/classes (RISK-L4).

## Explicitly NOT recommended pre-submission

- New model training, new splits, deep baselines, or external OOD detectors run preemptively (RISK-N3/S2): the paper's methodology depends on prespecification; extending comparisons now would blur exactly the discipline that makes it credible. Hold these as scoped revision-stage responses if reviewers require them.
