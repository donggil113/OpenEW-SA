# Baseline applicability audit
Decision made before new target evaluation; post-hoc motivation is explicit.

| Candidate | Classification | Decision and fidelity boundary |
|---|---|---|
| SAR-GN | FAITHFULLY_APPLICABLE (optimization); bounded-support protocol documented | Official SAR explicitly configures GroupNorm/LayerNorm. No norm replacement. Reuse P0; support-only updates, then frozen query evaluation differ from original online access. |
| EMB-STD | FAITHFULLY_APPLICABLE as explicitly defined control, not literature reproduction | Source-aligned diagonal moment transport avoids silently feeding zero-centered features to an unmodified head expecting source coordinates. No target choice. |
| SHOT | UNFAITHFUL_TO_IMPLEMENT as exact frozen-source reproduction | Source label smoothing, learned bottleneck/BN and classifier parameterization are absent. Adding them changes frozen source training; deleting them and borrowing IM loss is not exact SHOT. Exclusion is not a claim that SHOT cannot ever use bounded support. |
| Shen-GRL | NOT_APPLICABLE to current compact representation | Official 52x126 channel-independent STFT and 2D source network require longer physically meaningful LoRa signal. |
| Full-network supervised adaptation | FAITHFULLY_APPLICABLE oracle | Same128 labeled support, source-only selection; not a population ceiling. |

## Primary evidence
SAR: Niu et al., ICLR2023, [paper](https://openreview.net/pdf?id=g2YraF75Tj), [official code](https://github.com/mr-eggplant/SAR), commit20f6e24b17525f34503510afccedc0629b67b7c4. sar.py configure_model/collect_params include GroupNorm; forward_and_adapt_sar implements two reliability filters, SAM and entropy recovery. main.py GN learning-rate rule and sam.py rho=.05 were inspected. Paper sections3.2 and appendixC.2 establish norm-affine updates. Bounded receiver reset, class-count margin and no-query adaptation are explicitly recorded, not called the original ImageNet experiment.
SHOT: Liang, Hu, Feng, ICML2020, [publisher](https://proceedings.mlr.press/v119/liang20a.html), [official code](https://github.com/tim-learn/SHOT), commitf7d555a0d53b525b885e5ef2a887a267a5be3c36. object/image_source.py label smoothing=.1; network.py bottleneck and classifier; image_target.py freezes C and updates F/B with information maximization plus centroid pseudo-labeling. Current P0 does not have this source recipe. No loose SHOT-like entry.
Shen: [official code](https://github.com/gxhen/receiverAgnosticRFFI), frozen commitffad4828c267324fc514a5a729aac93a9b6ff556; dataset_preparation.py STFT128 hop64 and adjacent-frame ratio; deep_learning_models.py expects52x126x1. See representation bridge.
EMB-STD and supervised oracle are transparent benchmark controls, not attributed as published novel methods. No data-dependent applicability ranking.

Official code/paper snapshots are external literature evidence only. No third-party RF payload acquired; no third-party implementation vendored.
