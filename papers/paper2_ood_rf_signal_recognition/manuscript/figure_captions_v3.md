# Figure captions: v3

1. **OOD AUROC with confidence intervals.** Point estimates and percentile 95% bootstrap confidence intervals under the fixed higher-is-more-OOD orientation; the dashed AUROC = 0.5 line marks chance. The three-component fusion is prespecified; the four-component method is exploratory.
2. **FPR95 with confidence intervals.** False-positive rate at 95% OOD true-positive rate, with percentile 95% bootstrap confidence intervals. Lower values are preferable; axes include zero and the full probability range.
3. **Primary fusion comparison.** This figure reports AUROC only. Paired AUROC differences compare the prespecified primary fusion with each prespecified comparator. Intervals use identical bootstrap resamples across methods; the focused difference scale is centered on zero.
4. **Score distributions.** ID and OOD score-density outlines for the prespecified primary fusion, clipped only for display to the 0.5th–99.5th score percentiles within each dataset. Score and density axes are dataset-specific and should not be compared as common scales across panels.
5. **DeepSense distance and fusion score inversion.** **POST-HOC DIAGNOSTIC ONLY.** Fixed-orientation AUROC is compared with AUROC after score negation. Negated values were not used to change or replace the primary analysis.
