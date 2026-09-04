# External replication statistics preregistration

Status: **FROZEN BEFORE DATA COLLECTION/CONVERSION AND TARGET RESULTS**

## Estimands and units

The primary outcome is macro-F1 for transmitter classification on the disjoint
query episode of each unseen receiver. Every receiver has equal weight. If two
campaigns qualify, campaign-specific query macro-F1 is first averaged within
receiver and seed.

Seeds quantify algorithmic variability and are not independent deployment
units. For inferential comparisons, the five seed-matched differences are first
averaged within each receiver. Receiver-level differences—not packets—are the
inputs to intervals and tests.

Secondary descriptive outcomes are balanced accuracy, accuracy, ECE,
per-class recall, calibration/query coverage, and computation/latency. They do
not replace the primary endpoint.

## Frozen methods and comparisons

Only three methods are part of the replication:

- P0, independent ERM;
- T3A, same-information test-time adaptation; and
- P2, attentive receiver-context conditioning.

Primary confirmatory family:

1. T3A minus P0;
2. P2 minus P0; and
3. P2 minus T3A.

The first comparison answers whether the same-information adaptation route
establishes a receiver-calibration benefit even when P2 is not the best
mechanism. No comparison may be added to the confirmatory family after target
access.

## Summary statistics

For every method report all receiver-by-seed values, receiver means, equal-
weight mean, receiver standard deviation, median, minimum, maximum, and counts
of receivers with positive/zero/negative paired differences. Report both
campaigns separately and the preregistered within-receiver aggregate when two
campaigns qualify.

## Receiver bootstrap

For each primary paired difference:

- draw 10,000 bootstrap samples of receivers with replacement;
- preserve the within-receiver seed average and paired method structure;
- compute the equal-weight mean paired difference for each replicate;
- use the percentile 2.5th and 97.5th quantiles as the 95% interval; and
- use RNG seed `20260903`.

Packets, windows, and support items are never bootstrap units.

## Receiver sign-flip test

For each primary paired difference, perform a two-sided sign-flip test on the
receiver-level seed-averaged differences. Use 100,000 Monte Carlo sign patterns
with RNG seed `20260903`; the observed statistic is the absolute mean
difference. Include the observed assignment in the finite-sample p-value
calculation. Apply Holm adjustment across the three primary comparisons only.

The analysis reports exact effect estimates and intervals regardless of the
adjusted p-values. Statistical significance is not substituted for practical
benefit.

## Missingness and failures

Bad receivers and bad seeds are not removed. A technically failed run may be
retried only under the identical frozen configuration with the failure and
retry logged. A scientifically invalid receiver, missing calibration bank, or
split/integrity violation invalidates the confirmatory dataset rather than
shrinking the inferential cohort after results.

## Blinding

During training, source-validation results may control the frozen early-
stopping rule and T3A candidate selection. Target query probabilities and IDs
are written without target metrics. One create-once unblinding event is allowed
only after every preregistered run, hash, and integrity check is complete. The
unblinding manifest records the commit, data/split/support hashes, prediction
manifest, method ledger, and UTC time.

## Interpretation boundary

This is an independent-dataset replication only if the data contain no WiSig
signal or derivative. A positive T3A-minus-P0 result with nonpositive
P2-minus-T3A supports unlabeled receiver calibration but not the P2 mechanism.
A positive P2-minus-shuffled result is not part of this three-method replication
and will not be introduced post hoc. No causal claim is made from attention
weights or support composition.
