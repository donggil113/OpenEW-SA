# Prospective domain-generalization split protocol

Split families are declared before future result inspection. `domain_id` and
all split keys are withheld from model relations/features unless a separate
eligibility review explicitly allows the underlying acquisition field.

| Split family | Valid when | Required exclusion boundary | Scientific question |
|---|---|---|---|
| receiver holdout | multiple physical receivers cover comparable tasks/campaigns | receiver, capture, and session do not cross partitions | unseen receiver hardware/channel |
| site holdout | privacy-safe site identity is verified and multiple sites have task support | site and all nested sessions/captures are exclusive | unseen propagation/site |
| campaign holdout | campaign open/close semantics and configuration provenance are known | whole campaign exclusive | unseen collection campaign |
| time-period holdout | valid timestamps, clock/reset semantics, and predeclared cutoff exist | sessions crossing cutoff assigned wholly to one side or quarantined | future-period shift |
| hardware holdout | hardware model/unit identities are verified and not target-confounded | held-out hardware plus nested captures exclusive | unseen acquisition hardware |

## Universal constraints

- The same `capture_id` or `acquisition_session_id` cannot appear in more than
  one partition.
- Derived windows from one raw record/capture stay together.
- Validation comes only from source domains; target labels/performance cannot
  select preprocessing, relation types, context size, or hyperparameters.
- Relation structures are built separately inside train, validation, and test.
- Target-derived split IDs, target labels, and held-out-domain identifiers are
  never model inputs.
- Stratification by label, if needed for source-only validation, is documented
  as split construction and never leaks into relation incidence.

Each release writes sample/capture/session membership hashes and an overlap
audit. If a domain is target-pure by collection design, the split is invalid for
claiming label-independent domain generalization without additional evidence.

