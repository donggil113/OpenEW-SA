# PR #84 frozen evidence snapshot

PR #84, **Paper 3 WiSig static receiver-context domain generalization**, was merged as `53bcf41471c11cdd7a96f949fcfcb24b117deccd`. Its artifacts and results are prior, preliminary evidence. V2 is a post-review methodological remediation and robustness replication on the same dataset.

## Frozen primary receiver-holdout macro-F1

| Method | Macro-F1 |
|---|---:|
| P0 | 0.770749 |
| P0-WIDE | 0.773934 |
| P1 | 0.777142 |
| P2 | 0.792544 |
| P2-SHUFFLED | 0.781335 |
| P2-NULL | 0.787461 |
| DG-CORAL | 0.770310 |
| DG-GROUPDRO | 0.695924 |

Frozen matched means are P2 minus P0 `+0.021795`, P2 minus P0-WIDE `+0.018610`, P2 minus P2-SHUFFLED `+0.011210`, and P2 minus P2-NULL `+0.005083`.

## Frozen limitations

- The retention curve is non-monotonic.
- The descriptive P2-minus-P2-NULL interval includes zero.
- Day-holdout improvement is modest.
- The combined receiver-plus-day stress test shows essentially no P2 advantage.
- One of five receiver folds does not beat P2-SHUFFLED.
- V1 hash-chunked the entire held-out receiver partition, so query samples could provide context to other queries.
- V1's five receiver folds are too coarse to be the final inferential unit for an unseen-receiver claim.

These observations are not reinterpreted. V2 may corroborate the result, reduce it, attribute it to test-batch construction, or find that standard test-time adaptation is competitive or superior.
