# Receiver-adaptation benchmark preregistration

Status: **FROZEN BEFORE ANY NEW TARGET-RECEIVER METRIC**

## Scientific question

Among source-only generalization and unlabeled test-time receiver adaptation strategies, which methods most reliably improve transmitter recognition under unseen physical receiver shift when target information budgets are matched? The secondary question is how much unlabeled receiver support is needed before adaptation becomes beneficial.

This phase does not tune or rescue P2. Frozen WiSig V2 results are prior evidence and are reused only after hash verification. The receiver remains the inferential unit; packets are never bootstrap units.

## Evidence boundary and method set

R0 source-only methods receive no target support. R1 methods receive the exact frozen disjoint receiver bank. R2 is the supervised target-adaptation oracle. Queries never participate in adaptation. Receiver IDs select support but are not embedded.

Frozen P0, P0-WIDE, DG-CORAL, DG-DANN, DG-GROUPDRO, RX-NORM, T3A, and P2 are reused. AdaBN/Tent are not applicable because the frozen model has GroupNorm and no BatchNorm. Official SHEN-GRL cannot be faithfully transferred: it requires a 52-by-126 channel-independent spectrogram and distinct 2-D CNN, not frozen 256-IQ. No approximate second TTA/RF method passed pre-result gates.

`SUP-FT-128` is a label-dependent diagnostic ceiling. It resets P0 per receiver, freezes the backbone, and fine-tunes only the linear head using the exact 128 support labels. Candidate learning rates `{1e-4,5e-4,1e-3}` and steps `{5,20}` are selected on source-validation receivers only, with full-bank cross-entropy, AdamW, and zero weight decay.

## Support and inference

Budgets are `0,16,32,64,128,256`; 128 remains reference. Frozen P2/T3A curves are reused. RX-NORM receives the same nested stable-hash banks and a common query pool after reserving 256 samples. Its zero counterpart is SOURCE-NORM; P2 zero is P2-NULL; T3A zero retains source classifier templates and is a mechanism control.

The exact V2 32 LOSO splits, five seeds, six-class split-local maps, support hash rule, and query IDs remain immutable. All new predictions contain sample IDs plus probabilities only. One-time unblinding occurs after every expected record is complete, hashes are frozen, analysis code is committed, and the repository is clean.

Primary outcome is equal-weight receiver macro-F1. Secondary outcomes: accuracy, balanced accuracy, ECE, NLL, entropy, hardware variation, budget behavior, and compute. Catastrophic adaptation is an absolute macro-F1 drop greater than `0.05` from matched P0.

Seeds are averaged inside receiver. The confirmatory family contains only `T3A-P0`, because every proposed new deployable method failed applicability before target access. It uses 10,000 receiver bootstraps, 100,000 two-sided sign flips, seed `20260903`, and Holm correction. P2 and the supervised oracle are descriptive inherited/diagnostic evidence.

Stop for any artifact-hash mismatch, split/query mismatch, deployable-method label leakage, unexpected config, non-finite prediction, or V2 overwrite attempt. No receiver, seed, or bad result may be removed.
