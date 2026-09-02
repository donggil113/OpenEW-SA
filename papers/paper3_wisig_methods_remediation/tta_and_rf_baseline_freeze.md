# Test-time adaptation and RF-baseline freeze

Status: **FROZEN BEFORE V2 TARGET-METRIC UNBLINDING**

The selection below was made from method applicability, primary papers, official implementations, the frozen GroupNorm backbone, and source-only validation feasibility. No V2 target metric was available.

## Implemented methods

| Method | Evidence | Exact V2 rule | Test labels | Target batch/support | Updates |
|---|---|---|---|---|---|
| T3A | Iwasawa and Matsuo, NeurIPS 2021; [paper](https://proceedings.neurips.cc/paper/2021/hash/1415fe9fea0fa1e45dddcff5682239a0-Abstract.html); [official code](https://github.com/matsuolab/T3A), locally pinned at `ff8cde5f06f61035c957720c6275c33893e0f564` | Initialize templates from the frozen linear classifier weights; append embeddings of the same 128 unlabeled receiver-support packets; pseudo-label with the source classifier; retain the lowest-entropy supports per pseudo-class; normalize and form prototype weights; classify disjoint queries by normalized prototype similarity. `filter_K` is selected on source-validation receiver simulations only from the official sweep `{1,5,20,50,100,-1}`. | No | Yes, fixed 128 | Prototype update; no gradients |
| RX-NORM | Direct receiver-calibration baseline, not claimed as a named literature reproduction | Estimate I/Q mean and residual RMS from exactly the fixed 128 receiver-support packets; apply them to disjoint queries. A separately source-normalized model is reset for each receiver. | No | Yes, fixed 128 | Input statistics only |
| SOURCE-NORM | Control for RX-NORM | Estimate the same I/Q statistics from source-training packets only and apply them without target support. | No | No | None at test |
| DG-DANN | Ganin et al., JMLR 2016, [official article](https://jmlr.org/papers/v17/15-239.html) | Source-only receiver-domain adversary with gradient reversal coefficient `0.1`; source receiver identities supervise only the training-time domain discriminator and are not model inputs. | No | No | Source training only |
| DG-CORAL | Sun and Saenko, ECCV 2016, DOI `10.1007/978-3-319-49409-8_35` | Retain PR #84's prespecified CORAL-style alignment among source receiver embeddings. This is described as CORAL-style source-domain alignment, not as a claim of exact target-aware Deep CORAL reproduction. | No | No | Source training only |
| DG-GROUPDRO | Sagawa et al., ICLR 2020, [official paper](https://openreview.net/forum?id=ryxGuJrFvS) | Retain PR #84 source-receiver robust loss and fixed source-only hyperparameters. | No | No | Source training only |

## Not applicable

| Method | Evidence | Decision |
|---|---|---|
| AdaBN | Li et al., *Revisiting Batch Normalization for Practical Domain Adaptation*, [paper](https://arxiv.org/abs/1603.04779) | **Not applicable.** The frozen PR #84 RF backbone uses GroupNorm and has zero BatchNorm modules. Retrofitting BatchNorm would change the controlled backbone and is prohibited. |
| Tent | Wang et al., ICLR 2021, [paper](https://openreview.net/forum?id=uXl3bZLkr3c); [official code](https://github.com/DequanWang/tent), locally pinned at `e9e926a668d85244c66a6d5c006efbd2b82e83e8` | **Not applicable.** The official method updates target normalization statistics and channel-wise affine parameters of normalization layers and its reference compatibility check requires BatchNorm. V2 will not retrofit BatchNorm or substitute a different, unverified GroupNorm variant. |

## RF-specific review

The official WiSig pipeline supplies both unprocessed and equalized 256-sample signal variants. A limited, separate official-equalization comparison is therefore preregistered for P0, P2, and P2-SHUFFLED; raw and equalized results will not be pooled. [Official WiSig dataset page](https://cores.ee.ucla.edu/downloads/datasets/wisig/).

Receiver-agnostic/adversarial RFFI work, including Shen et al., *Towards Receiver-Agnostic and Collaborative Radio Frequency Fingerprint Identification* (IEEE TMC), supports the relevance of receiver-adversarial source training. It is not implemented as a claimed faithful reproduction because its LoRa data, architecture, loss stack, and collaboration setting do not map exactly to ManyRx. Likewise, cross-receiver contrastive/subdomain methods found in the review lacked a verified official implementation that could be transferred faithfully without inventing missing choices. V2 therefore implements DANN as the auditable generic source-only adversarial baseline and records **no faithful RF-specific baseline** beyond the official equalization preprocessing control.

## Excluded source-DG methods

IRM, Fishr, and SWAD are not added. The preregistered suite already contains ERM, capacity matching, source covariance alignment, group-robust optimization, and a source receiver-domain adversary. Adding every generic DG family would substantially expand computation without a receiver-specific rationale. No method may be added after target unblinding.
