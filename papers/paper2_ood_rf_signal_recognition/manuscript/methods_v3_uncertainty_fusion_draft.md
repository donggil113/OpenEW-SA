# Methods: v3 uncertainty–distance fusion (draft)

The prespecified primary score was the equal-weight fusion `ts_entropy_cosine_euclidean`, comprising temperature-scaled predictive entropy, nearest-centroid cosine distance, and nearest-centroid Euclidean distance. Component scores retained the fixed convention that larger values indicate greater OOD-likeness. Each component was robustly normalized using ID validation data only, and no test-OOD result was used to select orientation, weights, thresholds, the primary method, or comparators. The equal-weight four-component variant adding Mahalanobis distance was treated as an exploratory ablation.

Uncertainty was estimated using 1,000 nonparametric bootstrap replicates with seed 20260721. ID and OOD observations were resampled separately at their original counts. A common pair of ID/OOD index samples was reused across methods within each dataset, enabling paired differences. Percentile 95% confidence intervals were calculated for AUROC, AUPR-OOD, FPR95, and detection accuracy. Detection accuracy is descriptive because its threshold was optimized on the evaluation sample.

All numerical estimates in this draft are traceable to `paper2_v3_bootstrap_confidence_intervals.csv` or `paper2_v3_paired_differences.csv`.
