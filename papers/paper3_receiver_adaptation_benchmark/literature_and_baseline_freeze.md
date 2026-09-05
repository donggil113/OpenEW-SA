# Literature and baseline applicability freeze

Status: **FROZEN BEFORE NEW TARGET EVALUATION**

P0/P0-WIDE, DANN, CORAL, GroupDRO, SOURCE/RX-NORM, T3A, and P2 are reused from V2 after hash verification. `SUP-FT-128` is a separately labeled oracle.

AdaBN modulates BatchNorm statistics (Li et al., arXiv 1603.04779 / ICLR workshop 2017). The frozen backbone has zero BatchNorm modules. `ADABN-128` is **NOT APPLICABLE**.

Tent (Wang et al., ICLR 2021; official `DequanWang/tent`) estimates normalization statistics and optimizes channel-wise affine normalization parameters. Replacing GroupNorm or inventing a GroupNorm variant changes the controlled backbone. `TENT-128` is **NOT APPLICABLE**.

The official Shen code (`gxhen/receiverAgnosticRFFI`, commit `ffad4828c267324fc514a5a729aac93a9b6ff556`) applies AWGN, a channel-independent STFT, and a 2-D residual CNN with `(52,126,1)` input, a 512-dimensional normalized feature, and two 128-unit transmitter/receiver heads. The receiver head follows gradient reversal; both loss weights are one. Training uses SGD `1e-3`, momentum `0.9`, up to 500 epochs, patience 20. Frozen 256-IQ does not yield the official geometry. `SHEN-GRL` is **EXCLUDED AS UNFAITHFUL**; DG-DANN is not renamed.

SHOT uses iterative target-population representation updates rather than this bounded support API. LAME and batch-coupled methods require query interaction. Published GAN-RXA/feature-disentanglement candidates lack a verified frozen-256-IQ implementation without new pairing/architecture choices. No second TTA or RF-specific method is added merely to expand the table.

Primary sources:

- <https://openreview.net/forum?id=uXl3bZLkr3c> and <https://github.com/DequanWang/tent>
- <https://arxiv.org/abs/1603.04779>
- <https://proceedings.neurips.cc/paper/2021/hash/1415fe9fea0fa1e45dddcff5682239a0-Abstract.html>
- <https://jmlr.org/papers/v17/15-239.html>
- <https://openreview.net/forum?id=ryxGuJrFvS>
- <https://livrepository.liverpool.ac.uk/3176924/>
- <https://doi.org/10.1109/TMC.2023.3340039>
- <https://github.com/gxhen/receiverAgnosticRFFI>
- <https://doi.org/10.1109/TCCN.2023.3329012>

No target receiver result informed this freeze.
