# IEEE internal-review package

Build with IEEEtran, latexmk, pdfLaTeX, booktabs, tabularx, microtype, and standard fonts:

    bash build.sh /absolute/external/output

Regenerate assets from committed evidence (repository root):

    python scripts/paper3/collection_runtime/render_manuscript_assets.py --manuscript papers/paper3_receiver_adaptation_manuscript --output /absolute/external/png-directory

No RF payload or training required. Main manuscript: IEEEtran journal style. Landscape supplement: audit lookup. Authors, affiliations, venue, institutional release approval require human review. PDF build is not submission readiness.
