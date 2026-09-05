# PDF technical audit

**PASS for internal-review production. Not a submission-readiness decision.**

| Property | Main IEEEtran | Supplement | Operator checklist |
|---|---|---|---|
| Pages | 9 | 6 | 1 |
| Paper | US Letter portrait, 612×792 pt | US Letter landscape, 792×612 pt | US Letter portrait |
| Compile errors | 0 | 0 | 0 |
| Undefined citations / references | 0 / 0 | 0 / 0 | 0 / 0 |
| Overfull boxes | 0 | 0 | 0 |
| Underfull warnings | 1 page-output vbox | 0 | 0 |
| Type 3 fonts | 0 | 0 | 0 |
| All fonts embedded | Yes | Yes | Yes |

Main uses IEEEtran journal format. Supplement/checklist use scalable Latin Modern. PDF and PNG assets were visually inspected, including dense supplementary pages at higher resolution. The one main underfull warning does not clip or overlap content. Main includes six figures/six tables and 13 verified references; supplement contains two further figures and the full receiver-seed lookup.

Build: latexmk / pdfTeX (TeX Live 2023 Debian), IEEEtran; checks with pdfinfo, pdffonts, log scanning and pdftoppm. Generated PDF SHA256 values, including the independent fresh-source build, are recorded in validation_summary.json and external manuscript audit reports. Document CreationDate/trailer metadata varies between builds; text and generated figure/table sources remain reproducible. Byte-identical PDF output is not claimed.

Delivery PDFs: /mnt/d/openew_sa_data/paper3/manuscript_v1/pdf/main.pdf, supplementary.pdf and collection_checklist.pdf. Fresh-source validation PDFs are in fresh_clone_pdf/. No full manuscript PDF, raw RF payload or checkpoint is committed; small vector figure assets and LaTeX are committed for reproducible build.

Authorship/affiliation placeholders are intentional for internal review. No venue page-limit or submission formatting acceptance is asserted.
