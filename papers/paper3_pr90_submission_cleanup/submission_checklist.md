# PR #90 submission-package checklist

This checklist is a handoff, not submission authorization. The scientific analyses, splits, receiver ordering, model weights, and numerical results remain frozen. The repository's internal-review PDF and the two submission-candidate PDFs must be built separately from the same scientific source.

## HUMAN-ONLY decisions

- [ ] Confirm the author list, order, contribution eligibility, and approval by every author.
- [ ] Enter and verify every affiliation.
- [ ] Enter and verify ORCIDs.
- [ ] Designate the corresponding author and verify contact details.
- [ ] Confirm funding sources and required grant wording, or an explicit no-funding statement.
- [ ] Confirm conflicts of interest and the venue-specific disclosure.
- [ ] Approve the exact AI-use disclosure. Verify actual OpenAI Codex and Claude systems/versions, which sections each affected, the extent of generated or edited material, whether separate ChatGPT use occurred, and the venue's citation/disclosure requirements. The manuscript acknowledgment is a **draft**, not an author-approved final statement.
- [ ] Select the target venue (TMLCN or IEEE Access), article type, title, and required submission files.
- [ ] Obtain rights-holder/institutional approval for any derivative-artifact release. In particular, decide whether exact split/support manifests, converted tensors, checkpoints, or predictions may be shared under WiSig terms. Do not interpret a code release as authorization to redistribute RF payload.

## Technical checks before a human submission decision

- [ ] Internal and submission-candidate builds use the same scientific body and numbers; only presentation/identity wording and presentation-only plot titles differ.
- [ ] The submission-candidate main PDFs contain no “OpenEW-SA Internal Review” marker; the internal build may retain it.
- [ ] Author, affiliation, ORCID, and corresponding-author placeholders remain unfilled for human action.
- [ ] The main Figure 2 forest display and the supplementary full 32-receiver display both remain in their frozen receiver order.
- [ ] Composition Table V retains its frozen values, label-dependent oracle warning, and common query-universe disclosure.
- [ ] The SAR-GN row retains the 293/320 reset qualification; no general SAR-failure claim is introduced.
- [ ] SHOT-IM remains described as technically executable on this backbone but not a reproduction of the original source-training recipe; no new target experiment is implied.
- [ ] Source-data and derived-artifact availability statements match actual licence and repository contents. Do not invent a DOI or public payload URL.
- [ ] All three PDFs build without errors, undefined references/citations, overfull boxes, Type 3 fonts, or unembedded fonts, and their key pages have been visually inspected.
- [ ] Numerical lineage guard and relevant tests pass on the final source tree.

IEEE's current journal policy requires disclosure of AI-generated article content in Acknowledgments, with the system, affected article sections, and level of use identified. See the [IEEE Author Center policy](https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/) and [IEEE Access guidance](https://ieeeaccess.ieee.org/authors/preparing-your-article/). This checklist does not substitute for author verification of the actual tool history or final venue rules.
