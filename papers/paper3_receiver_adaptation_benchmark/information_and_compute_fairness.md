# Information and compute fairness

Status: **VERIFIED CONTRACT AND RESULT**

The machine-readable ledger is external at /mnt/d/openew_sa_data/paper3/receiver_adaptation_benchmark/analysis/information_budget_ledger.csv.

| Method | Regime | Target support | Target labels | Test gradient | BN/stat update | Prototype update | Extra parameters |
|---|---|---:|---|---|---|---|---|
| P0 | R0 | 0 | no | no | no | no | no |
| P0-WIDE | R0 | 0 | no | no | no | no | yes |
| CORAL/DANN/GroupDRO | R0 | 0 | no | no | no | no | DANN only |
| RX-NORM | R1 | 128 | no | no | input statistics | no | no |
| T3A | R1 | 128 | no | no | no | class prototypes | no |
| P2 | R1 | 128 | no | no | no | no | context module |
| SUP-FT-128 | R2 oracle | 128 | **yes** | classifier head | no | no | no |
| AdaBN/Tent | R1 | — | no | — | — | — | not applicable |
| SHEN-GRL | R0 | — | no | — | — | — | excluded as unfaithful |

The frozen disjoint bank and query IDs are identical wherever the method contract permits. Query samples never adapt a method. T3A, RX-NORM, and P2 receive no labels; SUP-FT-128 is a diagnostic ceiling and is excluded from the confirmatory family.

External compute details are in compute_fairness_summary.csv. P0/T3A share 64,774 parameters. P2 has 75,143. SUP-FT adapts 390 parameters. AdaBN and Tent were not retrofitted because the frozen GroupNorm backbone has no BatchNorm; doing so would change the benchmark rather than add a faithful baseline.
