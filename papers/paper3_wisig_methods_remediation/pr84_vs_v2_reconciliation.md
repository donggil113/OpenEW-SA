# PR #84 and V2 reconciliation

Status: **COMPLETE**

## Fixed prior evidence

PR #84 remains immutable preliminary evidence. Its five-fold, ten-class, query-coupled test-time context analysis reported P0 0.770749 and P2 0.792544 macro-F1, a matched mean P2-minus-P0 difference of +0.021795. V2 was designed after adversarial review and is not an independent-dataset replication.

V2 uses a different, stricter estimand: 32 leave-one-receiver-out units, six support-feasible transmitter classes, five seeds averaged within receiver, and a disjoint 128-packet support bank that cannot contain query samples. V1 and V2 magnitudes therefore must not be pooled or treated as a controlled single-factor comparison.

## VERIFIED RESULT

In V2, receiver-level mean macro-F1 was 0.805679 for P0 and 0.806726 for P2. The mean P2-minus-P0 difference was +0.001047, with a 10,000-replicate receiver-bootstrap interval of [-0.006660, 0.008857], a two-sided 100,000-draw receiver sign-flip p-value of 0.793472, and Holm-adjusted p-value 0.793472. P2 was positive on 15 of 32 receivers.

The context mechanism was not wholly nonspecific: P2 exceeded P2-SHUFFLED by +0.018364 and P2-MISMATCHED-RX by +0.019637. The shuffled comparison's bootstrap interval was [0.013924, 0.023171], with sign-flip p=0.000010 and Holm-adjusted p=0.000040. However, the source-validation-selected same-information TTA baseline T3A reached 0.833692, exceeding P2 by 0.026966; P2-minus-T3A had interval [-0.038002, -0.016769], sign-flip p=0.000010, and Holm-adjusted p=0.000040.

The same-class-excluded oracle retained full query coverage and was +0.020237 above P0, while transmitter-pure and same-class-only contexts were harmful. Thus, the V2 attenuation is not adequately explained by dependence on same-class support alone.

## INTERPRETATION

The evidence-consistent reconciliation is outcome **D: P2 does not exceed standard same-information TTA**. The apparent P2-versus-P0 advantage from PR #84 shrinks to a near-zero, receiver-heterogeneous difference under V2's disjoint support/query and receiver-level design. V2 still shows that same-receiver context is more useful to the fixed P2 architecture than shuffled or mismatched receiver context, but that mechanism specificity does not translate into superiority over P0 or T3A.

V2 cannot isolate which combination of query coupling, class-space change, fold aggregation, or support construction caused the cross-version attenuation. It therefore does not claim that PR #84 was caused solely by test-batch construction.

## UNRESOLVED

- Both studies use the same WiSig dataset; neither is an external replication.
- A verified acquisition episode is absent from both versions.
- Any future method change must be frozen using source-only evidence and tested on new data, not retuned on V2 receivers.
