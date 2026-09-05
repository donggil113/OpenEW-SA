# Exact frozen implementation lookup

No architecture or training code changes are made here. The release snapshot's frozen_method_code_hashes.json records SHA256 of the reused source and configuration at the PR88 baseline.

- Input: 256 complex samples represented as two real float channels. P0/context packet RMS normalization, epsilon 1e-6; no mean removal. SOURCE-NORM/RX-NORM are separate preprocessing/model conditions.
- Encoder: frozen 1D residual CNN in wisig/models.py, 64-dimensional embedding, GroupNorm rather than BatchNorm. See exact kernel/stride/group definitions in the hashed file; do not retrofit normalization.
- P0 head: linear 64→6. P0-WIDE: 64→147→6 with ReLU/dropout 0.2. P2 peer score 64→32→1 with tanh; weighted peer mean plus anchor, fusion 128→64→6 with ReLU/dropout 0.2. Scoring is per peer, not anchor-conditioned.
- Primary support 128; per-query peers 32; no anchor in support. Source episodes have 33 nodes and exclude self as peer. Episode node budget 1056; independent batch 1024.
- AdamW lr 0.0005, weight decay 0.0001, max 30 epochs, patience 8, source-validation macro-F1 checkpoint selection. CORAL weight 0.1, GroupDRO eta 0.01, DANN reversal 0.1.
- T3A filter candidates (1,5,20,50,100,-1), selected on designated source-validation receivers; ties retain candidate order. -1 retains all. Warmup classifier rows and support embeddings are pseudo-labeled, entropy-filtered within class, L2-normalized and summed into L2-normalized class prototypes. Query embedding final dot product is not additionally L2-normalized. Reset for each receiver; no gradients/query updates.
- Supervised oracle: same 128 bank, labels explicitly revealed, frozen encoder, six-class linear head (390 parameters), AdamW zero decay. Grid lr (0.0001,0.0005,0.001) × steps (5,20), chosen using each source-validation simulation. Not universally fixed to the first smoke winner.
- Receiver-bootstrap and sign-flip random seed 20260903, 10,000 and 100,000 draws respectively. Seeds averaged within receiver first.
- Legacy PR85 config uses R2 for T3A test-time adaptation. The PR88/manuscript taxonomy instead groups all unlabeled support methods as R1 and reserves R2 for the supervised oracle. This is an explicit information-regime relabeling, not a method change.
- The top-level project's inherited package description still contains earlier research terminology. It is frozen and does not define the manuscript's claim; the manuscript explicitly excludes dynamic/hypergraph/neuro-symbolic claims.

Exact code and frozen configs take precedence over a shortened prose description. Conversion/split/data hashes and original experiment Git SHAs resolve through the prior freeze documents and current evidence/source_manifest.json.
