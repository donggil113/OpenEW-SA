# Pretarget class-space correction

No held-out receiver prediction or target metric had been computed when the first source-only smoke run revealed that the split generator had frozen a common six-transmitter task while the runner still instantiated the original ten-output bundle label space. The split manifests already excluded the four ineligible transmitters, but leaving ten output units would have made four untrained classes part of the classifier and metric label union.

The runner was corrected to read each frozen `split_summary.json`, verify its eligible transmitter IDs against the converted bundle, create a contiguous split-local label map, and instantiate a six-output classifier. Two regression tests cover contiguous remapping and unknown-target rejection. The full 13-condition source-only smoke suite was repeated in a new external directory, `/mnt/d/openew_sa_data/paper3/wisig_v2/experiments/source_only_smoke_global6`, and completed 13/13 without failure. The earlier smoke directory remains intact as an audit trace and is not scientific evidence.

This is a pretarget structural correction, not a target-performance adjustment. The relation, support/query, seed, architecture, optimizer, and statistical definitions did not change.
