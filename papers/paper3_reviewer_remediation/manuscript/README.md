# Shared-source venue packages

Scientific content is shared by main_tmlcn.tex and main_access.tex. Supplementary content is separate. This is an internal-review revision, not a submitted or accepted article.

From repository root with Python and TeX Live/IEEEtran/latexmk:
```sh
python scripts/paper3/reviewer_remediation/build_pdfs.py --output /your/new/build-directory
```

To build the Access variant too, pass --access-template /path/to/ACCESS_latex_template_20260513.zip. Obtain it from the official IEEE Access submission-guidelines page (LaTeX link, verified 2026-09-06). The builder requires SHA256 60c7efc9db8ac9e8bdb31c550ad4e03cb6f258a878ececc0bc690b6203e45a67, checks archive paths and extracts only style/font/logo dependencies into the external build stage. Third-party fonts/classes are not redistributed by this repository. A changed official template requires a reviewed checksum update, not silent acceptance.

TMLCN-oriented output uses IEEEtran journal layout. The Access-oriented output uses the official May-2026 Access template, includes a human-biography blocker, and shares the exact scientific body. Authors, affiliations, funding, ORCIDs, corresponding author, disclosure review and venue approval remain unresolved. PDFs compiling successfully does not resolve those gates.
