# Paper 2 Reference Verification Matrix

Consolidated status for all `[REFERENCE NEEDED: R1–R17]` tokens in `paper2_full_manuscript_draft.md`, per the requirements register `unresolved_reference_requirements.md`.

- **Access date for all web verification: 2026-08-11.** Web access was available; no item is PENDING_WEB_VERIFICATION.
- Every bibliographic field was checked against primary/publisher sources (IEEE Xplore via doi.org resolution, PMLR, proceedings.neurips.cc / papers.nips.cc, JMLR, ITU, Zenodo, IEEE DataPort, official GitHub records, arXiv, Crossref, DBLP). Per-entry provenance, supporting-passage paraphrases, and drafting cautions are in `reference_evidence_notes.md`. Full BibTeX is in `references_verified.bib`.
- **PARTIALLY_VERIFIED is not VERIFIED** — the two such items carry explicit citation constraints (see notes column and evidence file).

## Final tally

| Status | Count | IDs |
| --- | ---: | --- |
| VERIFIED | 15 | R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R14, R15, R16, R17 |
| PARTIALLY_VERIFIED | 2 | R12, R13 |
| UNRESOLVED | 0 | — |

## Matrix

| ID | Manuscript claim (abridged) | Selected reference(s) [bib key] | Claim-support evidence (section) | Confidence | STATUS |
| --- | --- | --- | --- | --- | --- |
| R1 | RF monitors face changing emitters, receivers, sites, propagation, schedules, interference | ITU *Handbook on Spectrum Monitoring*, 2011 ed. [`itu2011spectrum`]; Rajendran et al., IEEE Comm. Mag. 56(1):210–217, 2018 [`rajendran2018electrosense`] | ITU Ch. 1–5 (monitoring as management function; sites/stations; equipment/automation; measurement scheduling; interference procedures), verified from the official ITU PDF; ElectroSense abstract (dispersed heterogeneous sensors over time/geography) | HIGH | **VERIFIED** |
| R2 | Closed-set overconfidence under shift; calibration ≠ OOD separability | Ovadia et al., NeurIPS 2019 [`ovadia2019trust`]; Nguyen et al., CVPR 2015, pp. 427–436 [`nguyen2015fooled`] | Ovadia Secs. 1/4: calibration degrades under shift; ID-fitted post-hoc calibration doesn't transfer. Nguyen abstract: ≥99% confidence on unrecognizable inputs | HIGH | **VERIFIED** |
| R3 | Fix orientation/normalization/selection/thresholds without target-test OOD labels | Shafaei et al., BMVC 2019 [`shafaei2019biased`]; Yang et al., NeurIPS 2022 D&B [`yang2022openood`] | Shafaei Sec. 3 (OD-test: validation outliers must differ from evaluation outliers) + Sec. 4 (performance collapse under unbiased protocol); OpenOOD abstract (unfair comparisons without unified protocol) | HIGH (Shafaei) / MEDIUM (OpenOOD) | **VERIFIED** |
| R4 | Open-set recognition definition and scope | Scheirer et al., IEEE TPAMI 35(7):1757–1772, 2013 [`scheirer2013toward`]; Geng et al., IEEE TPAMI 43(10):3614–3631, 2021 [`geng2021recent`] | Scheirer abstract/Sec. 2: formal OSR definition via open-space risk; Geng Sec. 2: scope vs. rejection/zero-shot/open-world | HIGH | **VERIFIED** |
| R5 | Sensor/day/channel/site shifts alter RF feature distributions independent of task | Al-Shawabka et al., INFOCOM 2020, pp. 646–655 [`alshawabka2020exposing`]; Hanna et al., IEEE Access 10:22808–22818, 2022 [`hanna2022wisig`] | Al-Shawabka: cross-day/channel accuracy collapse (85%→9%) on unchanged task; Hanna: receiver/day changes significantly degrade trained classifiers | HIGH | **VERIFIED** |
| R6 | MSP / entropy as post-hoc confidence-OOD baselines | Hendrycks & Gimpel, ICLR 2017 [`hendrycks2017baseline`] | Abstract/Sec. 1 (MSP baseline), Sec. 2 (AUROC/AUPR). Caution: entropy is not proposed here — attribute via secondary (Ovadia) or "e.g." | HIGH | **VERIFIED** |
| R7 | Validation-fitted scalar temperature scaling; calibration distinct from OOD | Guo et al., ICML 2017, PMLR 70:1321–1330 [`guo2017calibration`] (+ [`ovadia2019trust`] secondary) | Sec. 4 (hold-out validation requirement), Sec. 4.2 Eq. 9 (single scalar T, NLL-optimized, argmax-preserving) | HIGH | **VERIFIED** |
| R8 | Logit energy as OOD score | Liu et al., NeurIPS 2020 [`liu2020energy`] | Sec. 2 Eq. 4: free energy = −T·logsumexp(logits/T) on a pre-trained classifier | HIGH | **VERIFIED** |
| R9 | Prototype/nearest-centroid feature-distance scoring; Euclidean vs cosine geometry | Snell et al., NIPS 2017 [`snell2017prototypical`]; Sun et al., ICML 2022, PMLR 162:20827–20840 [`sun2022knn`] | Snell Sec. 2.2 Eq. 1 (class-mean prototypes), Secs. 2.3/2.6 (Euclidean is Bregman, cosine is not); Sun (non-parametric feature-distance OOD scoring) | HIGH | **VERIFIED** |
| R10 | Tied-covariance Mahalanobis OOD score (+ regularization) | Lee et al., NeurIPS 2018, pp. 7167–7177 [`lee2018mahalanobis`] | Sec. 2.1: class-conditional Gaussians, tied covariance, min Mahalanobis distance to class means. Caution: the diagonal regularizer is the manuscript's implementation detail, not Lee et al.'s | HIGH | **VERIFIED** |
| R11 | AUROC / AUPR-OOD / FPR95 interpretation | Hendrycks & Gimpel, ICLR 2017 [`hendrycks2017baseline`]; Liang et al., ICLR 2018 [`liang2018enhancing`] (+ optional Davis & Goadrich, ICML 2006 [`davis2006prroc`]) | H&G Sec. 2 (AUROC ranking; AUPR base-rate sensitivity; positive class must be specified); ODIN Sec. 4.3 (FPR at 95% TPR definition) | HIGH | **VERIFIED** |
| R12 | Paired stratified bootstrap with shared resamples; percentile intervals | Efron & Tibshirani, *An Introduction to the Bootstrap*, 1993 [`efron1993bootstrap`]; Dietterich, Neural Computation 10(7):1895–1923, 1998 [`dietterich1998approximate`] | Efron & Tibshirani Ch. 13 (percentile intervals, pp. 168–177 per published TOC); Dietterich (paired comparison of learners on shared data). The exact composite design (stratified + shared indices) is assembled from, not prescribed by, these sources; full text verified via Crossref/TOC (publisher pages 403) | MEDIUM | **PARTIALLY_VERIFIED** |
| R13 | ElectroSense provenance, collection design, six technology labels | Rajendran et al. 2018 [`rajendran2018electrosense`]; Scalingi et al., INFOCOM 2023, pp. 1–10, DOI 10.1109/INFOCOM53939.2023.10228867 [`scalingi2023framework`]; Zenodo DOI 10.5281/zenodo.7521246 [`scalingi2023electrosensepsd`] | Zenodo record confirms crowdsensed PSD (RTL-SDR sweeps, 47 sensors, custom academic license) but does NOT enumerate the six classes; class set {dab, dvbt, fm, gsm, lte, tetra, **+ unkn**} confirmed only in the official framework code (`TCpackage/TechClass.py`). Cite the framework paper/code for the taxonomy; scope claims to the converted subset | MEDIUM (papers HIGH) | **PARTIALLY_VERIFIED** |
| R14 | DeepSense provenance, I/Q acquisition, occupancy codes, acquisition-day domains | Uvaydov et al., INFOCOM 2021, pp. 1–10, DOI 10.1109/INFOCOM42981.2021.9488764 [`uvaydov2021deepsense`]; official GitHub record [`wineslab2021deepsensedataset`] | Official README documents 32 `.bin` files = 16 four-bit occupancy combinations × 2 days with day-tagged filenames (e.g., `1101_day2.bin`), and states the two days used different transmitter orientations (SNR/channel diversity) — directly supporting the day-shift protocol and the fixed-orientation context | HIGH | **VERIFIED** |
| R15 | JamShield provenance, telemetry features, jammer and benign scenarios | Panitsas et al., **ICC 2025, pp. 1067–1072, DOI 10.1109/ICC52391.2025.11161395** [`panitsas2025jamshield`]; IEEE DataPort DOI 10.21227/5hzf-w161 + GitHub [`panitsas2024jamshielddataset`] | README/DataPort: constant/random/reactive jammers plus no-jammer (benign) sets under LOS/NLOS; 40→20 tabular features incl. packet/byte counters, per-antenna RSSI, noise floor, SINR; CSV format. **Now peer-reviewed at IEEE ICC 2025 — supersedes the arXiv-only citation-plan skeleton.** No dataset license stated (flag in data availability) | HIGH | **VERIFIED** |
| R16 | Selective prediction / risk-coverage as complement | El-Yaniv & Wiener, JMLR 11(53):1605–1641, 2010 [`elyaniv2010foundations`]; Geifman & El-Yaniv, NIPS 2017 [`geifman2017selective`] | Risk–coverage trade-off formalization; deep-network selective classification with guaranteed risk. "Complements calibration/OOD" remains the manuscript's framing | HIGH | **VERIFIED** |
| R17 | Density/typicality responses to score inversion | Nalisnick et al., ICLR 2019 [`nalisnick2019deep`]; Ren et al., NeurIPS 2019 [`ren2019likelihood`] | Generative models assigning OOD data higher likelihood than training data (canonical one-sided-score inversion); likelihood-ratio correction restoring detection. The separate typicality paper (arXiv:1906.02994) is **arXiv-only** — cite as preprint or omit | HIGH | **VERIFIED** |

## Highest-risk references

1. **R13 (ElectroSense)** — the only dataset item not fully closed: the six-class taxonomy is documented in the official framework code rather than the Zenodo record, and the source taxonomy contains a seventh `unkn` label the manuscript does not mention. Resolve by citing the framework paper/code for the taxonomy and scoping the class claim to the converted OpenEW-SA subset. The Zenodo license is custom (not CC) with mandatory citation wording.
2. **R12 (paired bootstrap)** — cite Efron & Tibshirani + Dietterich as underpinnings; do not imply either source prescribes the exact stratified shared-index design.
3. **R15 (JamShield)** — resolved favorably, but the manuscript must switch from the arXiv preprint to the ICC 2025 proceedings citation, and the dataset's missing license needs a note in the data-availability statement.
4. **R6/R10 attribution scope** — Hendrycks & Gimpel does not propose entropy; Lee et al. does not include the regularizer. Both need one-clause phrasing adjustments when tokens are replaced.

## Replacement map (token → bib keys)

| Token | Replace with |
| --- | --- |
| R1 | `itu2011spectrum`, `rajendran2018electrosense` |
| R2 | `ovadia2019trust`, `nguyen2015fooled` |
| R3 | `shafaei2019biased`, `yang2022openood` |
| R4 | `scheirer2013toward`, `geng2021recent` |
| R5 | `alshawabka2020exposing`, `hanna2022wisig` |
| R6 | `hendrycks2017baseline` (entropy via `ovadia2019trust` or "e.g.") |
| R7 | `guo2017calibration` (+ `ovadia2019trust` in Discussion) |
| R8 | `liu2020energy` |
| R9 | `snell2017prototypical`, `sun2022knn` |
| R10 | `lee2018mahalanobis` |
| R11 | `hendrycks2017baseline`, `liang2018enhancing` (+ `davis2006prroc` optional) |
| R12 | `efron1993bootstrap`, `dietterich1998approximate` (bounded phrasing) |
| R13 | `rajendran2018electrosense`, `scalingi2023framework`, `scalingi2023electrosensepsd` (taxonomy via framework paper/code) |
| R14 | `uvaydov2021deepsense`, `wineslab2021deepsensedataset` |
| R15 | `panitsas2025jamshield` (ICC 2025), `panitsas2024jamshielddataset` |
| R16 | `elyaniv2010foundations`, `geifman2017selective` |
| R17 | `nalisnick2019deep`, `ren2019likelihood` |

After token replacement, re-run `grep -rn "REFERENCE NEEDED" papers/paper2_ood_rf_signal_recognition/` to confirm no token remains (per the checklist in `unresolved_reference_requirements.md`). Token replacement itself is outside this audit's write scope and was not performed.
