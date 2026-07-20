# Uncertainty-Calibrated Multi-View RF Signal Recognition for Open-Set Electromagnetic Spectrum Monitoring

## Motivation

Electromagnetic spectrum monitoring systems must classify RF activity under changing emitters,
receivers, propagation conditions, sensors, and interference regimes. Closed-set classifiers can
produce confident errors when exposed to unseen modulation families, unseen deployment domains, or
compound shifts. Paper 2 studies uncertainty-calibrated RF recognition that can identify known
signals while detecting open-set and out-of-distribution (OOD) samples.

## Problem Formulation

- Inputs: one or more RF views per sample, such as raw I/Q windows, PSD traces, spectrograms, or
  tabular signal-quality features.
- Known-label task: classify samples among known in-distribution RF classes.
- OOD task: assign high uncertainty or OOD score to samples from unknown classes, unseen domains, or
  both.
- Calibration task: align predicted confidence with empirical correctness under class, domain, and
  hybrid shifts.
- Selective prediction task: abstain on uncertain samples to reduce risk while preserving useful
  coverage.

Let `x = {x_iq, x_psd, x_tf, x_tab}` denote available views, `y` denote a known RF label, and `d`
denote a domain identifier such as sensor, receiver, day, band, jammer scenario, or dataset source.
Training observes known classes and training domains. Evaluation includes ID samples plus held-out
classes, held-out domains, or their union.

## Proposed Method

The planned method is a multi-view RF encoder with uncertainty calibration:

- View encoders for I/Q, PSD, spectrogram, and optional tabular metadata-derived features.
- Fusion layer that supports missing views and view-level reliability weighting.
- Known-class classifier trained on ID samples.
- OOD scoring from confidence, energy, entropy, distance-to-prototype, ensemble variance, or a
  learned uncertainty head.
- Post-hoc calibration using temperature scaling and protocol-specific validation splits.
- Selective prediction policy driven by calibrated confidence or OOD score.

Initial scripts in this scaffold focus on protocol generation and evaluation metrics. Model training
and artifact loading are left as future integration points.

## Datasets

OpenEW-SA converted artifacts will be reused where available:

- RadioML 2016.10A for modulation recognition and class-OOD experiments.
- DeepSense SDR WiFi for occupancy and day/domain shift experiments.
- ElectroSense PSD for technology recognition and sensor/frequency-domain shifts.
- JamShield for jamming/interference scenarios and jammer-domain holdouts.
- WiSig RF fingerprinting if transmitter/receiver metadata is available in converted artifacts.

All datasets should enter through the OpenEW-SA `metadata.csv`, `features.npy` or `features.pt`, and
`labels.json` convention.

## OOD Protocols

- Class OOD: train on known RF classes and evaluate unknown modulation, technology, occupancy, or
  jammer classes as OOD.
- Domain OOD: train on known domains and evaluate held-out sensors, receivers, days, bands, jammer
  sources, or dataset sources as OOD while preserving known labels where possible.
- Hybrid OOD: evaluate the union of held-out classes and held-out domains to emulate open-spectrum
  deployment.

Each protocol should produce train, validation-ID, test-ID, and OOD manifests with an `ood_label`
column where `0` is ID and `1` is OOD.

## Baselines

- Maximum softmax probability.
- Predictive entropy.
- Energy score.
- Temperature-scaled softmax.
- Deep ensemble uncertainty.
- MC dropout uncertainty.
- Mahalanobis or prototype distance in embedding space.
- OpenMax or EVT-style open-set recognition.
- Existing OpenEW-SA supervised baselines evaluated as closed-set references.

## Metrics

- Closed-set recognition: accuracy, macro F1, balanced accuracy, per-class support.
- Calibration: ECE, MCE, NLL, Brier score, average confidence, accuracy-confidence gap.
- OOD detection: AUROC, AUPR-OOD, FPR95, detection accuracy, threshold at best detection accuracy.
- Selective prediction: risk-coverage curve, area under risk-coverage curve, coverage at target
  risk.
- Robustness slices: metrics by dataset source, domain, class, SNR or frequency band where metadata
  is available.

## Current v0 Experimental Findings

The current v0 baseline results use lightweight closed-set classifiers and score functions over the
OpenEW-SA processed artifacts. The generated result tables are:

- Table A: OOD detection results from `paper2_v0_ood_results.md`.
- Table B: Calibration results from `paper2_v0_calibration_results.md`.
- Table C: Risk-coverage summary from `paper2_v0_risk_coverage_summary.md`.

Key findings:

- ElectroSense class-OOD: logistic regression improves OOD detection over nearest centroid. MSP and
  entropy AUROC are about 0.796 for logistic regression versus about 0.734 for nearest centroid MSP,
  with substantially stronger ID calibration and risk-coverage behavior.
- DeepSense day2-OOD: logistic regression has poor ID calibration and weak OOD detection. It reaches
  only about 0.484 AUROC for MSP/entropy and has high calibration error, while nearest centroid MSP
  is stronger for OOD detection at about 0.653 AUROC.
- JamShield scenario-OOD: logistic regression has strong ID calibration, with low ECE and high
  closed-set accuracy, but scenario-OOD detection remains weak at about 0.591 AUROC. This indicates
  that the model can be well calibrated on retained ID samples while still failing to separate
  scenario-shifted OOD samples.
- Main lesson: closed-set ID calibration does not guarantee robust OOD detection. Calibration and
  OOD separability must be evaluated as related but distinct properties.

Next experimental gaps:

- Temperature scaling for post-hoc calibration.
- Energy score from logits rather than probability-only scores.
- Mahalanobis or feature-distance OOD scoring.
- Multi-view fusion across I/Q, PSD, spectrogram, and tabular views where available.
- Per-domain and per-class error analysis to identify which emitters, days, sensors, or scenarios
  drive failures.

## v1-v3 Experimental Findings

Temperature scaling (v1) improved the DeepSense logistic-regression entropy AUROC from 0.484 to
0.527, but did not close the gap to the v0 nearest-centroid MSP result (0.653). Its effects on OOD
ranking were otherwise modest, reinforcing that calibration and OOD separation are distinct.

The train-fitted feature-distance experiment (v2) found strong ElectroSense cosine and Euclidean
distance rankings (AUROC 0.799 and 0.796), but weaker Mahalanobis ranking (0.772). JamShield distance
scores remained weak, with the best at about 0.50 AUROC. All DeepSense distances were systematically
inverted under the preregistered higher-distance-is-more-OOD orientation: cosine 0.378, Euclidean
0.384, and Mahalanobis 0.410 AUROC. This is evidence that the held-out day often lies closer to the
training prototypes than retained ID evaluation samples, not justification for an OOD-label-driven
orientation flip.

The v3 experiment robust-normalized every component using only ID validation medians and IQRs, then
applied equal-weight fusion with fixed higher-is-OOD orientation. It evaluated five variants without
using evaluation OOD labels for orientation, fitting, weights, variant choice, or threshold choice.
The descriptive best ElectroSense result combines temperature-scaled entropy, cosine, Euclidean,
and Mahalanobis scores (AUROC 0.893, AUPR-OOD 0.949, FPR95 0.393). The same four-component fusion is
the descriptive JamShield leader (AUROC 0.663), although FPR95 remains high at 0.904. DeepSense does
not benefit: its strongest v3 ranking is distance-only cosine-plus-Euclidean at 0.384 AUROC, and all
five variants remain below chance (0.316-0.384). Post-hoc negation gives 0.616-0.684 AUROC but is
reported only as an inversion diagnostic and was not used to alter the experiment.

Across v0-v3, the best observed AUROC changes from 0.799 to 0.893 on ElectroSense and from 0.591 to
0.663 on JamShield, while DeepSense v3 falls well below the v0 nearest-centroid MSP reference of
0.653. Scientifically, uncertainty and geometry provide complementary evidence for class novelty
and some scenario shifts, but geometric typicality is not domain-invariant. A distance can be
well-defined and validation-normalized yet point in the wrong direction after a domain change.

Unresolved limitations include a single split per dataset, correlated equal-weight components,
shared-covariance assumptions for Mahalanobis distance, probability-derived rather than logit-energy
uncertainty, and evaluation-descriptive detection-accuracy thresholds that are not deployable.
The next experiment should preregister an ID-validation-only density or two-sided tail-typicality
mapping, then apply it unchanged to untouched domain-OOD evaluations.

## Planned Tables And Figures

- Table 1: OpenEW-SA datasets, RF views, labels, domains, and OOD protocol mapping.
- Table 2: Class-OOD detection and calibration results.
- Table 3: Domain-OOD detection and calibration results.
- Table 4: Hybrid-OOD detection and selective prediction results.
- Table 5: Per-domain and per-class failure analysis.
- Table A: v0 OOD detection results.
- Table B: v0 calibration results.
- Table C: v0 risk-coverage summary.
- Figure 1: Multi-view RF uncertainty-calibrated recognition pipeline.
- Figure 2: Reliability diagrams across protocols.
- Figure 3: OOD score distributions for ID and OOD samples.
- Figure 4: Risk-coverage curves.
- Figure 5: Ablation of view combinations and calibration methods.
