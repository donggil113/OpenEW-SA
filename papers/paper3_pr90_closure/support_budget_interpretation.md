# Support-budget interpretation and matched-query audit

Status: POST-HOC LINEAGE/INTERPRETATION AUDIT; no new model prediction, training, or method selection.

The frozen reference support-128 table reserves 128 test-receiver packets. The frozen V2 addendum budget curve reserves 256 packets for **every** budget, so its query universe is smaller. Subtracting the reference P0 0.805679 from budget-curve T3A is invalid. `scripts/paper3/pr90_closure/audit_matched_budget.py` reads the 160 frozen P0 blind prediction archives, checks each archive SHA256 against `run.json`, verifies exact primary query IDs and reproduces every frozen P0 receiver-seed macro-F1, then re-scores those **same probabilities** only on the common-256 query IDs. It joins the frozen T3A budget records by protocol and seed and checks their query counts. No P0 forward pass was run. This audit does not alter any original result or analysis manifest.

| Support packets | Matched-query P0 macro-F1 | Frozen T3A macro-F1 | T3A minus matched P0 |
|---:|---:|---:|---:|
| 16 | 0.805632 | 0.719644 | -0.085988 |
| 32 | 0.805632 | 0.795558 | -0.010074 |
| 64 | 0.805632 | 0.822783 | +0.017151 |
| 128 | 0.805632 | 0.833617 | +0.027984 |
| 256 | 0.805632 | 0.838273 | +0.032641 |

These are descriptive receiver-equal means of 160 matched receiver-seed pairs (32 receivers, five seeds). All five support budgets use the same query universe within each pair; 717,535 query evaluations occur across the 160 pairs per budget (not 717,535 independent packets). This does not establish a universal sufficient support threshold. In this dataset and frozen support construction, the two smallest banks perform below the matched P0 average; T3A improves on average from 64 onward. There can be receiver heterogeneity, and no best budget is selected.

Coverage of transmitter classes in a support bank is a **label-aware post-hoc safety/interpretation diagnostic**, not an input to support selection or an operational guarantee. A receiver cannot know whether the query transmitter is represented in an unlabeled bank. The support pools were selected by stable sample-ID hashing without labels. The raw acquisitions have transmitter-specific containers and are not physically separate calibration episodes. Neither “64 packets are always sufficient” nor “10 packets per class guarantees performance” follows.

The source T3A budget CSV is `/mnt/d/openew_sa_data/paper3/v2_addendum/analysis_support_budget.csv` (SHA256 `e7ede8215e3f5c453ddc4cddac3444e4ddab0639ec6f12168ca201730238bd51`). The frozen primary receiver-seed CSV is `/mnt/d/openew_sa_data/paper3/wisig_v2/analysis/confirmatory_v2/primary_receiver_seed_results.csv` (SHA256 `59e7f4ccabd9dbfc97a7a696a2cd711c1b0e9288ca1b3ca8e62a2c5571238890`). Generated audit evidence is outside Git under `/mnt/d/openew_sa_data/paper3/pr90_closure/20260928T110826Z/budget/`: `matched_p0_budget_receiver_seed.csv` (SHA256 `143529395d18e02bdf453dfe14d7c01ddf6340c2ba2df242e6c316e6ab22d406`), `matched_p0_budget_summary.csv` (SHA256 `e64f4e54845bbb291fe3445670abfd2a52351dd70b134e3b3c792b5a5f07a4f6`), and `matched_p0_budget_audit.json`. Original 160 P0 archives remain in place.

The matched-query re-scoring is post-hoc and descriptive. It is not a new preregistered inferential comparison, and its same-query difference does not change the frozen V2 or PR90 primary conclusions.
