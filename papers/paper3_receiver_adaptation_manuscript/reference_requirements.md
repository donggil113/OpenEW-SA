# Verified reference requirements

Sources were checked against primary publisher, institutional or author-maintained records before manuscript use. BibTeX contains no guessed DOI. The IEEE main package and references_verified.bib are identical bibliographies.

| Key | Citation-dependent statement | Primary verification / exact location |
|---|---|---|
| wisig | Multi-receiver/day RF fingerprinting dataset, receiver/channel dependence, attribution | DOI 10.1109/ACCESS.2022.3154790; [official UCLA licence/citation page](https://cores.ee.ucla.edu/wisig/license/) Citation / License |
| orbit | ORBIT testbed origin, required acknowledgement | Same official WiSig citation page, ORBIT reference; WCNC 2005 proceedings citation |
| shen | Receiver-agnostic collaborative RFF is prior work, not a new problem | [Liverpool institutional record](https://livrepository.liverpool.ac.uk/3176924/), title/authors and final TMC record; DOI 10.1109/TMC.2023.3340039 |
| shenlora | LoRa spectrogram/CFO-aware RFF prior work | [Liverpool record](https://livrepository.liverpool.ac.uk/id/eprint/3112081), final JSAC metadata; DOI 10.1109/JSAC.2021.3087250. Do not substitute an earlier conference PDF's title |
| t3a | Pseudo-label / entropy-filtered classifier-template adjustment | [NeurIPS 2021 proceedings](https://proceedings.neurips.cc/paper/2021/hash/1415fe9fea0fa1e45dddcff5682239a0-Abstract.html), paper method; official code lineage audited in PR85 |
| dann | Gradient-reversal domain-adversarial source objective | [JMLR 17(59)](https://jmlr.org/papers/v17/15-239.html), method and author list |
| coral | Covariance alignment objective | [Springer chapter](https://doi.org/10.1007/978-3-319-49409-8_35), ECCV Workshops 2016, pp.443–450 |
| groupdro | Worst-group robust training and regularization dependence | [Official authors' implementation](https://github.com/kohpangwei/group_DRO), README / ICLR 2020 paper; arXiv:1911.08731 |
| tent | Entropy minimization over permitted normalization parameters/statistics | [Official ICLR paper](https://openreview.net/pdf/4de0af9691a5dcc52de7de756676fded33d037ef.pdf), adaptation method; source code audited in PR85/88 |
| groupnorm | GroupNorm distinction from BatchNorm state | [CVF ECCV 2018 paper](https://openaccess.thecvf.com/content_ECCV_2018/html/Yuxin_Wu_Group_Normalization_ECCV_2018_paper.html), normalization definition |
| adamw | Decoupled weight decay optimizer | [Authors' paper](https://arxiv.org/abs/1711.05101), ICLR 2019 metadata and method |
| guo | Confidence calibration/ECE definition | [PMLR ICML 2017](https://proceedings.mlr.press/v70/guo17a.html), calibration definitions |
| holm | Step-down multiple comparison adjustment | [Original journal record](https://www.jstor.org/stable/4615733), Scandinavian Journal of Statistics 6(2), 65–70 (1979) |

AdaBN is named only as an audited exclusion under the frozen backbone, not reproduced. Its source audit is preserved in PR88 literature_and_baseline_freeze.md; the manuscript attributes no accuracy result to it.

## Non-literature statements

All claims about this study's conversion, architecture, optimizer, splits, information boundaries, metrics and results require repository evidence, not a citation to an unrelated original method. See numerical_structural_traceability.md, claim_evidence_ledger.md and the complete numerical matrix. Related OpenEW-SA publication metadata and authorship are unresolved and must be supplied before submission. No blog or secondary summary supplies a scientific claim.
