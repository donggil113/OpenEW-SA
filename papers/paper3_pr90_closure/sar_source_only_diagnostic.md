# SAR source-validation-only operational sensitivity

Evidence class: **post-hoc source-only diagnostic**, not independent confirmation. No held-out receiver target query was predicted or scored. The original official-default PR90 SAR row, its 160 checkpoints/predictions and analysis manifest remain frozen.

## Design frozen before execution

The machine-readable config is configs/paper3/pr90_closure/sar_source_only_v1.json. The create-once *executed* freeze is external at sar/source_only_checkpointed/source_only_freeze.json, SHA256 **a50e7f1076ce6f887e8a1a97a4d1c81c4e8dadb2ee2d30f43f98a27891c2a3c6**. It records script/module/config hashes, 32 split hashes and 160 source P0 checkpoint hashes. An earlier freeze-only preflight at sar/source_only/source_only_freeze.json was created before atomic checkpointing was added, had **no executed candidates**, and was preserved unmodified; it is not the executed plan.

Within each LOSO fold and seed, only its three distinct frozen source-validation receivers supplied support/query data. The fold's held-out test receiver was excluded by split-role checks. Support128 was selected by the frozen label-free sample-ID hash separately within each validation receiver; its remaining samples served as source-validation query. Adaptation consumed support I/Q only. Source-validation labels entered afterward for macro-F1 and probability-quality diagnostics. The bundle loader contains annotation arrays, but the implementation indexes labels only at those validation-query indices.

The six candidates were frozen as A: reset threshold 0.2, B: 0.2 log(C)/log(1000), each at 1, 5 or 20 passes over the same support bank. C=6 gives B=0.0518767500. The same SGD learning rate 0.00025, SAM radius 0.05, momentum 0.9, margin 0.4 log(C) and batch64 were retained. B is a **normalization hypothesis**, not a correction from official SAR. The source-only selection rule is maximum mean macro-F1 over the fold's three validation receivers; ties follow candidate order A1,A5,A20,B1,B5,B20. No learning-rate search occurred.

The run produced one atomic checkpoint per fold × seed × candidate (960 files) and 2,880 candidate × validation receiver rows. All intended keys are complete. Summary SHA256 **684f3c94adfebdb547bbb9f6fb9fb3ede0d1e6057c1769247eb782dcd38a8518**; full source-only rows SHA256 **c28777803e8610bfe4662e4b79f5b5f069039a439e2ee1050ca5cfd6d658085b**; selected recipe CSV SHA256 **fab8a987791edb3c1c3a96b8847a07c6966b480555011838a736e4f2b9e0a918**.

## Descriptive source-validation results

Every row below averages the same 480 source-validation receiver runs: 32 LOSO mappings × five seeds × three validation receivers. Receivers recur as source validation across folds; these are **not 480 independent domains**. No receiver bootstrap, significance or target inference is claimed from this table.

| Recipe | Passes | Mean macro-F1 | Mean ECE | Mean NLL | Mean Brier | Resets / updates | Final state changed from P0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A1, threshold 0.2 | 1 | 0.822618 | 0.073145 | 0.573746 | 0.247372 | 852 / 960 | 50 / 480 |
| A5, threshold 0.2 | 5 | 0.822600 | 0.073250 | 0.574197 | 0.247417 | 4,369 / 4,800 | 32 / 480 |
| A20, threshold 0.2 | 20 | 0.822231 | 0.073691 | 0.576518 | 0.248007 | 17,893 / 19,200 | 27 / 480 |
| B1, normalized hypothesis | 1 | 0.822644 | 0.073155 | 0.573673 | 0.247302 | 17 / 960 | 473 / 480 |
| B5, normalized hypothesis | 5 | 0.823006 | 0.073367 | 0.573993 | 0.246745 | 69 / 4,800 | 472 / 480 |
| B20, normalized hypothesis | 20 | 0.821855 | 0.076421 | 0.588910 | 0.248409 | 304 / 19,200 | 471 / 480 |

Both reliable-subset filters were nonempty throughout this source diagnostic (zero empty-first and zero empty-second). Completion and finite probability checks passed. Reducing resets did not yield a monotonic macro-F1 or probability-quality gain; B20 had a lower mean macro-F1 and higher NLL than A1. This is an observed source-validation sensitivity, not a target result or proof of a better held-out method.

Source-only choice distribution across the 160 fold-seed keys: A1 24, A5 5, A20 3, B1 20, B5 44, B20 64. The mean *selected on these same validation receivers* was 0.824483; it is in-sample selection performance and must not be reported as independent performance. Recipe choices are tied to the respective fold's source-validation receivers, not to existing results from any held-out receiver. The diagnostic does not establish whether any chosen recipe would improve the frozen target result.

For A1, scripts/paper3/pr90_closure/check_sar_source_parity.py compared all 480 validation-receiver F1, ECE, NLL and Brier values against the frozen PR90 source_sar_gn.npz archives. Maximum absolute difference was **zero** for each metric. Parity JSON SHA256 **f905a2910877af07e26ed4221e9d773d43b16a3e9a9cfd78952492b69150fc25**.

## Computational and scientific limits

Summed adaptation timing across the 480 receiver runs per recipe ranged from about 12.9 seconds (B1) to 187.1 seconds (A20), measured inside resident-model source simulations. This excludes source loading, split assembly, archival writes, and any future target evaluation. More passes intentionally require more updates.

The source-only experiment did not compute test receiver predictions or labels. It is a post-hoc operational probe after known WiSig results, so it cannot become a fresh confirmatory family. Target evaluation of one source-selected recipe per fold-seed is specified only in sar_limited_rerun_plan.md and its machine plan. It requires separate independent review and authorization.
