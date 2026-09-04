# V2 mechanism decision-rule operationalization

Status: **FROZEN BEFORE TARGET-METRIC UNBLINDING**

This addendum turns the qualitative GO language in `methods_remediation_preregistration_v2.md` into deterministic checks. It does not alter any split, model, support pool, target metric, or comparison.

`GO` requires all of the following on the equal-weight receiver analysis after first averaging the five seeds within each receiver:

1. mean P2 minus P0 is strictly positive;
2. mean P2 minus P0-WIDE is strictly positive;
3. mean P2 minus P2-SHUFFLED is strictly positive;
4. mean P2 minus P2-MISMATCHED-RX is strictly positive;
5. mean P2 minus the strongest source-validation-selected, same-information TTA baseline is nonnegative;
6. the diagnostic same-class-excluded P2 result minus the matched P0 result is strictly positive, and every frozen query is evaluable in that diagnostic;
7. P2 minus P0 is positive for at least 17 of 32 receivers after seed averaging;
8. the hardware-family mean P2 minus P0 is positive in at least two of the three verified hardware families;
9. integrity and disjoint-support/query gates pass.

`CONDITIONAL GO` requires the integrity and disjointness gates and a strictly positive mean P2-minus-P0 result, but permits one or more mechanism-specific criteria to fail. `NO-GO` applies otherwise. Receiver bootstrap intervals, sign-flip tests, and Holm-adjusted values are reported as inferential evidence but are not retrofitted as extra pass/fail thresholds.

The transmitter-pure, same-class-excluded, and same-class-only contexts remain label-dependent oracle diagnostics. They cannot become deployable methods regardless of their results.
