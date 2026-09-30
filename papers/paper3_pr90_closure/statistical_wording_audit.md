# PR #90 statistical-wording audit (read-only frozen evidence)

This audit independently recomputed the receiver sign-flip exceedance counts
from the frozen `receiver_averaged_metrics.csv` and inspected the actual T3A
scoring code. No target prediction, split, model, analysis, or manifest was
changed. The reviewer-completeness comparisons remain **post-hoc/exploratory**.

## Receiver sign-flip calculation

The implemented inferential unit is a physical receiver, not a packet. For
each of 32 receivers, macro-F1 is first averaged over five seeds within each
method. The paired method-minus-reference value is then calculated. With
receiver differences \(d_1,\ldots,d_{32}\), the observed statistic is
\(|\overline d|\). Each of 100,000 Monte Carlo draws independently assigns
\(s_i\in\{-1,+1\}\) and counts an exceedance when
\(|32^{-1}\sum_i s_i d_i|\ge |\overline d|-10^{-15}\). The implementation
reports \(\widehat p=(E+1)/(100000+1)\), where \(E\) is the exceedance count.
Draws are with replacement; this is not exhaustive enumeration of \(2^{32}\)
sign assignments. The original T3A comparison used RNG seed `20260903`;
the PR #90 addendum uses `20260906` for each comparison separately.

| Frozen comparison | Mean receiver delta | Exceedances E / 100,000 | Reported/recomputed p | Status |
|---|---:|---:|---:|---|
| Historical T3A minus P0 | +0.028013737908 | 0 | 0.00000999990001 | Frozen prior, sole historical Holm family member |
| EMB-STD minus P0 | +0.022811516471 | 0 | 0.00000999990001 | Post-hoc, unadjusted |
| EMB-STD minus T3A | -0.005202221437 | 5,936 | 0.059369406306 | Post-hoc, unadjusted |
| SAR-GN minus P0 | +0.000005631621 | 64,019 | 0.640193598064 | Post-hoc, unadjusted |
| SAR-GN minus T3A | -0.028008106286 | 0 | 0.00000999990001 | Post-hoc, unadjusted |
| SUP-FT-FULL-128 minus P0 | +0.116132363718 | 0 | 0.00000999990001 | Post-hoc labeled comparator, unadjusted |
| SUP-FT-FULL-128 minus T3A | +0.088118625810 | 0 | 0.00000999990001 | Post-hoc labeled comparator, unadjusted |

The counts above were independently regenerated from the frozen receiver
averages, using the implemented 5,000-draw batches and RNG seeds; all seven
recomputed p-values exactly match their frozen JSON records to floating-point
precision. The minimum reportable **Monte Carlo estimate** at this budget is
`1/100001` when zero sampled signs exceed the statistic. It is **not** an
exact permutation p-value, a proof that the true p-value is zero, or an upper
bound on the exact p-value. Wording should say, for example, “two-sided
receiver-level Monte Carlo sign-flip estimate \(\widehat p=1/100001\)
(100,000 random sign assignments; zero exceedances).” Avoid `p < 1e-5` or
“exact p <= 1e-5.” The addendum has no preregistered Holm correction family;
its sign-flip p-values must remain explicitly exploratory and unadjusted.
A non-significant SAR-GN-minus-P0 test is not an equivalence test.

## T3A score-scale caveat

`T3AAdapter.adapted_weights` L2-normalizes the **selected support vectors**
and then the resulting **class-prototype columns**. Its `predict` computes
`query_embeddings @ weights` without L2-normalizing the query embeddings.
Consequently a class score obeys the sample-specific Cauchy--Schwarz bound
\(|\ell_c|\le\lVert z_{query}\rVert_2\), not a fixed `[-1, 1]` bound from
unit prototypes alone. The shared RF backbone has no final unit-norm layer.
Probability scale therefore can depend on query-embedding norm as well as
prototype geometry. Do not explain the observed T3A confidence pattern by
claiming its logits are universally bounded by unit-norm prototypes. Any
explanation of average underconfidence is descriptive unless embedding-norm
and receiver/bin-level evidence is explicitly shown; source-only temperature
scaling is a probability-quality diagnostic, not a classification result.

## Headroom and supervised comparators

The same frozen primary receiver-equal macro-F1 table gives P0
`0.805678504903`, T3A `0.833692242811`, labeled head-only
`0.838080642479`, and labeled full-network `0.921810868621`.
`(mean(T3A)-mean(P0))/(mean(head)-mean(P0)) = 0.864564501105`.
That is a **ratio of receiver-equal means** for this particular 32-receiver
query universe, not a mean of receiver-specific ratios and not “86% of the
available adaptation headroom.” Replacing head-only with full-network labeled
adaptation changes that descriptive ratio to `0.241222489674`. The two
labeled procedures reveal the *same 128 support labels* but update different
parameter subsets, and neither is a mathematical upper bound on accuracy or
macro-F1. The full-network comparator provides evidence of a larger observed
label-dependent gain under one source-selected adaptation recipe; it does not
establish a universal ceiling. Prefer removing the 86% phrase entirely.

## Frozen source lineage

- `src/openew/paper3/wisig_v2/statistics.py` SHA256 `75daf4128076b51f4f7d487cf3c98b8371c87765814652467aaa1cae49b407fd` (sign-flip rule).
- `src/openew/paper3/reviewer_remediation/analysis.py` SHA256 `cc92e03794f1689900b3a60b1d905a9574af5730d0df92cdc87ddb8851166c83` (five seeds within receiver, post-hoc family).
- `src/openew/paper3/wisig_v2/models.py` SHA256 `37fa646b20c6468c473e020e9ec8884e0bc0d28ceb38458a955992d3140d9eeb` (T3A adapter).
- `papers/paper3_reviewer_remediation/evidence/prior_receiver_inference.json` SHA256 `9192d0bf6bbac352bf8eccf6b8e61776df897615f21915da8b1136072ce0e8ce`.
- External frozen `reviewer_remediation/analysis/receiver_inference.json` SHA256 `63933d1947e0f132259023df495df65a003d52df74bb0b5b986a52a3d3308792`.
- External frozen `reviewer_remediation/analysis/receiver_averaged_metrics.csv` SHA256 `c8b4cf3c5c5be7fe57098eb951d0d5633ac5250bbc73fc7f0032dfa38a2c7bc4`.
