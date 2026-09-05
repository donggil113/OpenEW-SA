# Novelty boundary

| Prior work | Relationship | Classification | Boundary |
|---|---|---|---|
| WiSig source paper | Supplies multi-receiver/day data and receiver-shift motivation | REPRODUCTION / SYSTEMATIC EVALUATION | Dataset and receiver-transfer problem are not new |
| Shen receiver-agnostic work | Studies receiver/channel independence with different LoRa representation | RELATED EXISTING METHOD | No faithful Shen performance comparison on short-IQ WiSig; no payload obtained |
| T3A | Frozen source-model prototype adjustment is reused | REPRODUCTION | No algorithmic novelty or invented variant |
| Receiver normalization | RX-NORM / SOURCE-NORM change input statistics under explicit budgets | BENCHMARK CONTROL | Receiver normalization is not new |
| DANN / CORAL / GroupDRO | Frozen source-only objectives | PROTOCOL-SPECIFIC REPRODUCTION | Not exhaustive reproduction of original experiments |
| Standard TTA | Target support access is explicitly counted | SYSTEMATIC EVALUATION | Tent/AdaBN excluded for GroupNorm compatibility, not dismissed empirically |
| Learned P2 context | Existing frozen attentive fusion | NEGATIVE RESULT | Context dependence without meaningful P0 advantage; inferior to T3A |
| Present evidence package | Matched information, receiver-level reporting, source/code/result hashes, frank evidence progression | POTENTIAL NEW SYSTEMATIC EVALUATION | Novelty and publication sufficiency remain reviewer decisions |
| Collection journal and adapter | Prospective, synthetic-tested tools | ENGINEERING | Not new scientific RF evidence |

Maximum defensible claim: on the evaluated WiSig six-class protocol, bounded T3A adaptation improves source ERM under unseen-receiver shift more consistently than the evaluated learned context procedure, with support-size and probability-calibration caveats. No cross-dataset, acquired-episode or universal robustness claim follows.
