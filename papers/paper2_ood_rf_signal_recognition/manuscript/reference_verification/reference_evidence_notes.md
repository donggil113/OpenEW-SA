# Paper 2 Reference Evidence Notes

Independent literature verification for `unresolved_reference_requirements.md` (R1–R17).
Access date for all web sources: **2026-08-11**. No bibliographic field below is invented; every field was checked against a primary or publisher source (IEEE Xplore, PMLR, proceedings.neurips.cc / papers.nips.cc, JMLR, arXiv abstract pages, Crossref, DBLP, Zenodo, official GitHub records). Where a publisher page was unreachable (bot-check/403), the fallback source used is named explicitly.

Status vocabulary (applied strictly; PARTIALLY_VERIFIED is never silently upgraded):

- **VERIFIED** — metadata fully confirmed from primary/publisher sources AND the source demonstrably supports the manuscript claim.
- **PARTIALLY_VERIFIED** — metadata confirmed but claim support only partial/inferred, or a minor metadata gap remains.
- **UNRESOLVED** — could not be confirmed; do not cite.

General access note for 2026-08-11: OpenReview, ACM DL, Taylor & Francis, and MIT Press Direct blocked automated fetches during this session; where those were the natural publisher pages, metadata was verified via Crossref API, DBLP, JMLR, arXiv, and proceedings.neurips.cc instead, as itemized per entry.

---

## R6 — MSP / entropy confidence baselines

- **STATUS: VERIFIED**
- **Manuscript claim:** Maximum softmax probability and predictive entropy are common post-hoc confidence/OOD baselines computable from an existing classifier (Related Work, "Confidence and calibration").
- **Selected reference:** Dan Hendrycks, Kevin Gimpel. "A Baseline for Detecting Misclassified and Out-of-Distribution Examples in Neural Networks." ICLR 2017 (conference track). No pages/DOI (ICLR 2017 assigns none). OpenReview forum `Hkg4TI9xl`; arXiv:1610.02136.
- **Metadata source:** arXiv abstract page (title, authors, "Published as a conference paper at ICLR 2017"); DBLP record `conf/iclr/HendrycksG17` (confirms ICLR 2017 poster, no DOI).
- **Evidence:** Abstract and Section 1 propose using the maximum softmax class probability to detect misclassified and out-of-distribution examples. Section 2 ("Problem Formulation and Evaluation") introduces AUROC and AUPR as OOD evaluation metrics.
- **Confidence:** HIGH.
- **Drafting caution:** Hendrycks & Gimpel propose **MSP**, not predictive entropy. The manuscript sentence covers both; entropy should be attributed as an established uncertainty measure via a secondary source (Ovadia et al. 2019, verified under R2/R7 notes) or introduced with "e.g.," so the citation does not overreach.

## R7 — Temperature scaling

- **STATUS: VERIFIED**
- **Manuscript claim:** A single scalar temperature fitted on held-out ID validation predictions improves probabilistic calibration while leaving the classifier fixed; calibration is distinct from OOD detection (Related Work; Methods "Temperature scaling"; Discussion).
- **Selected reference:** Chuan Guo, Geoff Pleiss, Yu Sun, Kilian Q. Weinberger. "On Calibration of Modern Neural Networks." Proceedings of the 34th International Conference on Machine Learning, PMLR vol. 70, pp. 1321–1330, 2017. No DOI (PMLR). URL: https://proceedings.mlr.press/v70/guo17a.html
- **Metadata source:** PMLR page (title, authors, volume, pages) plus full PDF.
- **Evidence:** Section 4 states all methods are post-processing steps requiring a hold-out validation set. Section 4.2 (Eq. 9) defines temperature scaling with a single scalar T > 0 optimized by NLL on the validation set, and notes T does not change the softmax argmax, so accuracy is unchanged — exactly the manuscript's usage. Guo et al. also assume train/validation/test come from the same distribution, which supports the manuscript's point that calibration is defined on a specified (ID) distribution.
- **Supporting secondary (calibration ≠ robustness under shift):** Yaniv Ovadia, Emily Fertig, Jie Ren, Zachary Nado, D. Sculley, Sebastian Nowozin, Joshua Dillon, Balaji Lakshminarayanan, Jasper Snoek. "Can you trust your model's uncertainty? Evaluating predictive uncertainty under dataset shift." Advances in Neural Information Processing Systems 32 (NeurIPS 2019). Verified directly against the proceedings page https://proceedings.neurips.cc/paper/2019/hash/8558cb408c1d76621371888657d2eb1d-Abstract.html (title, full author order, volume). No pages/DOI shown on the proceedings page — omit pages.
- **Confidence:** HIGH.

## R8 — Energy score

- **STATUS: VERIFIED**
- **Manuscript claim:** Logit energy as an OOD score (Related Work).
- **Selected reference:** Weitang Liu, Xiaoyun Wang, John D. Owens, Yixuan Li. "Energy-based Out-of-distribution Detection." Advances in Neural Information Processing Systems 33 (NeurIPS 2020). No DOI/pages on the proceedings page. URL: https://proceedings.neurips.cc/paper/2020/hash/f5496252609c43eb8a3d147ab9b9c006-Abstract.html ; arXiv:2010.03759.
- **Metadata source:** proceedings.neurips.cc abstract page; arXiv abstract page.
- **Evidence:** Section 2, Eq. 4 defines the free-energy score E(x; f) = −T·log Σ exp(f_i(x)/T) computed directly from a pre-trained classifier's logits and proposes it as a superior replacement for softmax confidence in OOD detection.
- **Confidence:** HIGH.
- **Note:** the commonly cited page range 21464–21475 was not confirmed on a publisher page and is omitted.

## R9 — Prototype / nearest-centroid / feature-distance scoring

- **STATUS: VERIFIED**
- **Manuscript claim:** Prototype/nearest-centroid approaches score a sample by its position relative to class-conditional training features; Euclidean and cosine distances encode different geometry (Related Work "Feature geometry and score fusion"; Methods).
- **Selected references:**
  1. Jake Snell, Kevin Swersky, Richard Zemel. "Prototypical Networks for Few-shot Learning." Advances in Neural Information Processing Systems 30 (NIPS 2017). No DOI/pages on proceedings page. URL: https://proceedings.neurips.cc/paper/2017/hash/cb8da6767461f2812ae4290eac7cbc42-Abstract.html ; arXiv:1703.05175.
  2. Yiyou Sun, Yifei Ming, Xiaojin Zhu, Yixuan Li. "Out-of-Distribution Detection with Deep Nearest Neighbors." Proceedings of the 39th International Conference on Machine Learning, PMLR vol. 162, pp. 20827–20840, 2022. URL: https://proceedings.mlr.press/v162/sun22d.html
- **Metadata source:** proceedings.neurips.cc abstract page (Snell); PMLR page (Sun).
- **Evidence:** Snell et al. Section 2.2 (Eq. 1) defines class prototypes as mean vectors of embedded class samples with distance-based classification; Sections 2.3/2.6 contrast squared Euclidean (a Bregman divergence) with cosine (not a Bregman divergence), directly supporting "different geometry." Sun et al. establish non-parametric feature-space distance as an OOD score, covering the OOD-scoring use of feature distance.
- **Confidence:** HIGH.
- **Note:** Snell is a few-shot paper — it grounds the centroid mechanism and geometry, while Sun grounds the OOD application. Mensink et al. (TPAMI 2013) and Techapanurak (ACCV 2020) were considered but not needed and were not metadata-verified; do not cite them without separate verification.

## R10 — Shared-covariance Mahalanobis OOD scoring

- **STATUS: VERIFIED**
- **Manuscript claim:** Shared-covariance (tied) Mahalanobis distance to class means as an OOD score, with a diagonal regularizer for numerical stability (Related Work; Methods "Feature-distance scoring").
- **Selected reference:** Kimin Lee, Kibok Lee, Honglak Lee, Jinwoo Shin. "A Simple Unified Framework for Detecting Out-of-Distribution Samples and Adversarial Attacks." Advances in Neural Information Processing Systems 31 (NeurIPS 2018), pp. 7167–7177. URL: https://proceedings.neurips.cc/paper_files/paper/2018/hash/abdeb6f575ac5c6676b747bca8d09cc2-Abstract.html ; arXiv:1807.03888.
- **Metadata source:** proceedings.neurips.cc abstract page; arXiv abstract page ("Accepted in NIPS 2018"). Page range 7167–7177 sourced from the NeurIPS-31 volume record (one notch below the abstract page in verification strength).
- **Evidence:** Section 2.1 defines class-conditional Gaussians with a tied covariance Σ, empirical class means, the pooled covariance estimator, and the confidence score as Mahalanobis distance to the closest class mean — precisely the model the manuscript adopts.
- **Confidence:** HIGH.
- **Drafting caution:** the **diagonal regularizer and pseudo-inverse are the manuscript's implementation details, not Lee et al.'s** — phrase as "following [Lee et al. 2018], with added covariance regularization for numerical stability." Optional follow-up (arXiv-only, cite as preprint if used): Ren et al., "A Simple Fix to Mahalanobis Distance for Improving Near-OOD Detection," arXiv:2106.09022, 2021.

## R11 — AUROC / AUPR-OOD / FPR95 interpretation

- **STATUS: VERIFIED**
- **Manuscript claim:** AUROC, AUPR with OOD as the positive class, and FPR at 95% OOD TPR summarize different aspects of ranking and operating behavior (Related Work "Statistical evaluation of OOD scores"; Methods "OOD metrics").
- **Selected references:**
  1. Hendrycks & Gimpel, ICLR 2017 (metadata as under R6): Section 2 defines AUROC as threshold-independent ranking probability and AUPR as base-rate-sensitive, explicitly noting the positive class must be specified and reporting OOD-as-positive variants.
  2. Shiyu Liang, Yixuan Li, R. Srikant. "Enhancing The Reliability of Out-of-distribution Image Detection in Neural Networks." ICLR 2018. No DOI/pages. OpenReview forum `H1VGkIxRZ`; arXiv:1706.02690. Section 4.3 defines "FPR at 95% TPR" alongside AUROC and AUPR-In/AUPR-Out.
- **Metadata source:** arXiv abstract pages (Comments fields confirm ICLR acceptance); DBLP. OpenReview and ACM DL were blocked this session.
- **Optional third (AUPR vs AUROC under imbalance):** Jesse Davis, Mark Goadrich. "The Relationship Between Precision-Recall and ROC Curves." Proc. 23rd ICML, 2006, pp. 233–240, DOI 10.1145/1143844.1143874 — metadata confirmed via DBLP (`conf/icml/DavisG06`), not the ACM landing page (403). Treat as verified-via-DBLP.
- **Confidence:** HIGH.

## R12 — Paired stratified bootstrap intervals

- **STATUS: PARTIALLY_VERIFIED**
- **Manuscript claim:** Paired resampling with shared resamples preserves within-sample dependence when methods score the same observations; percentile intervals quantify uncertainty conditional on the observed data (Related Work; Methods "Bootstrap statistical analysis").
- **Selected references:**
  1. Bradley Efron, Robert J. Tibshirani. *An Introduction to the Bootstrap.* Monographs on Statistics and Applied Probability 57. New York: Chapman & Hall, 1993 (xvi + 436 pp., print ISBN 0-412-04231-2). Electronic edition Chapman and Hall/CRC 1994, DOI 10.1201/9780429246593.
  2. Thomas G. Dietterich. "Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms." Neural Computation, vol. 10, no. 7, pp. 1895–1923, 1998. DOI 10.1162/089976698300017197.
- **Metadata source:** Crossref records for both DOIs; DBLP `journals/neco/Dietterich98`; print-edition details cross-checked against a published Psychometrika book review (Cambridge Core PDF). Taylor & Francis and MIT Press pages were blocked this session.
- **Evidence:** Efron & Tibshirani Chapter 13 ("Confidence intervals based on bootstrap percentiles," pp. 168–177 per the published table of contents) is the canonical percentile-interval source. Dietterich addresses statistical comparison of two learning algorithms evaluated on the same data via paired tests.
- **Why not VERIFIED:** the specific composite procedure — *stratified* ID/OOD resampling with *shared resample indices across methods* — is a standard construction assembled from these sources, not a named procedure quotable from either; and full-text section verification was via Crossref/TOC rather than publisher full text. The manuscript should cite these as the underpinnings of the design, not as sources that prescribe the exact procedure.
- **Year caveat:** DOI 10.1201/9780429246593 carries year 1994 (electronic edition); cite the 1993 print or keep DOI+1994 consistently.
- **Confidence:** MEDIUM.

## R16 — Selective prediction / risk-coverage

- **STATUS: VERIFIED**
- **Manuscript claim:** Selective-prediction / risk-coverage evaluation complements calibration and OOD detection (Discussion).
- **Selected references:**
  1. Ran El-Yaniv, Yair Wiener. "On the Foundations of Noise-free Selective Classification." Journal of Machine Learning Research, vol. 11(53), pp. 1605–1641, 2010. No DOI (JMLR). URL: https://www.jmlr.org/papers/v11/el-yaniv10a.html
  2. Yonatan Geifman, Ran El-Yaniv. "Selective Classification for Deep Neural Networks." Advances in Neural Information Processing Systems 30 (NIPS 2017). No pages/DOI. URL: https://papers.nips.cc/paper_files/paper/2017/hash/4a8423d5e91fda00bb7e46540e2b0cf1-Abstract.html
- **Metadata source:** JMLR page (volume, issue, pages); papers.nips.cc abstract page (title, authors, volume).
- **Evidence:** El-Yaniv & Wiener's abstract centers on the risk–coverage trade-off in classification with a reject option — the source of the risk-coverage framing. Geifman & El-Yaniv extend selective classification to deep networks with guaranteed-risk selection.
- **Drafting caution:** neither paper itself discusses calibration or OOD detection; the "complements" framing is the manuscript's, which is fine as long as the citation supports only the selective-prediction concept.
- **Confidence:** HIGH.

## R17 — Density/typicality responses to score inversion

- **STATUS: VERIFIED**
- **Manuscript claim:** Two-sided tail scores and density/typicality models are candidate prespecified responses to domain-shift score inversion (Discussion "Geometry can invert under domain shift").
- **Selected references:**
  1. Eric Nalisnick, Akihiro Matsukawa, Yee Whye Teh, Dilan Gorur, Balaji Lakshminarayanan. "Do Deep Generative Models Know What They Don't Know?" ICLR 2019. No DOI/pages. arXiv:1810.09136.
  2. Jie Ren, Peter J. Liu, Emily Fertig, Jasper Snoek, Ryan Poplin, Mark A. DePristo, Joshua V. Dillon, Balaji Lakshminarayanan. "Likelihood Ratios for Out-of-Distribution Detection." Advances in Neural Information Processing Systems 32 (NeurIPS 2019). URL: https://papers.nips.cc/paper_files/paper/2019/hash/1e79596878b2320cac26dd792a6c51c9-Abstract.html
- **Metadata source:** arXiv abstract page (ICLR 2019 in Comments); papers.nips.cc abstract page (title, full author list, volume).
- **Evidence:** Nalisnick et al. demonstrate that deep generative models can assign *higher* likelihood to OOD data (CIFAR-10-trained models scoring SVHN above training data) — the canonical one-sided-score inversion, directly analogous to the DeepSense result, motivating two-sided/typicality corrections. Ren et al. propose a likelihood-ratio score that restores OOD detection where raw density fails.
- **Important negative finding:** the typicality paper (Nalisnick et al., "Detecting Out-of-Distribution Inputs to Deep Generative Models Using Typicality," arXiv:1906.02994) is **arXiv-only** — DBLP lists it solely as an informal CoRR publication, and no accepted-venue record was found (OpenReview shows an ICLR 2020 *submission*, decision page blocked). If the manuscript cites it for the phrase "typicality," it must be cited as a preprint; the two peer-reviewed selections above are sufficient on their own.
- **Confidence:** HIGH.

---

## R13 — ElectroSense dataset provenance (STRICT)

- **STATUS: PARTIALLY_VERIFIED**
- **Manuscript claim:** ElectroSense provides processed PSD features for signal-technology recognition with classes DAB, DVB-T, FM, LTE (ID) and GSM, TETRA (OOD), collected via a crowdsensed sensor network (Datasets section).
- **Paper references (both fully verified):**
  1. S. Rajendran, R. Calvo-Palomino, M. Fuchs, B. Van den Bergh, H. Cordobés, D. Giustiniano, S. Pollin, V. Lenders. "Electrosense: Open and Big Spectrum Data." *IEEE Communications Magazine*, vol. 56, no. 1, pp. 210–217, 2018. DOI 10.1109/MCOM.2017.1700200 (the "2017" in the DOI reflects online-first; the issue is Jan 2018 — correct as-is). Verified via DBLP record `journals/cm/RajendranCFBCGP18` mirroring IEEE metadata.
  2. A. Scalingi, D. Giustiniano, R. Calvo-Palomino, N. Apostolakis, G. Bovet. "A Framework for Wireless Technology Classification using Crowdsensing Platforms." *IEEE INFOCOM 2023*, pp. 1–10. DOI 10.1109/INFOCOM53939.2023.10228867 — DOI confirmed resolving to IEEE Xplore document 10228867; DBLP `conf/infocom/ScalingiGCAB23`. (IEEE/DBLP render "using" lowercase in the title.)
- **Official dataset record:** Zenodo, "ElectroSense PSD Spectrum Dataset," DOI 10.5281/zenodo.7521246, v1, published 2023-01-10; sole listed creator Alessio Scalingi (IMDEA Networks Institute); files: `DATASET LICENCE`, `README.md`, `spectrum_bands.tar.gz` (1.7 GB). **License is a custom academic license, not CC** (as-is, mandatory citation, redistribution only with license pass-through; the license file self-names the dataset "Electrosense PSD Spectrum Bands Dataset"). Companion framework repo: https://github.com/electrosense/PSD-technology-classification-framework (BSD 3-Clause + citation requirement), which links to this Zenodo DOI.
- **Evidence:** The Zenodo description confirms PSD data from RTL-SDR sweeps (24 MHz–1.7 GHz in 2 MHz chunks) collected by 47 sensors across Europe with labeled licensed-band portions — supporting "processed PSD" and "crowdsensed sensor network." **The six-class enumeration is NOT stated on the Zenodo record** (its text names only examples such as "FM Bands"). The class set is confirmed in the official framework code `TCpackage/TechClass.py`: `{0:'dab', 1:'dvbt', 2:'fm', 3:'gsm', 4:'lte', 5:'tetra', 6:'unkn'}` — the six claimed classes **plus a seventh `unkn` label**.
- **Why not VERIFIED:** the specific class taxonomy the manuscript relies on is documented in the official companion code, not in the dataset record text; and the taxonomy includes an `unkn` class the manuscript does not mention.
- **Confidence:** MEDIUM (papers HIGH; class-set provenance via official code).
- **Drafting cautions:** (1) cite the framework paper/repo — not the Zenodo record — for the class taxonomy; (2) if class counts matter anywhere, acknowledge the `unkn` label's existence in the source taxonomy or state that the converted OpenEW-SA subset uses the six named technology classes; (3) the framework GitHub README cites its own paper with a wrong title ("Spectrum Classification") — use the DBLP/IEEE title.

## R14 — DeepSense dataset provenance (STRICT)

- **STATUS: VERIFIED**
- **Manuscript claim:** DeepSense provides I/Q windows labeled by 4-bit binary WiFi occupancy codes (e.g., `0000`, `0001`, `0010`, `0100`), collected on multiple acquisition days usable as a day-1 vs day-2 domain shift (Datasets section).
- **Paper reference:** D. Uvaydov, S. D'Oro, F. Restuccia, T. Melodia. "DeepSense: Fast Wideband Spectrum Sensing Through Real-Time In-the-Loop Deep Learning." *IEEE INFOCOM 2021*, pp. 1–10. DOI 10.1109/INFOCOM42981.2021.9488764 — DOI confirmed resolving to IEEE Xplore document 9488764; DBLP `conf/infocom/UvaydovDRM21`; identical citation appears in the official dataset README.
- **Official dataset record:** https://github.com/wineslab/deepsense-spectrum-sensing-datasets (WiNES Lab, Northeastern University), MIT license. Data files hosted at the Northeastern University Digital Repository: SDR 802.11a/g handle `neu:n009w2985`, simulated LTE-M handle `neu:n009w299f`; DeepSense collection `neu:n009w292h`. (DRS landing pages returned HTTP 403 to automated fetch; DRS-side metadata verified via search snippets only.)
- **Evidence:** The README documents BOTH critical elements verbatim: 32 `.bin` files, "16 for the first day and 16 for the second day each of the 16 representing a different combination of bandwidth occupation (i.e. `1101_day2.bin` means the first, second, and fourth channels are occupied, collected on the second day)" — i.e., all 16 four-bit occupancy codes exist per day, with day provenance in the filename; and "Data was collected from two separate days with two different transmitter orientations to give the dataset diversity in the SNR and channel effects" — a documented inter-day domain difference, which directly supports using day as the shift variable (and is relevant context for the manuscript's inversion result: the days differ by transmitter orientation, not merely time).
- **Confidence:** HIGH.
- **Notes:** no dataset DOI exists — cite GitHub + DRS handles. Exact binary I/Q format beyond `.bin` + provided conversion scripts (`bin2hdf5.py`, `preprocessing.py`) was not independently parsed.

## R15 — JamShield dataset provenance (STRICT)

- **STATUS: VERIFIED**
- **Manuscript claim:** JamShield provides tabular radio/network telemetry for jamming/interference detection with multiple benign and jammer scenarios (Datasets section).
- **Paper reference (important correction — now peer-reviewed):** I. Panitsas, Y. Yigit, L. Tassiulas, L. Maglaras, B. Canberk. "JamShield: A Machine Learning Detection System for Over-the-Air Jamming Attacks." *ICC 2025 – IEEE International Conference on Communications*, 2025, pp. 1067–1072. DOI 10.1109/ICC52391.2025.11161395 — IEEE Xplore document 11161395 confirmed; DBLP `conf/icc/PanitsasYTMC25`. The arXiv preprint (arXiv:2507.11483, submitted 2025-07-15, "Accepted for presentation at IEEE ICC 2025") matches in title/authors. **Cite the ICC 2025 version, not arXiv-only** — this supersedes the Paper 1 citation-plan skeleton.
- **Official dataset record:** IEEE DataPort, "JamShield Dataset," DOI 10.21227/5hzf-w161, published 2024-10-26, CSV format (~9.45 MB), hosted on GitHub: https://github.com/panitsasi/JamShield-Dataset (owner panitsasi / Ioannis Panitsas, Yale; created 2024-10-15). **No explicit license found** (GitHub license field null; none visible on DataPort) — flag in the data-availability statement.
- **Evidence:** README documents scenario organization: three implemented jammer types (constant, random, reactive) with varying output power and jamming signals, plus datasets "without the presence of a jammer" (benign), under LOS and NLOS propagation configurations. Telemetry: 40 features reduced to 20, including tx/rx packet and byte counters, retries/failures, per-antenna RSSI, noise-floor measurement, and per-antenna SINR — matching "tabular radio/network telemetry." CSV format confirmed by IEEE DataPort.
- **Confidence:** HIGH.
- **Notes:** the manuscript's specific retained/held-out scenario partition is an OpenEW-SA construction fixed in split manifests — the public record supports scenario diversity, not the particular partition (correctly described in the manuscript as project-internal).

---

## R1 — Operational variability of RF spectrum monitoring

- **STATUS: VERIFIED**
- **Manuscript claim:** Operational RF spectrum monitors encounter changing emitters, receivers, sites, propagation conditions, acquisition schedules, and interference regimes (Introduction).
- **Selected references:**
  1. International Telecommunication Union, Radiocommunication Bureau. *Handbook on Spectrum Monitoring*, Edition 2011 (fifth edition). Geneva: ITU, 2011. ISBN 92-61-13501-3, 674 pp. No DOI (ITU uses handles). Official URL: https://www.itu.int/pub/R-HDB-23 (handle: http://handle.itu.int/11.1002/pub/80399e8b-en). The 2011 edition is confirmed as the latest complete edition on ITU's official page as of 2026-08-11.
  2. Rajendran et al., "Electrosense: Open and Big Spectrum Data," IEEE Communications Magazine 56(1):210–217, 2018, DOI 10.1109/MCOM.2017.1700200 (full verification under R13).
- **Metadata source:** ITU publication pages (itu.int/pub/R-HDB-23 and R-HDB-23-2011), ITU iLibrary, and the official ITU PDF title page/preface. ElectroSense: doi.org resolution to IEEE document 8121869 + DBLP + Semantic Scholar API.
- **Evidence:** Verified from the official ITU PDF's preface and table of contents: Ch. 1 "Spectrum monitoring as a key function of a spectrum management system," Ch. 2 covers organization/physical structures (sites/stations), Ch. 3 monitoring equipment and automation (receivers/acquisition), Ch. 4 measurements including occupancy measurement scheduling, Ch. 5 specific monitoring systems and procedures — the authoritative operational description of monitoring across sites, equipment, schedules, and interference handling. The ElectroSense abstract describes a crowdsourced network of geographically dispersed, heterogeneous low-cost sensors collecting spectrum data over time and geography.
- **Confidence:** HIGH.

## R2 — Overconfidence under shift; calibration ≠ OOD separability

- **STATUS: VERIFIED**
- **Manuscript claim:** Closed-set classifiers can be overconfident under distribution shift, and calibration differs from OOD separability (Introduction).
- **Selected references:**
  1. Yaniv Ovadia, Emily Fertig, Jie Ren, Zachary Nado, D. Sculley, Sebastian Nowozin, Joshua Dillon, Balaji Lakshminarayanan, Jasper Snoek. "Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift." Advances in Neural Information Processing Systems 32 (NeurIPS 2019). No pages/DOI on the proceedings page. URL: https://papers.nips.cc/paper_files/paper/2019/hash/8558cb408c1d76621371888657d2eb1d-Abstract.html (also independently confirmed against proceedings.neurips.cc in this audit).
  2. Anh Nguyen, Jason Yosinski, Jeff Clune. "Deep Neural Networks Are Easily Fooled: High Confidence Predictions for Unrecognizable Images." IEEE CVPR 2015, pp. 427–436. DOI 10.1109/CVPR.2015.7298640.
- **Metadata source:** official NeurIPS proceedings abstract page (Ovadia); DBLP `conf/cvpr/NguyenYC15` + doi.org resolution to IEEE document 7298640 + arXiv:1412.1897 (Nguyen; the CVF Open Access page returned 403).
- **Evidence:** Ovadia et al. benchmark predictive-uncertainty methods under dataset shift and find accuracy and calibration degrade with increasing shift, and that post-hoc calibration fitted on ID validation data does not fix behavior under shift — supporting both halves of the claim. Nguyen et al. demonstrate ≥99%-confidence predictions on unrecognizable images — the canonical closed-set overconfidence result.
- **Confidence:** HIGH.

## R3 — Leak-free OOD evaluation protocol design

- **STATUS: VERIFIED**
- **Manuscript claim:** OOD score orientation, normalization, model selection, and thresholds should be fixed without target-test OOD labels to avoid leakage and overstated results (Introduction).
- **Selected references:**
  1. Alireza Shafaei, Mark Schmidt, James J. Little. "A Less Biased Evaluation of Out-of-distribution Sample Detectors." British Machine Vision Conference (BMVC 2019), Cardiff, UK. Paper 0333; no pages/DOI (BMVC online proceedings assign none). URL: https://bmvc2019.org/wp-content/uploads/papers/0333-paper.pdf ; arXiv:1809.04729.
  2. Jingkang Yang et al. (16 authors). "OpenOOD: Benchmarking Generalized Out-of-Distribution Detection." NeurIPS 2022 Datasets and Benchmarks Track. URL: https://papers.nips.cc/paper_files/paper/2022/hash/d201587e3a84fc4761eadc743e9b3f35-Abstract-Datasets_and_Benchmarks.html
- **Metadata source:** DBLP `conf/bmvc/ShafaeiSL19` + arXiv abstract page + ar5iv full text (Shafaei; the bmvc2019.org PDF link timed out on direct fetch but is DBLP-confirmed); official NeurIPS proceedings page (OpenOOD, full author list confirmed).
- **Evidence:** Shafaei et al. Section 3 argues that tuning the reject function/threshold on outliers from the same distribution used at test time overestimates performance, and their OD-test protocol requires the validation outlier set to differ from the evaluation outlier set; Section 4 shows near-perfect methods drop to ~68% mean accuracy under the unbiased scheme — the most direct peer-reviewed support for the no-test-OOD-tuning principle. OpenOOD supports the standardized-protocol motivation ("unfair comparisons and inconclusive results" without a unified benchmark).
- **Confidence:** HIGH (Shafaei); MEDIUM for OpenOOD's support of the specific no-leakage point (abstract-level).

## R4 — Open-set recognition definition and scope

- **STATUS: VERIFIED**
- **Manuscript claim:** Definition and scope of open-set recognition — known-class classification plus rejection of unknown classes absent from training (Related Work).
- **Selected references:**
  1. Walter J. Scheirer, Anderson de Rezende Rocha, Archana Sapkota, Terrance E. Boult. "Toward Open Set Recognition." IEEE TPAMI, vol. 35, no. 7, pp. 1757–1772, 2013. DOI 10.1109/TPAMI.2012.256.
  2. Chuanxing Geng, Sheng-Jun Huang, Songcan Chen. "Recent Advances in Open Set Recognition: A Survey." IEEE TPAMI, vol. 43, no. 10, pp. 3614–3631, 2021. DOI 10.1109/TPAMI.2020.2981604.
- **Metadata source:** DBLP records `journals/pami/ScheirerRSB13` and `journals/pami/GengHC21` + doi.org resolutions to IEEE documents 6365193 and 9040673 + author-hosted preprint / Semantic Scholar abstracts.
- **Evidence:** Scheirer et al. define OSR ("incomplete knowledge of the world is present at training time, and unknown classes can be submitted to an algorithm during testing") and formalize it as balancing empirical risk against open-space risk — the original formal definition. Geng et al. survey the field and situate OSR relative to zero-shot learning, rejection, and open-world recognition.
- **Confidence:** HIGH.
- **Drafting caution:** published title is "Toward Open Set Recognition" (not "Towards" — the author-hosted preprint header differs from the published form). Geng et al.: cite 2021 (versioned issue), not the 2020 early-access date.

## R5 — RF-specific feature-distribution shift

- **STATUS: VERIFIED**
- **Manuscript claim:** Waveform, sensor, site, day, channel, and interference changes alter the RF feature distribution independently of the recognition task (Related Work).
- **Selected references:**
  1. Amani Al-Shawabka, Francesco Restuccia, Salvatore D'Oro, Tong Jian, Bruno Costa Rendon, Nasim Soltani, Jennifer Dy, Stratis Ioannidis, Kaushik Chowdhury, Tommaso Melodia. "Exposing the Fingerprint: Dissecting the Impact of the Wireless Channel on Radio Fingerprinting." IEEE INFOCOM 2020, pp. 646–655. DOI 10.1109/INFOCOM41043.2020.9155259.
  2. Samer Hanna, Samurdhi Karunaratne, Danijela Cabric. "WiSig: A Large-Scale WiFi Signal Dataset for Receiver and Channel Agnostic RF Fingerprinting." IEEE Access, vol. 10, pp. 22808–22818, 2022. DOI 10.1109/ACCESS.2022.3154790.
- **Metadata source:** DBLP `conf/infocom/Al-ShawabkaRDJR20` and `journals/access/HannaKC22` + doi.org resolutions to IEEE documents 9155259 and 9721895 + Semantic Scholar API / arXiv:2112.15363.
- **Evidence:** Al-Shawabka et al.: on >7 TB from 20 devices across anechoic-chamber and real-world testbeds over several days, CNN fingerprinting accuracy collapses across days/channel conditions (85%→9% in the reported case) while the device-identity task is unchanged — direct evidence of day/channel-induced feature shift. Hanna et al.: on 10M packets from 174 transmitters and 41 receivers over a month, "changing receivers, or using signals captured on a different day can significantly degrade a trained classifier's performance" — direct receiver- and day-shift evidence.
- **Confidence:** HIGH.
- **Drafting caution:** neither paper makes the meta-claim that computer-vision OOD evidence "is not automatically transferable" to RF — that framing is the manuscript's inference. Phrase the cited sentence as "RF feature distributions shift with channel, receiver, and day [refs]" and keep the transferability remark as the authors' own argument.
