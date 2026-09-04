# V2 analysis output and evidence-grain contract

Status: **FROZEN BEFORE TARGET-METRIC UNBLINDING**

All generated files remain external under `/mnt/d/openew_sa_data/paper3/wisig_v2/`. This document defines the unit and label-access boundary for each output used in scientific reporting.

| Output | Row/evidence grain | Target labels | Permitted use |
|---|---|---:|---|
| `predictions_blind.npz` | one query sample per model/receiver/seed archive | No | Immutable probabilities and opaque IDs only; never committed |
| `suite_status.json` and `run.json` | one condition record | No target metric | Checkpoint/resume, source validation, provenance, compute |
| `pre_unblinding_freeze.json` | one immutable suite event | No | Exhaustive hash, query-ID, diagnostic, Git, and protocol preflight |
| `primary_receiver_seed_results.csv` | one held-out receiver × model × seed | Yes, after one-time unblinding | Descriptive metrics and seed variability |
| `primary_receiver_averaged_results.csv` | one held-out receiver × model, after averaging five seeds | Yes | Primary equal-receiver estimand |
| `primary_receiver_level_summary.csv` | distribution across 32 receiver means per model | Yes | Headline model summaries; never packet weighted |
| `paired_receiver_seed_differences.csv` | one receiver × seed × comparison | Yes | Full paired audit trail |
| `paired_receiver_averaged_differences.csv` | one receiver × comparison, after seed averaging | Yes | Bootstrap/sign-flip input and positive-receiver counts |
| `receiver_level_inference.json` | one prespecified comparison over 32 receivers | Yes | 10,000-replicate bootstrap, 100,000 sign flips, Holm correction |
| `source_validation_method_selection.json` | source-validation receiver means only | No target metrics | Select strongest predeclared TTA and source-DG comparator |
| `context_receiver_seed_diagnostics.csv` | one receiver × model × seed | No labels | Support/query overlap, coverage, attention entropy, effective peers, latency |
| `support_composition_audit.csv` | one receiver × seed | Yes, audit only | Post-hoc natural-support composition and correlation diagnostics |
| `composition_oracle_results.csv` | one receiver × seed × oracle condition | Yes, construction and evaluation | Nondeployable mechanism stress only; excluded from primary table |
| `support_budget_results.csv` | one receiver × seed × frozen budget | Yes, after unblinding | Secondary curve; 128 remains primary regardless of result |
| `context_k_results.csv` | one receiver × seed × frozen k | Yes, after unblinding | Secondary curve; k=32 remains primary regardless of result |
| `day_receiver_seed_results.csv` | one coarse day × model × seed plus serialized receiver scores | Yes | Secondary coarse-day analysis; no temporal claim |
| `grouped_secondary_receiver_seed_results.csv` | repeat × grouped fold × receiver × model × seed | Yes | Secondary robustness; LOSO remains primary |
| `equalized_receiver_results.csv` | one receiver × model at seed 829 | Yes | Separate official-equalization diagnostic; never pooled with raw |
| `compute_budget_per_run.csv` | one primary condition record | No target labels | Parameters, wall time, memory, operation estimates, support cost |
| `standardized_inference_benchmark.csv` | one held-out receiver × method at frozen seed 829 | No | Three-repeat test-time latency with checkpoint load excluded and support/adaptation included; blind probabilities must reproduce |
| `analysis_quality_report.json` | one analysis package | No new label access | Fail-closed grain, range, count, condition, and disclosure checks |
| `final_integrity_report.json` | one repository/data state | No | Paper 1/2, PR #80--#84, raw, conversion, and prior-analysis immutability |
| `report_evidence.json` | compact source-backed ledger | Summaries only | Sole numerical source for final narrative reports |

## Inferential boundary

Five seeds quantify algorithmic variability; they are not independent deployment domains. Each paired seed difference is first averaged within a receiver. The 32 receiver means are the primary inferential observations. Packets are never resampled as independent units for an unseen-receiver claim.

## Interpretation boundary

R0 is pure-inductive source training. R1 consumes a bounded unlabeled receiver support bank. R2 adapts prototypes from that same bank. Natural composition, oracle composition, day, grouped receiver, hardware family, and equalization analyses are secondary or diagnostic as labeled; none can redefine the primary estimator or GO rule.

For the support-budget sensitivity only, all five budgets use one common query universe: the packets remaining after the deterministically ranked 256-packet support bank is removed. Smaller banks are nested prefixes of that label-free ranking. This prevents changing query composition across budget values. Consequently, the 128-budget sensitivity point is not substituted for the primary P2 estimate, whose query set is defined by the primary 128-packet support/query split. The `k` sensitivity keeps the primary 128-packet support bank and its query set fixed.
