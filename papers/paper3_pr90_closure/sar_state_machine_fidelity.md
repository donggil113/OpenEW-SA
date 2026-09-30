# SAR state-machine fidelity and deviation boundary

Evidence class: synthetic software verification plus support-only forensic replay. No new held-out query score is included here.

## Reference code

We inspected the official SAR repository at commit [20f6e24b17525f34503510afccedc0629b67b7c4](https://github.com/mr-eggplant/SAR/tree/20f6e24b17525f34503510afccedc0629b67b7c4), especially [sar.py](https://github.com/mr-eggplant/SAR/blob/20f6e24b17525f34503510afccedc0629b67b7c4/sar.py) and [sam.py](https://github.com/mr-eggplant/SAR/blob/20f6e24b17525f34503510afccedc0629b67b7c4/sam.py). Their local SHA256s are 0553a395ac2bc087049720f1f162789079fe5ee25aa6a1cf82b2ea6286d66eff and b0569de29015016996feae257d30be6cc36f80d42d0f51d4a201eb39d2491712. The original paper is Niu et al., Towards Stable Test-Time Adaptation in Dynamic Wild World, ICLR 2023. The PR90 implementation is src/openew/paper3/reviewer_remediation/methods.py; it was not changed by this closure.

## State-transition findings

| Question | Observed branch and implication |
| --- | --- |
| Does reset_constant_em control official recovery? | SAR.forward passes the argument into forward_and_adapt_sar, but that function checks literal if ema < 0.2. Changing the constructor argument alone has no effect. A synthetic model with EMA about 0.586 and supplied threshold 0.9 still updates instead of resetting. |
| What happens to weights after a reset? | Official SAR.reset reloads copied model and wrapper optimizer state. Frozen PR90 reloads initial model state. |
| What happens to momentum? | Official SAM maintains its own wrapper state and a separate base_optimizer SGD momentum state. SAM.load_state_dict rebinds parameter groups but does not reload the base SGD state. A one-reset synthetic probe left 14 base SGD momentum buffers, while wrapper momentum buffers were zero. Frozen PR90 explicitly clears its SGD state on reset. This is a documented recovery-path deviation from literal upstream behavior, not official-code identity. |
| Does EMA survive? | Official wrapper calls reset(), which sets ema=None, then immediately assigns the returned ema. Frozen PR90 also retains the returned EMA across reset. The probe observed non-null EMA after reset. |
| Which logits does official forward return? | forward_and_adapt_sar returns logits calculated before its current optimizer update. Frozen WiSig V2 uses support-only adaptation, then predicts disjoint queries with the final adapted model in eval mode. They are different information and output timing protocols. |
| What if a reliable subset is empty? | Official code takes the mean of an empty tensor; it has no skip/restore branch. PR90 skips an empty first filter, or restores SAM perturbation and skips an empty second filter. These are numerical safety deviations, not upstream parity. Neither empty path occurred in the frozen 160 primary runs. |
| Is GroupNorm eligible? | Official configure_model and collect_params explicitly include GroupNorm; the frozen local parameter names are 14 GN affine tensors, 672 scalars. The RF model uses GN; no BatchNorm was retrofitted. |

## Scope of verification

The pre-existing audit_sar_fidelity.py checked **ten synthetic, single-update, noncollapse cases** only. It did not verify a ten-step sequence. The new sar_diagnostic.py and transition tests cover consecutive minibatches, first/last/repeated reset, retained EMA, momentum clearing, first/second empty filters, perturbation restoration, receiver isolation, non-GN classifier invariance, label-free support, absent query input, and a threshold argument that actually changes the branch. These synthetic tests are software tests; they do not make source- or target-domain performance claims.

The additional audit_sar_upstream.py synthetic probe found exact final tensor parity for two consecutive nonreset minibatches (maximum absolute error zero). It also reproduced the ignored upstream threshold argument, persisted base SGD momentum after wrapper reset, and preupdate returned logits. Its JSON is stored at sar/upstream_state_probe.json in the new closure root. The 160 support-only forensic replays matched the *frozen local* adapted checkpoint tensors exactly, including reset-dominated cases.

**Not tested as upstream-equivalent:** empty-filter corner handling, reset-then-later-nonreset sequences with momentum divergence, official online query-update protocol, or arbitrary thresholds in upstream code. The new diagnostic threshold parameter is used in its actual comparison branch. Threshold B, 0.2 log(C)/log(1000), is an explicitly post-hoc normalization hypothesis; it is not the official SAR default.

No existing PR90 scientific source, saved checkpoint, prediction, metric or manifest was changed.
