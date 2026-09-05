# Receiver-adaptation model configuration freeze

Status: **FROZEN AFTER SOURCE-ONLY SMOKE AND BEFORE NEW TARGET PREDICTION**

The source-only smoke used `receiver_loso_00`, seed 829, and its three already-designated source-validation receivers. It created no held-out-receiver prediction, loaded no held-out label for metrics or adaptation, and selected the supervised-oracle grid using source-validation receiver macro-F1 only.

All six preregistered candidates completed with finite losses. Mean source-validation receiver macro-F1 was:

| Learning rate | Steps | Mean macro-F1 |
|---:|---:|---:|
| 0.0001 | 5 | 0.823259 |
| 0.0001 | 20 | 0.825319 |
| 0.0005 | 5 | 0.825937 |
| 0.0005 | 20 | 0.833962 |
| 0.001 | 5 | 0.828498 |
| 0.001 | 20 | 0.840408 |

The smoke selected learning rate `0.001`, 20 steps. The full blinded runner repeats the same frozen source-validation-only selection per LOSO protocol/seed because its source checkpoint and designated validation receivers vary. It cannot use the target receiver. Ties follow the declared candidate order.

`SUP-FT-128` remains:

- frozen P0 source checkpoint reset per receiver;
- frozen backbone;
- linear six-class head only (390 adapted parameters);
- exact stable-hash 128 target support packets;
- labels revealed only because the condition is an oracle;
- full-support cross-entropy with AdamW and zero weight decay;
- no query access during adaptation;
- target predictions blinded until the create-once analysis step.

No P2 architecture, weight, support budget, k, loss, or optimizer changes. AdaBN/Tent stay not applicable; SHEN-GRL/other TTA/RF candidates stay excluded. The catastrophic threshold remains an absolute 0.05 macro-F1 loss from P0.

Smoke external record:

`/mnt/d/openew_sa_data/paper3/receiver_adaptation_benchmark/smoke/runs/receiver_loso_00__sup_ft_128__s829/`

The source-validation selection file SHA-256 is `3e6075fb7ddb7893f38c443d3848ceef00fdba811e8f7804888d0ecdfc8d791c`.
