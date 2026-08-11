# Paper 2 Target Journal Matrix

Candidate journals for "Uncertainty-Calibrated Multi-View RF Signal Recognition for Open-Set Electromagnetic Spectrum Monitoring" (~11-page IEEE-style draft; contribution centered on leak-resistant open-set evaluation protocol, paired bootstrap statistics, and honest mixed/negative results across three public RF datasets).

All facts below come from **official publisher/journal pages only**, accessed **2026-08-11**; source URLs are listed per candidate and collected at the end. No impact factors or acceptance rates are reported anywhere in this file because none were taken from official pages. APCs are as officially stated for the noted submission year and may change.

## Summary table

| # | Journal | Publisher | Scope fit | OA model | APC (official, 2026 unless noted) | Page constraint | Fit for this paper | Major rejection risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | IEEE Trans. Machine Learning in Communications and Networking (TMLCN) | IEEE ComSoc (+CS, SPS, VTS) | GOOD (bullseye: ML for spectrum/signal problems; reproducibility advocated) | Fully OA, CC BY 4.0 | US$2,160 | Not stated on official pages — pre-submission query invited | Excellent | ML-novelty expectations; young journal (2023) |
| 2 | IEEE Access | IEEE | GOOD (multidisciplinary; soundness over novelty) | Fully OA | US$2,160 | No page limit; <20 pp recommended | Very good (explicit "Negative Result" article type) | Low editorially; lower field-specific prestige |
| 3 | IEEE Open Journal of the Communications Society (OJ-COMS) | IEEE ComSoc | GOOD (ML for communications; cognitive/intelligent networks) | Fully OA | US$2,160 (US$2,075 for 2025 submissions) | No page limits; ≤25 pp = regular paper | Good | Communications-novelty lens from ComSoc reviewer pool |
| 4 | IEEE Trans. Cognitive Communications and Networking (TCCN) | IEEE ComSoc (+SPS) | GOOD (cognitive radio / dynamic spectrum access is core) | Hybrid (OA optional) | OA option US$2,800; mandatory US$220/page beyond 10 published pages | 13 pp at submission (16 on revision) | Strong topical fit; higher variance | Transactions novelty bar vs. incremental fusion + mixed results |
| 5 | IEEE Open Journal of Signal Processing (OJSP) | IEEE SPS | GOOD (signal processing applications; reproducibility enforced) | Fully OA | US$2,160 | No hard limit; ≤15 pp recommended | Good (mandatory code capsule aligns with paper values) | Generic SP audience, not spectrum-monitoring specialists; Code Ocean compliance step |
| 6 | Journal on Wireless Communications and Networking (formerly EURASIP JWCN) | Springer Nature | GOOD topically / PARTIAL strategically (non-IEEE; renamed 2026-01-01) | Fully OA | US$2,190 / £1,590 / €1,890 | Not retrievable from official pages this session | Viable fallback | Non-IEEE preference mismatch; mid-rebrand metrics uncertainty |

Evaluated and **not recommended**: IEEE Transactions on Wireless Communications (scope listed but communication-theoretic culture; "advance the theory" bar; 13-page limit, hybrid OA US$2,800, mandatory overlength charges) and IEEE Internet of Things Journal (official scope is IoT-architecture-centric with no spectrum/ML mention; 8-page limit before mandatory US$175/page overlength — an 11-page draft would owe ~US$525; hybrid, OA US$2,695 for 2025).

---

## 1. IEEE Transactions on Machine Learning in Communications and Networking (TMLCN)

- **Publisher:** IEEE Communications Society; co-sponsors: IEEE Computer Society, Signal Processing Society, Vehicular Technology Society.
- **Scope fit:** GOOD — official scope: "advances in machine learning and artificial intelligence (AI) methods and their application to problems across all areas of communications and networking"; CFP topics include ML for "signal detection," "interference mitigation," and "spectrum management … using machine learning." The journal "advocates for reproducible and public sharing of codes, datasets, software, and other artefacts" — a stated editorial value directly matching this paper's core contribution.
- **Article type:** theoretical and practical contributions (no finer taxonomy on official pages).
- **Template:** IEEE article template via IEEE Template Selector; PDF submission.
- **Page/word constraints:** not stated on the official pages checked (scope, information-for-authors, CFP). The journal invites pre-submission queries (eictmlcn@gmail.com) — do this before formatting final length.
- **OA model / APC:** 100% open access, CC BY 4.0, author retains copyright; APC US$2,160 for 2026 submissions; 5%/20% member discounts (non-combinable); low-income-country waivers.
- **Supplementary policy:** not separately stated; artifact submission encouraged (below).
- **Data/code expectations:** authors "strongly encouraged" to include a GitHub link to codes and datasets in the camera-ready and/or submit codes and other experimental artifacts.
- **Fit for this paper:** Excellent — the only IEEE Transactions in this set whose official policy rewards exactly what the paper does well (reproducibility, artifact sharing, ML-for-RF). The frozen-split protocol, traceability matrix, and paired bootstrap become selling points.
- **Major rejection risk:** the CFP "particularly encourages" work that advances both ML and wireless networking simultaneously; reviewers may fault the fusion's ML-methodological novelty. Mitigate by leading with the evaluation-protocol contribution (see `reviewer_risk_register.md` RISK-N1/N2). Young journal (launched 2023) with a short track record.
- **Sources:** comsoc.org TMLCN scope page; TMLCN information-for-authors page; TMLCN call-for-papers page (accessed 2026-08-11).

## 2. IEEE Access

- **Publisher:** IEEE. Multidisciplinary, online-only, gold fully open access; Communications Technology and Signal Processing among its leading categories.
- **Scope fit:** GOOD — trivially in scope (all IEEE fields of interest).
- **Article types:** 16 types including Research Article, Applied Research, Methods, and an explicit **"Negative Result"** type; all types get the same peer review.
- **Template:** IEEE Access double-column template required; Word or LaTeX file plus PDF at submission.
- **Page constraints:** no page limit and no overlength charge; under 20 pages recommended; >20 pages requires an EIC pre-submission inquiry.
- **OA model / APC:** fully (gold) OA; US$2,160 per article plus applicable local taxes.
- **Supplementary policy:** accepted and peer-reviewed with the article (videos ≤100 MB).
- **Data/code expectations:** no explicit mandate found on official pages.
- **Review model:** binary accept/reject, ~4 weeks average to decision, ≥2 reviewers, single-anonymized; official criterion: articles "are not necessarily expected to have a high level of novelty, but they should be distinct from previous publications and technically sound."
- **Fit for this paper:** very good mechanically — the soundness-over-novelty criterion and the Negative Result/Methods article types align with a protocol-rigor, mixed-results contribution; 11 pages is comfortable. Note: Paper 1 targets IEEE Access (repo `papers/paper1_openew_sa/ieee_access/`), so venue diversification between the two papers is worth considering.
- **Major rejection risk:** low on substance; the trade-off is reputational (less field-specific prestige than a ComSoc Transactions) and desk-return for template/compliance issues.
- **Sources:** ieeeaccess.ieee.org home, APC, submission-guidelines, rapid-peer-review, reviewer-guidelines pages (accessed 2026-08-11).

## 3. IEEE Open Journal of the Communications Society (OJ-COMS)

- **Publisher:** IEEE Communications Society.
- **Scope fit:** GOOD — official scope areas include "Big Data and Machine Learning for Communications," "Green, Cognitive, and Intelligent Communications and Networks," "Signal Processing for Communications," "Wireless Communications and Networks"; welcomes theoretical and practical contributions including experiments/prototypes.
- **Article types:** original manuscripts, surveys, tutorials.
- **Template:** Template for IEEE Open Journals (Word + LaTeX); **graphical abstract mandatory** for peer review.
- **Page constraints:** no page limits; ≤25 pages handled as Original Manuscript (2-week reviewer deadline), >25 pages as Long Survey.
- **OA model / APC:** fully OA; US$2,075 for 2025 submissions, US$2,160 for 2026; member discounts; low-income-country support.
- **Supplementary policy:** multimedia, datasets, and other materials accepted via IEEE Author Center procedures.
- **Data/code expectations:** no explicit mandate found.
- **Fit for this paper:** good — ComSoc branding with rapid, experiment-tolerant review and no length constraint.
- **Major rejection risk:** reviewers from the ComSoc pool may apply a communications-systems novelty lens; the paper's center of gravity (OOD evaluation methodology) is adjacent to, not central in, communications research.
- **Sources:** comsoc.org OJ-COMS scope and submit-manuscript pages (accessed 2026-08-11).

## 4. IEEE Transactions on Cognitive Communications and Networking (TCCN)

- **Publisher:** IEEE Communications Society; co-sponsor IEEE Signal Processing Society.
- **Scope fit:** GOOD — topics explicitly include "Machine learning and artificial intelligence for communications and networking" and "Cognitive radio and dynamic spectrum access"; open-set spectrum monitoring maps directly onto the perception/learning/decision framing of a cognitive entity.
- **Article types:** regular Transactions papers; surveys/tutorials.
- **Template:** official IEEE templates via Template Selector; ORCID mandatory.
- **Page constraints:** regular papers max **13 double-column pages at submission** (16 on revision); voluntary US$110/page for first 10 published pages; **mandatory US$220/page beyond 10 published pages** — the ~11-page draft fits submission limits but would incur ~1 page of mandatory overlength at publication.
- **OA model / APC:** hybrid; OA option US$2,800 for 2026 submissions (member discounts non-combinable); traditional no-fee subscription route available.
- **Supplementary / data-code:** no explicit policy found on pages checked.
- **Fit for this paper:** the best classical-prestige topical fit in the set.
- **Major rejection risk:** the Transactions novelty bar — temperature-scaled entropy + nearest-centroid distances may be judged an incremental combination of known OOD components, and mixed/negative results can read as "insufficient advance of the state of the art." Higher-variance bet than #1–#3.
- **Sources:** comsoc.org TCCN scope and submit pages (accessed 2026-08-11).

## 5. IEEE Open Journal of Signal Processing (OJSP)

- **Publisher:** IEEE Signal Processing Society.
- **Scope fit:** GOOD — "theory, algorithms with associated architectures and implementations, and applications related to processing information"; RF signal recognition is squarely signal processing.
- **Article types:** regular papers (no hard length limit; ≤15 pages recommended); Short Papers ≤8 pages + 1 reference page.
- **Template:** OJ-SP template via IEEE Author Center; ORCID required.
- **Page constraints:** no hard limit; 15 or fewer pages recommended.
- **OA model / APC:** fully OA; US$2,160 (2026).
- **Supplementary policy:** graphical abstracts, multimedia, datasets allowed.
- **Data/code expectations:** **enforced, not just encouraged** — papers whose primary contribution involves learning-based models "are required to submit a Code Ocean capsule that includes the models along with code for applying them."
- **Review model:** single-blind, ≥2 reviewers, ~15-week target.
- **Fit for this paper:** good — the mandatory-code policy selects reviewers who value the paper's reproducibility stance.
- **Major rejection risk:** generic signal-processing audience rather than spectrum-monitoring specialists; Code Ocean capsule is an extra compliance step on top of the existing artifact pipeline.
- **Sources:** signalprocessingsociety.org OJSP page and information-for-authors page (accessed 2026-08-11).

## 6. Journal on Wireless Communications and Networking (formerly EURASIP JWCN)

- **Publisher:** Springer Nature. **Status note:** officially renamed from "EURASIP Journal on Wireless Communications and Networking" effective 2026-01-01; active and accepting submissions (recent July–August 2026 publications, open CFPs into November 2026). Target under the new name.
- **Scope fit:** GOOD topically — "bridges science and applications of wireless communications and networking technologies," with emphasis on signal processing techniques. PARTIAL strategically: non-IEEE, and the rename creates indexing/branding continuity uncertainty in 2026.
- **Template:** Springer OA journal format (not IEEE template) — reformatting required.
- **Page constraints / supplementary / data policy:** not retrievable from official pages this session (Springer bot-checks); verify the Submission Guidelines tab manually before any submission.
- **OA model / APC:** fully OA; APC officially stated as £1,590 / US$2,190 / €1,890; no submission fee; CC BY or CC BY-NC-ND, author retains copyright; waivers available.
- **Fit for this paper:** viable fallback if IEEE options are exhausted.
- **Major rejection risk:** low-to-moderate on novelty; main costs are the non-IEEE venue and rebrand uncertainty.
- **Sources:** link.springer.com journal 13638 home and how-to-publish pages (accessed 2026-08-11).

---

## Official source URLs (all accessed 2026-08-11)

- IEEE Access: https://ieeeaccess.ieee.org/ ; https://ieeeaccess.ieee.org/about/article-processing-charges/ ; https://ieeeaccess.ieee.org/authors/submission-guidelines/ ; https://ieeeaccess.ieee.org/about/rapid-peer-review/ ; https://ieeeaccess.ieee.org/reviewers/reviewer-guidelines/
- TCCN: https://www.comsoc.org/publications/journals/ieee-tccn ; https://www.comsoc.org/publications/journals/ieee-tccn/ieee-transactions-cognitive-communications-and-networking-submit
- OJ-COMS: https://www.comsoc.org/publications/journals/ieee-ojcoms ; https://www.comsoc.org/publications/journals/ieee-ojcoms/ieee-open-journal-communications-society-submit-manuscript
- TMLCN: https://www.comsoc.org/publications/journals/ieee-tmlcn ; https://www.comsoc.org/publications/journals/ieee-tmlcn/ieee-transactions-machine-learning-communications-and-networking-information-authors ; https://www.comsoc.org/publications/journals/ieee-tmlcn/call-for-papers
- TWC (evaluated, not recommended): https://www.comsoc.org/publications/journals/ieee-twc ; https://www.comsoc.org/publications/journals/ieee-twc/submit-manuscript
- IoT-J (evaluated, not recommended): https://ieee-iotj.org/ ; https://ieee-iotj.org/wp-content/uploads/2025/07/IoT-Journal-Guidelines-for-Authors.pdf
- OJSP: https://signalprocessingsociety.org/publications-resources/ieee-open-journal-signal-processing ; https://signalprocessingsociety.org/publications-resources/ieee-open-journal-signal-processing/information-authors-ojsp
- JWCN: https://link.springer.com/journal/13638 ; https://link.springer.com/journal/13638/how-to-publish-with-us
- Computer Networks (considered, not shortlisted; aims-and-scope page returned HTTP 403): https://www.sciencedirect.com/journal/computer-networks
