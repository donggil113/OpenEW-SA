# Figure and page visual audit

Final eight PDF/PNG assets and all nine main / six supplementary pages were rendered and visually inspected. Supplementary dense table pages were checked at higher resolution after a preview artifact suggested clipping; the final render shows intact headers and separated columns.

| Figure | Checks and outcome |
|---|---|
| 1 Design | Four readable boxes, arrows, bounded support, no acquired-session implication: PASS |
| 2 Benchmark | All ten displayed methods; x=0–1; receiver SD explicitly not CI; full-width placement: PASS |
| 3 Receiver deltas | All 32 in fixed ID order, one negative visible, symmetric zero-centered axis: PASS |
| 4 Support budget | All five budgets; primary remains 128; log axis labeled; minor-label overlaps removed: PASS |
| 5 Accuracy/ECE | Three methods × all receivers; hollow distinct markers; ECE/NLL distinguished: PASS |
| 6 Compute | Separate timing scopes; titles wrapped; bars start at zero; no implied isolated latency: PASS |
| 7 Hardware | All three families with receiver counts; hatching distinguishes P2; descriptive caveat: PASS |
| 8 Evidence progression | Earlier negative/neutral stages retained; not independent replications: PASS |

Corrections during QA: shortened the compute table's method/scope labels to eliminate a 17.92pt overfull box; wrapped conceptual boxes and compute title; removed log-axis minor tick labels; used full-width benchmark/receiver plots; ensured Figures 3/4 follow requested receiver/budget order. None changed data.

Main Table VI no longer collides with the second column. Tables I–VI and the full 160-row receiver-seed supplementary lookup are legible. Blue/gold/gray contrasts are supplemented by marker shape, line style or hatching where comparison requires it. Absolute macro-F1 axes cover 0–1; difference axes include zero and both directions. One underfull page-output warning remains without clipping. The final reference page has unused space; venue-specific compression is a later editorial decision.
