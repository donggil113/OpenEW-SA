# Structural numbers and derivations

The generated numerical_traceability_matrix.md covers every exported result row and all method/metric cells, with original SHA and Git lineage. This companion covers non-result constants in text, captions and protocol tables. Generated numerical macros are mapped in evidence/manuscript_number_macros.json. Rounding is six decimals in primary tables/text and four in budget diagnostics; no number is manually optimized.

| Literal / definition | Exact source / location | Unit / status |
|---|---|---|
| 32 LOSO; 28 train, 3 validation, 1 test | ../paper3_wisig_methods_remediation/split_freeze_v2.md; configs/paper3/wisig_v2/ | Physical receiver; frozen design |
| 6 transmitter classes | Same split freeze; source-support eligibility | Classes, not full WiSig universe |
| 5 seeds: 829,1829,2829,3829,4829 | methods_remediation_preregistration_v2.md and primary grid | Algorithmic replicates; not extra receivers |
| 128 support, 32 peers | V2 model_config_freeze_v2.md; src/openew/paper3/wisig_v2/support.py | Packets; no temporal meaning |
| 256 complex samples, two real channels | src/openew/paper3/wisig/schema.py and frozen ManyRx manifest | Input representation |
| 16/32/64 channels; 64 embedding | src/openew/paper3/wisig_v2/models.py and reused wisig models | Architecture, unchanged |
| 30 epochs; patience 8; learning rate 5e-4; weight decay 1e-4 | configs/paper3/wisig_v2/methods_v2.yaml; model freeze | Maximum optimizer budget; not selected target epoch |
| 10,000 bootstrap; 100,000 sign flips | evidence/receiver_level_inference.json / T3A_MINUS_P0 | Receiver-level; seeds averaged first |
| 31 positive / 32 | Same JSON receiver_delta_summary | Positive receiver mean deltas |
| 15-bin ECE; degradation >0.05 | Frozen V2 metrics and PR88 benchmark_preregistration.md | Descriptive metric / receiver-seed harm threshold |
| One Holm comparison | PR88 benchmark_preregistration.md; receiver_level_inference.json | T3A_MINUS_P0 only; later evidence timing |
| Budgets 16/32/64/128/256 | support_budget_summary.csv, method + support_budget | Post-hoc common-query grid; 128 stays primary |
| 7 B210, 16 N210, 9 X310; three families | hardware_family_summary.csv | Physical receiver counts; descriptive |
| Figures 1–8; Tables I–VI; RQ1–RQ7; equation/section indices | Manuscript layout | Labels, not scientific measurements |
| PR84–88; V0/V1/V2; P0/P1/P2; T3A; R0/R1/R2 | Frozen package identifiers and information regime ledger | Identifiers, not numeric empirical claims |

The Git tree inherited from 7cc9a27a6cf049690c881068d9163b942c6a2110 is the method/protocol reference; evidence/source_manifest.json supplies result-producing Git SHAs. No rounded value is used to recalculate inference.
