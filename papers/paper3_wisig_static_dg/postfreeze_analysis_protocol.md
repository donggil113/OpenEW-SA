# WiSig post-freeze analysis protocol

Status: frozen before aggregate held-out results were opened.

## Run accounting

The code-defined study grid contains 580 declared condition entries and 530 unique executable configurations; 50 exact duplicates are reused by configuration hash. Final analysis must compare the persisted `config_hash` set with this complete grid, require exactly one terminal record per hash, reject malformed or unexpected records, and report every technical failure. Missing conditions may not be silently omitted.

## Primary selection

Primary receiver- and day-holdout summaries use context size 32 and relation retention 100%. `P2-NULL` is the prespecified zero-context architecture control. Context-size and retention conditions are reported separately and cannot replace the primary condition.

All five seeds and all folds are retained. Model comparisons are paired by exact protocol and seed. Report mean, sample standard deviation, median, minimum, maximum, seed-level values, and fold-level variability. No best-seed or best-fold result may replace the complete summary.

## Descriptive uncertainty

The preregistered 2,000-replicate analysis resamples receiver folds as top-level clusters and preserves all paired seed/model differences within each selected fold. It does not treat RF packets as independent bootstrap units. Intervals are descriptive; no statistical-significance claim is made.

## Mechanism decision

The GO/CONDITIONAL GO/NO-GO criteria are those in `experiment_preregistration_v1.md`. The executable decision audit requires reproducible source-validation behavior, held-out non-degradation within 0.01 absolute, a reproducible advantage over shuffled context, an advantage over the capacity-matched independent model, benefit beyond one fold, and a passed leakage gate. The rules are not changed after target evaluation.

## Diagnostic-only post-audit

After predictions are frozen, errors are grouped by receiver, day, packet-quality flag, and transmitter support. This audit may join annotations only after prediction serialization. It is not feature selection, cannot change class eligibility, cannot change folds, and cannot trigger model redesign. A constant packet-quality field is reported as non-informative rather than assigned an artificial correlation.

## Figures

Performance figures use an untruncated 0--1 metric axis. Context attention is summarized only as an association diagnostic; it is not interpreted causally. Publication CSV, PNG, and PDF outputs remain external to Git under the WiSig analysis root.
