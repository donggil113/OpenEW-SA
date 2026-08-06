# Discussion: v3 (draft)

The results support a dataset-dependent interpretation of uncertainty–distance fusion. The prespecified fusion improved some fixed-orientation comparisons but did not generalize uniformly: DeepSense remained directionally inverted, and performance patterns differed across datasets and metrics. These observations warrant caution against universal claims.

The exploratory Mahalanobis addition should be interpreted as an ablation. Any paired interval excluding zero supports a difference for that dataset, metric, and fixed comparison only; it does not establish broad superiority or a causal mechanism. The post-hoc DeepSense inversion diagnostic suggests systematic score-direction mismatch, but test-OOD labels cannot be used to redefine the primary orientation.

All numerical estimates in this draft are traceable to `paper2_v3_bootstrap_confidence_intervals.csv` or `paper2_v3_paired_differences.csv`.
