# Shared-source venue packages

Scientific content is shared by main_tmlcn.tex and main_access.tex; the
supplement has a separate wrapper. Canonical wrappers retain the OpenEW-SA
Internal Review identity. Submission builds remove that identity only in a
fresh external staging copy. Scientific body, tables, numerical macros,
author/affiliation/ORCID/corresponding-author placeholders, and frozen evidence
are unchanged by the audience switch. Neither build is an accepted article.

From the repository root with Python, TeX Live/IEEEtran, latexmk, and the
verified official Access template, choose fresh, nonexistent output directories:

~~~sh
python scripts/paper3/reviewer_remediation/build_pdfs.py \
  --repository . --audience internal \
  --output /your/new/build-root/internal \
  --access-template /path/to/ACCESS_latex_template_20260513.zip

PYTHONPATH=src python scripts/paper3/reviewer_remediation/render_release_assets.py \
  --repository . \
  --presentation-output /your/new/build-root/presentation_figures \
  --png-output /your/new/build-root/presentation_png

python scripts/paper3/reviewer_remediation/build_pdfs.py \
  --repository . --audience submission \
  --submission-figures /your/new/build-root/presentation_figures/figures \
  --output /your/new/build-root/submission \
  --access-template /path/to/ACCESS_latex_template_20260513.zip
~~~

The internal build retains the internal-review masthead. The submission build
uses the same source, but its staged TMLCN, Access, and supplement wrappers
remove the internal-review masthead, Access draft history, draft footer, and
draft footnote. The Access submission layout also suppresses the official
template's example volume/year footer instead of presenting it as publication
metadata. It stages presentation-only figure variants whose plot data and
receiver order are unchanged; the main forest-style paired-delta figure is
copied unchanged. Frozen analysis figures are never overwritten. Both builds
produce separate main_tmlcn.pdf, main_access.pdf, supplementary.pdf, build
logs, and a build manifest. Submission identity preparation fails closed if
expected wrapper markers or presentation figures are missing.

The Access template is obtained from the official IEEE Access
submission-guidelines page (LaTeX link, verified 2026-09-06). The builder
requires SHA256
60c7efc9db8ac9e8bdb31c550ad4e03cb6f258a878ececc0bc690b6203e45a67,
checks archive paths, and extracts only style/font/logo dependencies into the
external build stage. Third-party fonts/classes are not redistributed by this
repository. A changed official template requires a reviewed checksum update,
not silent acceptance.

TMLCN-oriented output uses IEEEtran journal layout. The Access-oriented output
uses the official May-2026 Access template and retains a human-biography
blocker. Authors, affiliations, funding, ORCIDs, corresponding author,
AI-disclosure confirmation, derivative-release approval, and venue choice
remain unresolved. Compiling PDFs does not resolve those human-only gates.
