# Final bibliography audit (submission finalization)

Scope: the frozen `papers/paper3_reviewer_remediation/references_verified.bib`
(SHA-256 `ff1b4c8100fd76507a65b3fe893d533d9a50f822cc3fd9099644d1237de22a4c`).
It has **32** unique entries: 12 with a DOI, 19 with an official or
author/institutional URL, and the ORBIT proceedings entry with neither in
BibTeX. No reference was added, removed, or edited in this finalization.
The older `reference_requirements.md` says 31 because it predates the Yang
receiver-adaptation citation; this is a documentation count, not a missing
manuscript reference.

The frozen [reference-requirements audit](../paper3_reviewer_remediation/reference_requirements.md),
[original source matrix](../paper3_receiver_adaptation_manuscript/reference_requirements.md),
and [PR90 direct receiver-shift check](../paper3_pr90_submission_cleanup/reference_final_audit.md)
provide the earlier verification trail. The final spot checks below used
publisher, proceedings, official dataset, or author/institutional pages. For
DOI-bearing additions, the frozen Crossref deposit snapshot is at the
external `paper3/reviewer_remediation/literature/bibliography/reference_metadata_manifest.json`.
Crossref's deposited year may be the online year rather than the final volume
year (for example Shen); the final issue/volume year is used in BibTeX.

| Entries | Final check and primary source | Disposition |
|---|---|---|
| `wisig`, `orbit` | [UCLA WiSig citation page](https://cores.ee.ucla.edu/wisig/license/) supplies authors, titles, venue, year, volume and pages for both; [IEEE WiSig record](https://ieeexplore.ieee.org/document/9721895/) confirms DOI and pages. [Rutgers ORBIT record](https://www.researchwithrutgers.org/en/publications/overview-of-the-orbit-radio-grid-testbed-for-evaluation-of-next-g/) confirms the conference metadata. | VERIFIED. ORBIT's DOI is not in frozen BibTeX; do not silently insert it under this science freeze. |
| `shen`, `shenlora` | [Shen author publication page](https://junqing-zhang.github.io/research/dataset-code/) confirms final TMC volume 23(7), pp. 7618–7634, 2024 and DOI; [Liverpool JSAC record](https://livrepository.liverpool.ac.uk/id/eprint/3112081) confirms the LoRa paper's five authors, vol. 39(8), pp. 2604–2616, 2021, DOI. | VERIFIED. One institutional PDF cover sheet contains a page typo; final author/institutional publication records agree with frozen BibTeX. |
| `ganrxa`, `yang_receiver_adapt` | [IEEE GAN-RXA record](https://ieeexplore.ieee.org/document/10304266) confirms title, 2024 vol. 10(2), pp. 403–416, DOI; [IEEE Yang record](https://ieeexplore.ieee.org/document/10500834) and its publisher-deposited DOI metadata confirm 2024 vol. 11(13), pp. 24024–24034. | VERIFIED. These are related receiver-shift precedents, not information-matched numerical comparators. |
| `oracle`, `rffsurvey`, `rfmethodology`, `rfchallenges` | [IEEE ORACLE record](https://ieeexplore.ieee.org/document/8737463), [Elsevier Computer Networks issue](https://www.sciencedirect.com/journal/computer-networks/vol/219/suppl/C), and the frozen DOI registry records establish the published metadata. | VERIFIED from prior deposit and publisher records; no new claims or citations. |
| `t3a`, `shot` | [NeurIPS T3A](https://proceedings.neurips.cc/paper/2021/hash/1415fe9fea0fa1e45dddcff5682239a0-Abstract.html) and [PMLR SHOT](https://proceedings.mlr.press/v119/liang20a.html) confirm authors, title, venue/year, and PMLR volume/pages. | VERIFIED. SHOT is cited as prior work, not claimed to have been run. |
| `dann`, `coral`, `groupdro`, `tent`, `groupnorm`, `adamw`, `domainbed`, `wilds`, `betterda`, `eata`, `ttapitfalls`, `sar` | The frozen source matrices point to the JMLR, Springer, CVF, PMLR, ICLR/OpenReview, and author pages, with the published fields recorded in BibTeX. OpenReview's live browser challenge prevented an independent in-browser recheck of several ICLR records today; their earlier primary-source verification remains the basis. | VERIFIED BY FROZEN PRIOR AUDIT; live OpenReview recheck NEEDS HUMAN REVIEW if required at submission. No inferred DOI was added. |
| `calibration`, `evalcal`, `ovadia`, `verifiedcal`, `dirichlet`, `gneiting`, `brier`, `holm` | Prior frozen proceedings/journal audit covers metadata. [AMS Brier publisher page](https://journals.ametsoc.org/view/journals/mwre/78/1/1520-0493_1950_078_0001_vofeit_2_0_co_2.xml) freshly confirms vol. 78(1), pp. 1–3, DOI and author. | VERIFIED from publisher/proceedings and prior audit. |

The bib entries include the author list, title, venue, year, and the volume,
issue, pages and DOI/official URL where these bibliographic fields exist.
Conference proceedings without a journal issue are not assigned a fictitious
issue. No citation was added for the sake of increasing the count.

**Retraction/correction concern:** no correction or retraction notice appeared
on the publisher records spot-checked above. This is *not* a comprehensive
Crossmark/Retraction Watch or publisher-wide screen. Final human reference and
retraction screening remains required immediately before submission. The
inaccessible OpenReview pages and the optional absent ORBIT DOI should be
reviewed by the human submitter; neither is evidence of retraction.
