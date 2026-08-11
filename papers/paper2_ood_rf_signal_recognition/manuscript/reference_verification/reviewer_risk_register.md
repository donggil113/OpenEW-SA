# Paper 2 Reviewer Risk Register

Independent skeptical-reviewer audit of `paper2_full_manuscript_draft.md` (branch `paper2/reference-verification`, HEAD `6e0fb75`).
Audit date: 2026-08-11. This register does not change any scientific result; it records anticipated reviewer criticisms, whether the current draft already addresses them, and what response or revision is recommended.

Severity legend: **HIGH** = plausible sole grounds for rejection at a serious venue; **MEDIUM** = likely major-revision request; **LOW** = likely minor comment.

---

## 1. Novelty

### RISK-N1 — Equal-weight uncertainty + centroid-distance fusion is not methodologically novel
- **Severity:** HIGH
- **Why a reviewer may raise it:** Averaging a calibrated-entropy score with nearest-centroid cosine and Euclidean distances after robust normalization is a straightforward score-level ensemble. Combining confidence-based and feature-distance evidence for OOD detection is well established (e.g., Mahalanobis-based scoring, energy scores, feature-norm/logit hybrids such as ViM). A methods-focused reviewer will say the detector itself contains no new learning component, no learned weighting, and no architectural contribution.
- **Does the manuscript address it?** Partially. The contributions paragraph emphasizes protocol, reproducibility, and prespecification rather than model invention, but the abstract and title still foreground the method ("Uncertainty-Calibrated Multi-View RF Signal Recognition"), which invites a method-novelty reading.
- **Recommended response/revision:** Reframe the claimed contribution explicitly as (a) a leak-resistant, prespecified open-set evaluation protocol for heterogeneous RF artifacts, (b) the first paired-bootstrap, fixed-orientation comparison of uncertainty vs. geometry scores across class-, day-, and scenario-OOD RF shifts, and (c) the empirical findings themselves — including the DeepSense orientation inversion, which is the scientifically distinctive result. State plainly in the Introduction that the fusion is deliberately simple and prespecified, and that simplicity is a design choice for auditability, not an oversight. Target venues that value rigorous empirical/benchmark work (see `target_journal_matrix.md`) rather than method-novelty venues.
- **New experiments required?** No. This is a framing and venue-selection issue.

### RISK-N2 — Contribution rests on protocol rigor; reviewers may call it "an evaluation study, not a method paper"
- **Severity:** MEDIUM
- **Why a reviewer may raise it:** The strongest material in the paper is the discipline (frozen splits, validation-only fitting, fixed orientation, prespecified roles, traceability matrix). Reviewers at transactions-style venues sometimes discount this as engineering hygiene rather than contribution.
- **Does the manuscript address it?** Yes, implicitly — the leakage-controls section and reproducibility statement are unusually explicit — but the draft never argues *why* protocol rigor is itself a contribution in RF OOD, where post-hoc score reversal and comparator selection are easy to hide.
- **Recommended response/revision:** Add 2–3 sentences (Introduction or Related Work) arguing that RF OOD literature frequently reports results that could not be reproduced under deployment constraints (orientation, normalization, and thresholds chosen with test OOD knowledge), and position the paper as establishing a defensible baseline protocol. Cite R3-class references. Frame the negative DeepSense result as evidence the protocol has teeth.
- **New experiments required?** No.

### RISK-N3 — Comparator set is internal only ("fusion beats its own components")
- **Severity:** HIGH
- **Why a reviewer may raise it:** All prespecified comparators (TS entropy, NC cosine, NC Euclidean) are the fusion's own ingredients. There is no external reference detector — no energy score in the verified comparison, no ODIN, no kNN-distance, no Mahalanobis-only comparator in the primary set (Mahalanobis appears only inside the exploratory four-component fusion). A reviewer can argue the paper cannot show the fusion is competitive, only that averaging helps or hurts relative to its parts.
- **Does the manuscript address it?** Partially. The Limitations section admits the absence of logit-energy, deep-ensemble, MC-dropout, and learned-uncertainty baselines. It does not explain *why* the comparator set was restricted, beyond prespecification.
- **Recommended response/revision:** Two defensible options: (a) keep the current scope and add an explicit justification — the study tests a specific complementarity hypothesis (uncertainty vs. geometry) under a frozen protocol, and external detectors were excluded a priori to keep the comparison paired and leak-free; or (b) if reviewers insist, run additional prespecified baselines (energy score is available in principle since the pipeline supports logits) as a *new frozen evaluation*, clearly labeled as post-initial-protocol. Do not silently extend the comparator set inside the existing "prespecified" framing — that would undermine the paper's own methodology.
- **New experiments required?** Not for initial submission if option (a) is argued well. Realistically, reviewers at a strong venue **may genuinely require** at least one established external baseline (energy or Mahalanobis-standalone); this would be a real new experiment run on the frozen splits, not a reanalysis. Flag this as the most likely revision-stage experimental request.

---

## 2. "Multi-View" title risk

### RISK-T1 — "Multi-View" overstates the model
- **Severity:** HIGH (title/abstract-level; cheap to fix)
- **Why a reviewer may raise it:** In the ML literature "multi-view" almost always means a model that consumes multiple simultaneous representations of the *same sample* (e.g., raw I/Q + PSD + spectrogram fusion). Here, (a) each dataset contributes one processed representation, and (b) the fused "views" are scalar score types (uncertainty, cosine distance, Euclidean distance) over the same representation. A reviewer skimming title + abstract will expect within-sample multimodal fusion and feel misled; this is a credibility hit even where the body is honest.
- **Does the manuscript address it?** Yes — unusually candidly. The Introduction explicitly defines the two scopes of "multi-view," and the Limitations section repeats that no single model jointly consumes I/Q, PSD, spectrogram, and tabular views. But a disclaimer inside the paper does not neutralize a misleading title; many reviewers form the objection before reaching the disclaimer.
- **Recommendation (not applied automatically):** **Change the title.** The honest content does not need the term. Candidate titles that preserve the substance:
  - "Uncertainty-Calibrated Score Fusion for Open-Set RF Signal Recognition: A Leak-Resistant Evaluation Across Class, Day, and Scenario Shifts"
  - "Calibrated Uncertainty and Feature-Geometry Fusion for Out-of-Distribution RF Signal Recognition in Spectrum Monitoring"
  If the authors keep "Multi-View," it must be qualified in the abstract's first use (e.g., "multi-view in the sense of complementary score views"), and the same term should also be reconsidered inside Methods ("'multi-view' fusion refers to uncertainty and geometric score views"). Keeping the title is defensible only at venues where reviewers read carefully; the risk/benefit favors renaming.
- **New experiments required?** No.

### RISK-T2 — "Open-Set" in the title vs. day/scenario shifts in the body
- **Severity:** MEDIUM
- **Why a reviewer may raise it:** Strictly, only ElectroSense is open-set (unseen classes). DeepSense day-OOD is covariate/domain shift with an unchanged label space; JamShield scenario-OOD is domain novelty with an unchanged label vocabulary. An open-set-recognition purist will object that two of three protocols are not open-set problems, and may further ask whether "detecting" a covariate shift that preserves labels is even the right objective (the classifier might still be accurate on day 2).
- **Does the manuscript address it?** Partially. The protocol table and dataset sections label the shift types precisely, and the DeepSense section states it "tests domain shift rather than unseen-class rejection." The manuscript does not, however, discuss whether flagging label-preserving shift is operationally desirable, nor report the classifier's closed-set accuracy on the shifted domain.
- **Recommended response/revision:** Use "open-set and out-of-distribution evaluation" language consistently ("open-set electromagnetic spectrum monitoring" in the title is acceptable as an *operational setting* description, but the abstract should name the three shift types immediately, which it already nearly does). Add one Discussion sentence acknowledging that for label-preserving shifts, OOD flagging is a monitoring/triage objective (novel-domain awareness), not a claim that classification necessarily fails there. If closed-set accuracy of the frozen classifier on day-2 rows already exists in verified tables, cite it; do not run new training.
- **New experiments required?** No (unless day-2 classification accuracy is absent from frozen artifacts and reviewers demand it; that would be an evaluation-only computation on existing predictions, not new training).

---

## 3. DeepSense negative result

### RISK-D1 — Is the fixed-orientation negative result scientifically useful?
- **Severity:** LOW (as framed) — the framing is a strength
- **Assessment:** Yes, it is useful, and the manuscript's handling is one of its best features. AUROC 0.353 under a fixed orientation is direct evidence that "held-out domain ⇒ larger distance from training prototypes" is a false universal, and that validation-only normalization cannot repair a reversed direction. This falsifies an assumption embedded in most distance-based OOD deployments. Keep it.
- **Recommended response/revision:** None structural. Consider adding one sentence quantifying the implication: a deployed fixed-orientation detector on this shift would systematically *pass* novel-day traffic while flagging retained ID traffic.

### RISK-D2 — Post-hoc inversion diagnostic could be read as a backdoor result
- **Severity:** MEDIUM
- **Why a reviewer may raise it:** Any post-hoc negation analysis invites the suspicion that the authors are quietly showing "our score works if you flip it." A hostile reviewer will test whether negated numbers leak into claims.
- **Does the manuscript address it?** Yes, thoroughly and safely: the negation appears only in Figure 5, is labeled "POST-HOC DIAGNOSTIC ONLY" in the caption and figure title, is stated three separate times (Results, Discussion, Reproducibility) to not replace the primary result, and the Limitations section explicitly says it "cannot be considered evidence for a deployable orientation-selection rule." This is currently described safely. The one residual hazard is the Discussion phrase "would produce a useful diagnostic but an invalid primary detector" — keep exactly this stance in any revision.
- **Recommended response/revision:** No change needed. In the response letter, preempt by pointing to the three explicit fences.
- **New experiments required?** No.

### RISK-D3 — Reviewers will ask *why* day-2 samples concentrate nearer the centroids
- **Severity:** MEDIUM
- **Why a reviewer may raise it:** The paper reports the inversion but offers only a hypothesis ("held-out day-two samples can lie closer to training prototypes or receive lower uncertainty"). A reviewer will want at least a descriptive mechanism: gain/AGC differences, per-day amplitude normalization effects, occupancy-mix differences between days, or reduced day-2 diversity. Without it, the negative result reads as unexplained.
- **Does the manuscript address it?** Only as a hypothesis; no supporting descriptive statistics are shown.
- **Recommended response/revision:** A descriptive analysis of already-frozen features/scores (per-day feature norms, per-class score distributions, day-2 vs day-1 within-class spread) would materially strengthen the paper and requires no new training, no new splits, and no protocol change — it is a read-only analysis of existing artifacts. Recommend adding it as a short subsection or supplementary figure *if* it can be produced from frozen artifacts without touching the evaluation protocol. Otherwise, explicitly label the mechanism as untested hypothesis (the current wording "suggests" is acceptable but minimal).
- **New experiments required?** No new training or evaluation; descriptive reanalysis of frozen artifacts only.

### RISK-D4 — DeepSense detection accuracy sits at the trivial all-OOD baseline
- **Severity:** HIGH (interpretation risk, cheap to fix)
- **Why a reviewer may raise it:** DeepSense evaluation prevalence is 16,000 OOD / 19,200 total = 0.8333. The reported detection accuracy 0.833490 [0.833333, 0.833750] is numerically the "declare everything OOD" baseline (the CI lower bound *is* 0.833333 = 5/6). A sharp reviewer will notice that the best-threshold accuracy has collapsed to the majority-class rule, and will then ask whether detection accuracy is meaningful anywhere in the paper given ID/OOD imbalance (ElectroSense is 74% OOD, JamShield 58% OOD).
- **Does the manuscript address it?** Partially. Detection accuracy is consistently flagged "evaluation-descriptive," but the draft never states the prevalence baselines, so the trivial-classifier coincidence is left for the reviewer to discover — the worst way for it to surface.
- **Recommended response/revision:** State the OOD prevalence and the corresponding majority-class accuracy baseline for each dataset (Table 1 or Table 2 caption), and explicitly note that DeepSense detection accuracy equals the trivial baseline, consistent with the inverted score. This costs three sentences, uses only numbers already derivable from Table 1, and converts a latent "gotcha" into demonstrated statistical literacy. (Numerical values themselves must not be altered; this is added interpretation only.)
- **New experiments required?** No.

---

## 4. Statistical validity

### RISK-S1 — No multiplicity correction over 48 reported intervals
- **Severity:** MEDIUM
- **Why a reviewer may raise it:** 3 datasets × 4 comparisons × 4 metrics = 48 paired intervals plus 12 primary CIs, all at pointwise 95%. Some "excludes zero" cells are expected by chance alone. A statistically minded reviewer will ask for family-wise or FDR control, or at least for the family to be defined.
- **Does the manuscript address it?** Yes, candidly: it states the intervals are pointwise, that no family-wise adjustment is applied, and that interval exclusion "is not labeled universal statistical significance." The Limitations section repeats this.
- **Recommended response/revision:** The disclosure is adequate for an evaluation-focused paper, but the defense would be stronger by (a) noting that conclusions are drawn from *consistent patterns* (e.g., all four ElectroSense comparisons favorable; all DeepSense ranking metrics unfavorable) rather than isolated exclusions, and (b) optionally reporting a simple Bonferroni-style sensitivity note (e.g., which decisions survive at 99.9% pointwise) computed from the existing bootstrap replicate distributions. The latter is a reanalysis of stored bootstrap outputs, not a new experiment; do it only if the deterministic replicate data are retrievable from the frozen analysis package.
- **New experiments required?** No; optional reanalysis of frozen bootstrap outputs.

### RISK-S2 — One frozen split per dataset
- **Severity:** HIGH (most likely source of a "more experiments" request)
- **Why a reviewer may raise it:** Every conclusion is conditional on one class partition (ElectroSense), one day pairing (DeepSense), and one scenario holdout (JamShield). The reviewer will ask: would a different GSM/TETRA-style holdout, a different day pair, or a different scenario subset reverse the findings? The bootstrap resamples rows but cannot capture split-level variation, which the manuscript admits.
- **Does the manuscript address it?** Yes, explicitly in Limitations ("single frozen split... limits claims about alternative class partitions, days, sensors, or jammer scenarios") and in the bootstrap-scope paragraph. Claims in the Results are correspondingly bounded ("evidence for the frozen ElectroSense protocol").
- **Recommended response/revision:** Keep the bounded language. In a response letter, the defensible position is: (a) split-level replication changes the study design and would require refitting/recalibration per split — a genuinely new experiment campaign; (b) the paper's claims are already scoped to the frozen protocols; (c) frozen single splits are what make the leak-audit and exact paired analysis possible. Do **not** preemptively run extra splits just to appear stronger; if a specific reviewer requires it, treat it as a scoped revision experiment (e.g., a second ElectroSense class partition only).
- **New experiments required?** Not for submission. Possibly at revision, and it would be a real new experiment — say so honestly if asked.

### RISK-S3 — Evaluation-descriptive detection accuracy invites misreading
- **Severity:** MEDIUM
- **Why a reviewer may raise it:** A best-over-thresholds accuracy computed on the evaluation set is an oracle metric. Even flagged, its presence in headline tables (Table 2, Table 3 columns) risks readers citing it as performance. Some reviewers will ask for its removal or demotion.
- **Does the manuscript address it?** Yes: the flag is applied consistently in Methods, Results, captions, Limitations, and the reproducibility statement — this is better than standard practice.
- **Recommended response/revision:** Consider moving detection accuracy to a supplementary table at submission time (allocation question — see `submission_strategy.md`), keeping AUROC/AUPR-OOD/FPR95 as the main-text operating metrics. If kept, retain the caption flag verbatim. Combined with RISK-D4's prevalence baselines, this metric becomes safe.
- **New experiments required?** No.

### RISK-S4 — FPR95 near ceiling for two of three datasets
- **Severity:** LOW–MEDIUM
- **Why a reviewer may raise it:** DeepSense FPR95 = 0.992 and JamShield FPR95 = 0.927 are close to the maximum, where the metric saturates and its bootstrap CI mostly reflects tail granularity (DeepSense's CI width is ~0.006 around 0.992). A reviewer may note that differences in a saturated region are operationally meaningless, and that the 95%-TPR operating point is arbitrary for these data.
- **Does the manuscript address it?** Partially: Limitations notes FPR95 "can still be unstable under shifts in prevalence or score distribution," and the JamShield discussion correctly refuses to treat AUROC as a substitute for operating metrics. The saturation point itself is not called out.
- **Recommended response/revision:** Add one sentence noting that near-ceiling FPR95 values indicate no usable high-recall operating point exists under the fixed orientation, and that paired FPR95 differences in this regime should be read qualitatively. No metric change needed.
- **New experiments required?** No.

### RISK-S5 — Stable-order AUPR-OOD tie handling is nonstandard and interacts with input ordering
- **Severity:** MEDIUM
- **Why a reviewer may raise it:** Precision-at-OOD-ranks with ties broken by input-CSV order is not the grouped-threshold average precision most libraries (e.g., scikit-learn) compute. Worse, the evaluation CSV is documented as "test ID rows then test OOD rows concatenated": under heavy ties, stable descending sort places ID rows *before* OOD rows within a tie block, which systematically shifts tied-block precision (direction depends on block composition). So the convention is not merely different — it is coupled to a non-random input order. If any compared method produces many exact ties (plausible for discrete tabular JamShield features or clipped probabilities), AUPR-OOD values could differ measurably from standard AP.
- **Does the manuscript address it?** Substantially: the Methods section documents the convention, states it is applied identically to every method and replicate, and warns it "can differ from grouped-threshold average-precision implementations when scores are tied." The Limitations section repeats the reproduction caveat. What is missing is any statement of *how common ties actually are* in the compared score files.
- **Recommended response/revision:** Report tie prevalence per dataset/method (a read-only computation on frozen score CSVs), and if ties are rare, say so — the caveat then becomes moot. If ties are common for any method, additionally report standard interpolated/step-wise AP for that case in supplementary as a sensitivity check. Neither requires rerunning models or bootstraps. If neither computation is possible without touching frozen artifacts' scope, keep the documented-convention defense, which is honest but weaker.
- **New experiments required?** No; read-only sensitivity computation recommended.

### RISK-S6 — Paired bootstrap design details
- **Severity:** LOW
- **Why a reviewer may raise it:** Percentile (rather than BCa) intervals with 1,000 replicates; stratified ID/OOD resampling at original counts; shared indices across methods. These are all reasonable, and the shared-resample pairing is exactly right for same-observation comparisons. Possible nitpicks: 1,000 replicates is on the low side for stable 2.5%/97.5% quantiles; percentile intervals can undercover for near-boundary metrics (FPR95 near 1).
- **Does the manuscript address it?** The design is fully specified (replicates, stratification, pairing, seed, pointwise level); the choice of percentile method is not justified.
- **Recommended response/revision:** One sentence justifying percentile intervals (simplicity, no analytic acceleration for these metrics) and acknowledging quantile granularity at 1,000 replicates. Only if a reviewer insists, rerun the *existing deterministic* bootstrap with more replicates — a reanalysis, not a new experiment, but it changes frozen numbers, so treat it as out of scope unless required.
- **New experiments required?** No.

---

## 5. Dataset comparability

### RISK-C1 — Cross-dataset comparisons confound representation, task, and shift type
- **Severity:** MEDIUM
- **Why a reviewer may raise it:** ElectroSense (PSD, 6-class technology, class-OOD), DeepSense (I/Q windows, occupancy codes, day-OOD), and JamShield (tabular telemetry, binary, scenario-OOD) differ in *every* factor simultaneously. Any sentence of the form "the method works on X but not Y" cannot attribute the difference to shift type vs. representation quality vs. task difficulty. A reviewer may push on phrases like "materially different behavior" if they read as cross-dataset ranking.
- **Does the manuscript address it?** Yes, well: the Limitations section states cross-dataset differences "may reflect both protocol difficulty and representation quality," and the Conclusion frames results "at the level of the actual dataset and shift." The Results avoid cross-dataset superiority claims.
- **Recommended response/revision:** Keep claims per-dataset. Audit the final text for any sentence implying the three evaluations are a controlled comparison of shift types (the Abstract's "dataset-dependent view" phrasing is safe). Consider adding to Table 1 a note that the three protocols are three separate case studies, not arms of one controlled experiment.
- **New experiments required?** No.

### RISK-C2 — Different ID/OOD prevalences make AUPR-OOD non-comparable across datasets
- **Severity:** MEDIUM
- **Why a reviewer may raise it:** AUPR depends on prevalence: the no-skill AUPR baseline is 0.739 for ElectroSense, 0.833 for DeepSense, 0.577 for JamShield. Without these anchors, DeepSense AUPR 0.738 looks superficially decent when it is *below* its no-skill baseline, and ElectroSense 0.934 vs JamShield 0.710 cannot be compared at face value.
- **Does the manuscript address it?** No — prevalence baselines are never stated (this overlaps RISK-D4).
- **Recommended response/revision:** Add per-dataset no-skill AUPR-OOD baselines (equal to OOD prevalence) to Table 1 or the Table 2 caption, and one sentence in Methods noting AUPR-OOD must be read against its prevalence baseline within each dataset. Derivable from existing counts; no new computation beyond arithmetic.
- **New experiments required?** No.

### RISK-C3 — OOD sets dominate ID sets in two protocols
- **Severity:** LOW
- **Why a reviewer may raise it:** OOD:ID ratios of ~2.8:1 (ElectroSense) and 5:1 (DeepSense) are the reverse of typical deployment, where novelty is rare. FPR95 and AUPR-OOD are computed in an OOD-rich regime; a reviewer may question deployment relevance of the operating metrics.
- **Does the manuscript address it?** Indirectly (metrics are described precisely; no deployment-prevalence claim is made).
- **Recommended response/revision:** One Limitations sentence: evaluation prevalence reflects the frozen holdout sizes, not deployment prevalence; ranking metrics (AUROC) are prevalence-free while AUPR-OOD and detection accuracy are not.
- **New experiments required?** No.

### RISK-C4 — Are cross-dataset claims sufficiently bounded overall?
- **Assessment:** Yes, with the additions above. The draft already avoids universal claims, reports a negative result at equal prominence, and scopes the conclusion to "the actual dataset and shift." The residual exposure is entirely in missing prevalence context (RISK-C2/D4), not in overclaiming.

---

## 6. Leakage safeguards

### RISK-L1 — Prespecification is asserted but not externally evidenced
- **Severity:** MEDIUM
- **Why a reviewer may raise it:** The paper repeatedly says the primary method, comparators, orientation, and roles were fixed in advance, and that machine-readable metadata names them. A skeptical reviewer cannot verify "in advance" from the PDF alone and may ask what prevents the primary from having been chosen after inspecting test results (especially since the exploratory four-component fusion beats the primary on ElectroSense — a pattern consistent with honest prespecification, which is worth pointing out).
- **Does the manuscript address it?** Partially: the Reproducibility Statement cites frozen snapshots, `analysis_role` metadata, SHA256 manifests, and an independent review report. It does not state *when* roles were fixed relative to evaluation.
- **Recommended response/revision:** Add one sentence stating that analysis roles were recorded in the frozen v3 metadata before test-set metrics were inspected, and that repository history preserves the ordering. If the repository will be public, point to the commit history as the audit trail. The ElectroSense case (exploratory beats primary, yet primary is retained) can be cited in the response letter as behavioral evidence of genuine prespecification.
- **New experiments required?** No.

### RISK-L2 — Temperature scaling from clipped log-probabilities is nonstandard
- **Severity:** LOW–MEDIUM
- **Why a reviewer may raise it:** Standard temperature scaling divides *logits* by T. The pipeline reconstructs pseudo-logits as log of numerically clipped probabilities when logits are unavailable. For softmax outputs this differs from true logits only by a per-sample constant (which cancels in softmax) *except* where clipping binds, i.e., exactly the high-confidence samples that matter most for entropy scores. A careful reviewer may ask how often clipping binds and whether T is distorted.
- **Does the manuscript address it?** The mechanism is honestly documented in Methods (including clipping); the distortion question is not discussed.
- **Recommended response/revision:** State the clipping threshold and (if available from frozen artifacts) the fraction of validation probabilities at the clip boundary; note that for logistic regression the probabilities are available in closed form so log-probability reconstruction is exact up to clipping. Since the classifier is scikit-learn logistic regression, true logits (decision-function values) exist in principle — acknowledge that using them directly is a cleaner future implementation. Do not recompute anything for this draft.
- **New experiments required?** No.

### RISK-L3 — Validation-only normalization and calibration: residual coupling
- **Severity:** LOW
- **Why a reviewer may raise it:** Validation data serve two roles (temperature fitting and normalization statistics). This is legitimate — both are ID-only and OOD-free — but a reviewer may probe whether any evaluation information leaks via the fallback chain (IQR → std → unit scale with warning).
- **Does the manuscript address it?** Yes: the fallback chain is documented, evaluation rows are explicitly excluded from center/scale estimation, and the leakage-controls section enumerates exactly which labels touch which stage. This is stronger than typical practice.
- **Recommended response/revision:** None required. Optionally state whether the fallback was ever triggered in the verified runs (a fact presumably recorded in warnings/metadata).
- **New experiments required?** No.

### RISK-L4 — JamShield held-out scenario selection could itself encode a choice
- **Severity:** LOW–MEDIUM
- **Why a reviewer may raise it:** "A frozen subset of benign and jammer scenarios is held out" — the reviewer will ask how that subset was chosen (random? convenience? difficulty?). If the held-out scenarios were selected with any knowledge of model behavior, the scenario-OOD result is biased; if arbitrary, results may be sensitive to the particular holdout (overlaps RISK-S2).
- **Does the manuscript address it?** It states the identifiers are fixed in split manifests, but not the selection rule.
- **Recommended response/revision:** State the selection rule for held-out scenarios (and for the DeepSense day pairing and ElectroSense class partition) in one sentence each — e.g., fixed before evaluation, chosen without reference to any model output. This is documentation, not analysis.
- **New experiments required?** No.

### RISK-L5 — Overall leakage posture
- **Assessment:** The safeguard set — train-only centroids/covariance, validation-only temperature and normalization, fixed orientation, equal untuned weights, prespecified primary/comparator/exploratory roles, untouched test rows, post-hoc diagnostic quarantined — is coherent and unusually well documented. No safeguard gap was found that would invalidate a reported number. The exposures are evidentiary (RISK-L1) and presentational (RISK-D4, RISK-C2), not substantive leakage.

---

## Summary of top risks (ranked)

| Rank | Risk | Severity | Fix cost |
| --- | --- | --- | --- |
| 1 | RISK-N3 internal-only comparator set | HIGH | Framing now; possible real experiment at revision |
| 2 | RISK-T1 "Multi-View" title overstatement | HIGH | Retitle (recommended, not applied) |
| 3 | RISK-D4 DeepSense detection accuracy = trivial baseline, prevalence baselines absent | HIGH | 3 sentences + caption note |
| 4 | RISK-S2 single frozen split per dataset | HIGH | Bounded language already present; honest response-letter position |
| 5 | RISK-N1 fusion not methodologically novel | HIGH | Reframe contributions; venue choice |
| 6 | RISK-S5 stable-order AUPR ties coupled to input order | MEDIUM | Read-only tie-prevalence check |
| 7 | RISK-S1 no multiplicity correction | MEDIUM | Disclosure exists; optional sensitivity note |
| 8 | RISK-L1 prespecification not externally evidenced | MEDIUM | 1–2 sentences + audit trail pointer |
| 9 | RISK-C2 AUPR prevalence anchors missing | MEDIUM | Arithmetic + caption note |
| 10 | RISK-D3 inversion mechanism unexplained | MEDIUM | Read-only descriptive analysis of frozen artifacts |

No recommendation above requires new model training, new splits, or changes to any verified number for initial submission. The only genuinely experimental item (external baseline detectors, RISK-N3) is flagged as a *likely reviewer request*, not something to run preemptively.
