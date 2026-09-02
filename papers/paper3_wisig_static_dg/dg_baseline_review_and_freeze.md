# Domain-generalization baseline review and freeze

This review was completed before held-out receiver/day metrics were computed. Selection used peer-review status, source-only feasibility, receiver-shift relevance, implementation auditability, and compute cost—not target performance.

## Selected baselines

### Source–source covariance alignment (`DG-CORAL`)

CORAL aligns second-order feature statistics. The original CORAL and Deep CORAL papers study domain adaptation with target-domain observations (Sun, Feng, and Saenko, AAAI 2016, DOI `10.1609/aaai.v30i1.10306`; Sun and Saenko, ECCV 2016, DOI `10.1007/978-3-319-49409-8_35`). This study does **not** use held-out target data. It preregisters a transparent source-only adaptation: pairwise covariance loss across source receiver groups present in a training minibatch. It is therefore named `DG-CORAL`, and no claim is made that the original paper prescribed this exact multi-source construction.

### Group distributionally robust optimization (`DG-GROUPDRO`)

GroupDRO minimizes a dynamically weighted worst-group training objective over predefined source groups (Sagawa, Koh, Hashimoto, and Liang, ICLR 2020, official OpenReview/ICLR paper). Here, source receiver identity defines the training groups. Held-out receiver labels and samples are unavailable during optimization. The same RF encoder and source-validation checkpoint rule are retained.

## RF-specific literature checked

- The official WiSig examples define a compact CNN on 256×2 I/Q packets and explicitly evaluate receiver and capture-day shifts. P0 uses the same input semantics but a compact PyTorch 1-D residual implementation shared by every study model.
- Shen et al., “Towards Receiver-Agnostic and Collaborative Radio Frequency Fingerprint Identification,” IEEE Transactions on Mobile Computing, DOI `10.1109/TMC.2023.3340039`, uses receiver-adversarial training on a separate LoRa testbed and also studies collaborative inference. It establishes task relevance but is not ported as an extra bespoke baseline: a faithful port would introduce LoRa-specific and collaborative-inference choices not fixed by WiSig, while substantially overlapping the source-domain-invariance role already covered here.

## Excluded methods

- **DANN:** the canonical JMLR method uses unlabeled target-domain data for adaptation. A source-only receiver discriminator would be a material protocol adaptation and duplicates the receiver-adversarial RF baseline family; it is documented but not one of the two frozen DG baselines.
- **IRM, Fishr, and SWAD:** excluded to avoid a broad method sweep after dataset access. The two selected methods already cover source covariance alignment and worst-source-group robustness with auditable implementations.
- **Fine-tuning or test-time adaptation:** forbidden because it would consume held-out receiver/day data and alter the deployment claim.

No RF-specific baseline was implemented from a title or incomplete description. The baseline set is frozen as P0, P0-WIDE, DG-CORAL, and DG-GROUPDRO before target evaluation.
