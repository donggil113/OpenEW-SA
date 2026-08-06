# Limitations: v3 (draft)

The evaluation covers one frozen split for each of three datasets and therefore does not establish universal generalization. Bootstrap intervals quantify sampling variability conditional on these samples and do not capture dataset-shift uncertainty. Detection accuracy uses an evaluation-selected threshold and is descriptive rather than deployment-valid. Equal weighting and score orientation were fixed; no test-OOD adaptation was permitted. The DeepSense result is negative under that orientation. The negated-score analysis is post-hoc and diagnostic only. Multiple dataset, metric, and comparator intervals are reported without a family-wise multiplicity adjustment, so interval exclusion of zero should be interpreted narrowly.

All numerical estimates in this draft are traceable to `paper2_v3_bootstrap_confidence_intervals.csv` or `paper2_v3_paired_differences.csv`.
