# Pre-execution implementation audit
No new target predictions or metrics existed when this audit was recorded.

- Preregistration commit: f30b658ff40f4d8ec3770be4c7c2b4692e5814da.
- Clean prior root: PR89 merge verified; 2080 primary run/checkpoint/prediction records and119 listed analysis files passed inherited hashes.
- Source-only smoke: receiver_loso_00, seed829, three source-validation receivers; no target predictions. Selected full-network oracle recipe1e-4/20 for this smoke only. Full suite repeats the same frozen source-only grid per checkpoint; no shared target optimization.
- Tests:184 new tests;1650 full Paper3+Paper2 tests passed, plus7 subtests. Compileall and diff check passed.
- SAR fidelity:10 synthetic noncollapse one-update comparisons against official sar.py/sam.py had maximum parameter error exactly0. GroupNorm already exists in P0. Parameter-name selector is applied directly; no invented ResNet layer-name mapping.
- Explicit upstream corner cases: reliable-empty means are undefined in upstream code, so skip and restore perturbation rather than emit NaNs. On model recovery, this implementation clears SGD momentum to implement the paper's intended source optimizer reset. The upstream SAM wrapper does not reliably restore its base optimizer's momentum state. This is a disclosed recovery implementation correction, not an empirically selected method variant. EMA retention follows the official wrapper. Report all skip/recovery counts.
- Primary grid480; common256-query budget grid1920; total2400 unique records. Primary128 query IDs and common256 query IDs are not conflated.
- Unlabeled adapters cannot accept annotations. Only supervised_full receives support labels. The data bundle retains split-local annotations in memory for source selection and oracle use; no claim of physically absent target-label bytes.
- Five source-validation-only temperature fits per protocol/seed. No temperature is selected on target correctness.
- New blind archives allow only sample_ids/probabilities. Unblinding checks expected grid, all hashes, query identity/order, support disjointness, oracle boundary and clean committed analysis.
- Receiver inference averages five seeds first;10000 receiver bootstraps,100000 sign flips, exploratory only; no Holm family introduced.
- A full-network labeled128 comparator is stronger in parameter scope than the frozen head comparator, but is not a true achievable-performance ceiling.
- Scientific implementation and entry-point hashes are frozen before target execution. Later writing/figure/collection work cannot change these files without stopping and auditing the blind suite.
