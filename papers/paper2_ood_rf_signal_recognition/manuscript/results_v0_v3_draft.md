# Results: v0–v3 (draft)

The prespecified primary fusion produced the following fixed-orientation results:

- ElectroSense: AUROC 0.857037 (95% CI 0.851138–0.862585); AUPR-OOD 0.934429 (95% CI 0.930849–0.937570); FPR95 0.434589 (95% CI 0.420886–0.447774).
- DeepSense: AUROC 0.352958 (95% CI 0.340919–0.364553); AUPR-OOD 0.737936 (95% CI 0.733647–0.742146); FPR95 0.992188 (95% CI 0.989062–0.995313).
- JamShield: AUROC 0.657625 (95% CI 0.652294–0.663324); AUPR-OOD 0.710403 (95% CI 0.704694–0.716541); FPR95 0.927205 (95% CI 0.922869–0.931402).

For JamShield, the primary fusion improved AUROC against each prespecified comparator, but AUPR-OOD and FPR95 were not uniformly better against every comparator. AUPR-OOD was lower than temperature-scaled entropy, and FPR95 was higher than nearest-centroid cosine.

DeepSense was a negative result under the fixed score orientation: its primary-fusion AUROC was below 0.5. Post-hoc score negation is presented only as a diagnostic sensitivity analysis and does not replace the primary result. The four-component method is an exploratory ablation and is not described as prespecified. Paired comparisons and whether their 95% intervals exclude zero are reported in `paper2_v3_paired_differences.csv`; no comparator was selected according to test performance.

All numerical estimates in this draft are traceable to `paper2_v3_bootstrap_confidence_intervals.csv` or `paper2_v3_paired_differences.csv`.
