# Paper 2 IEEE PDF technical audit

Audit date: 2026-08-11

## Artifact and commands

The audited artifact is `build/main.pdf`, produced from a clean source build:

```text
latexmk -C main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
pdfinfo build/main.pdf
pdffonts build/main.pdf
```

No TeX package was installed during this pass.

## PDF results

| Check | Result |
|---|---:|
| PDF exists | PASS |
| Page count | 11 |
| File size | 546,023 bytes (approximately 533.2 KiB) |
| Paper size | 612 x 792 points, US letter (8.5 x 11 inches) |
| PDF version | 1.5 |
| Encrypted | No |
| Expected figures included | 5 of 5 |
| Font objects | 27 |
| All fonts embedded | PASS; 27 of 27 |
| All fonts subset | PASS; 27 of 27 |
| Type 3 font count | 0 |

The font set consists of embedded/subset Type 1 manuscript fonts and embedded/
subset CID TrueType fonts carried by the source figures. No Type 3 font is
present.

## Compiler-log results

Counts are from the final successful pass in `build/main.log`.

| Log item | Count |
|---|---:|
| Compilation errors | 0 |
| Overfull boxes | 0 |
| Underfull boxes | 13 |
| Underfull `\hbox` | 9 |
| Underfull `\vbox` | 4 |
| `LaTeX Warning:` messages | 2 |
| LaTeX font warnings | 0 |
| Undefined cross-references | 0 |
| Undefined citations | 0 |
| Multiply-defined labels | 0 |
| Missing-file or missing-figure messages | 0 |
| Unresolved citation placeholders | 17 (R1--R17) |

Both LaTeX warnings are the same float-placement notice: text page 7 contains
only floats. The remaining underfull boxes are non-destructive whitespace
warnings from IEEE column justification, long monospaced reproducibility paths,
the visible unresolved-reference list, and float-heavy pages. There are no
overfull boxes, clipped elements, or unresolved internal references.

## Figure inclusion and visual confirmation

The recorder file confirms that all expected PDFs were read:

1. `figures/figure_ood_auroc_with_ci.pdf`
2. `figures/figure_fpr95_with_ci.pdf`
3. `figures/figure_primary_fusion_comparison.pdf`
4. `figures/figure_score_distributions_by_dataset.pdf`
5. `figures/figure_deepsense_inversion_diagnostic.pdf`

All 11 output pages were rasterized at 120 dpi and visually inspected. Figure
legends and captions are readable, all tables are complete and unclipped,
Figure 3 clearly states that it reports AUROC only, and Figure 5 visibly states
that score negation is a post-hoc diagnostic only.
