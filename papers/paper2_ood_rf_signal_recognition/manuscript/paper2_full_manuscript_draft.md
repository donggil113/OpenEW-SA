# Uncertainty-Calibrated Multi-View RF Signal Recognition for Open-Set Electromagnetic Spectrum Monitoring

## Abstract

Electromagnetic spectrum monitors encounter signal classes, receivers, acquisition days, and interference scenarios that are absent from closed-set training data. A recognizer can therefore be accurate and apparently well calibrated on retained in-distribution (ID) samples while assigning unwarranted confidence to operationally novel observations. This study develops a reproducible open-set evaluation path over existing OpenEW-SA processed artifacts from ElectroSense, DeepSense, and JamShield. The approach combines a calibrated predictive-uncertainty view with train-fitted feature-geometry views. A scalar temperature is fitted only on ID validation predictions; temperature-scaled entropy, nearest-centroid cosine distance, and nearest-centroid Euclidean distance are then normalized using validation-only robust statistics and averaged to form the prespecified primary score, `ts_entropy_cosine_euclidean`. A variant that additionally includes Mahalanobis distance is retained as an exploratory ablation. All scores use a fixed higher-is-more-OOD orientation, and evaluation OOD labels are not used to choose orientations, weights, methods, or thresholds. Stratified paired bootstrap analysis shows that the primary fusion is effective for ElectroSense class novelty and improves AUROC against the prespecified comparators for JamShield scenario shift. JamShield nevertheless exhibits an operating-metric trade-off: AUPR-OOD and FPR95 are not uniformly better against every comparator. DeepSense remains a negative fixed-orientation result, indicating that a held-out acquisition day can appear more geometrically typical than retained ID data. Post-hoc score negation is reported only as a diagnostic and does not replace the primary result. These findings support a dataset-dependent view of uncertainty-distance fusion and show that closed-set calibration alone does not ensure robust OOD separation.

**Keywords:** RF signal recognition; electromagnetic spectrum monitoring; out-of-distribution detection; open-set recognition; uncertainty calibration; temperature scaling; feature distance; score fusion

## Introduction

Electromagnetic spectrum monitoring systems are expected to recognize known activity while operating across changing emitters, receivers, sites, propagation conditions, acquisition schedules, and interference regimes [@itu2011spectrum; @rajendran2018electrosense]. Conventional supervised recognition assumes that evaluation samples belong to the same label and domain support as the training set. That assumption is fragile in open-spectrum operation, where an unknown signal technology, a new acquisition domain, or a previously unseen jammer scenario may be encountered without an OOD label available at decision time. Closed-set models can remain confident under such shifts, so classification confidence and OOD separability must be evaluated as related but distinct properties [@ovadia2019trust; @nguyen2015fooled].

RF OOD evaluation also has a protocol-design problem. An apparent detector can be improved after the fact by reversing a score, selecting the strongest test comparator, fitting normalization on evaluation samples, or optimizing a threshold using OOD labels. Those operations leak information from the target shift and can turn a diagnostic observation into an overstated primary result. A deployment-relevant experiment instead fixes the score direction and analysis roles in advance, fits classifiers and distance models on training data, fits calibration and normalization on ID validation data, and leaves the test ID and test OOD rows untouched until evaluation [@shafaei2019biased; @yang2022openood].

This work studies that disciplined path on the OpenEW-SA artifact convention. The term *multi-view* has two scopes here. Across datasets, the evaluation includes processed power-spectral-density (PSD), in-phase/quadrature (I/Q), and tabular radio/network representations. Within the proposed detector, the fused views are complementary evidence sources: predictive uncertainty and two forms of feature-space distance. The current experiments do not claim an end-to-end, within-sample fusion of raw I/Q, PSD, spectrogram, and metadata inputs; that broader multimodal model remains future work.

The study makes four contributions. First, it defines frozen class-OOD and domain/scenario-OOD evaluations for ElectroSense, DeepSense, and JamShield while preserving symbolic RF labels. Second, it connects a lightweight supervised recognition baseline, validation-fitted temperature scaling, and train-fitted feature-distance scores in one reproducible pipeline. Third, it specifies `ts_entropy_cosine_euclidean` as an equal-weight primary fusion after ID-validation-only robust normalization, while keeping the Mahalanobis-augmented fusion exploratory. Fourth, it reports fixed-orientation point estimates and paired bootstrap uncertainty, including a negative DeepSense result and a post-hoc inversion diagnostic that is explicitly excluded from the primary analysis.

The resulting evidence is intentionally bounded. The primary method performs differently across the three shifts, and no universal generalization or universal statistical-significance claim is made. Instead, the analysis asks where calibrated uncertainty and feature geometry agree, where they trade off across metrics, and where their assumed higher-is-more-OOD direction breaks under domain change.

## Related Work

### Open-set and OOD recognition for RF monitoring

Open-set recognition distinguishes known-class classification from the additional requirement to reject observations outside the modeled class support [@scheirer2013toward; @geng2021recent]. OOD detection broadens the concern to covariate and domain shifts that can preserve labels while changing the observation distribution. Both settings are relevant to RF monitoring because channel, receiver, and acquisition-day changes can alter RF feature distributions independently of the nominal recognition task [@alshawabka2020exposing; @hanna2022wisig]. The transferability of OOD evidence from other application domains therefore remains an empirical question in RF monitoring.

### Confidence and calibration

Maximum softmax probability is a common post-hoc confidence/OOD baseline [@hendrycks2017baseline]. Predictive entropy is also widely used as a predictive-uncertainty summary [@ovadia2019trust], while logit energy provides a distinct score computed from classifier logits [@liu2020energy]. Temperature scaling fits a scalar on held-out ID predictions to improve probabilistic calibration while leaving the classifier architecture fixed [@guo2017calibration]. These techniques address different properties: calibration concerns the relationship between confidence and correctness on a specified distribution, whereas OOD detection concerns ranking or separating a shifted population. Their relationship should therefore be tested rather than assumed.

### Feature geometry and score fusion

Prototype and nearest-neighbor approaches score a sample by its position relative to training features; Euclidean and cosine distances encode different geometry [@snell2017prototypical; @sun2022knn]. A shared-covariance Mahalanobis score adjusts directions by estimated within-class variability [@lee2018mahalanobis]. Their usefulness depends on whether novelty actually maps to increasing distance in the learned or processed representation. Combining uncertainty and distance can expose complementary evidence, but score scales must be aligned without consulting evaluation OOD labels.

### Statistical evaluation of OOD scores

AUROC, AUPR with OOD as the positive class, and FPR at a high OOD true-positive rate summarize different aspects of ranking and operating behavior [@hendrycks2017baseline; @liang2018enhancing]. Percentile bootstrap intervals and paired learner comparisons provide methodological underpinnings for uncertainty estimation on shared observations [@efron1993bootstrap; @dietterich1998approximate]. Neither source prescribes the exact composite resampling scheme used in this study; that analysis design is specified explicitly in Methods. Confidence intervals quantify uncertainty conditional on the observed dataset and resampling design; they do not establish performance on every future domain.

## Datasets and OOD Evaluation Protocols

The experiments use converted OpenEW-SA artifacts with one metadata row per sample, an index into a shared feature array, and symbolic labels loaded as strings. Each frozen protocol contains an ID training split, an ID validation split, an ID test split, and an OOD test split. The evaluation CSV is the concatenation of test ID and test OOD rows only. Table 1 reports the verified evaluation counts used by every compared v3 method.

**Table 1. Dataset and OOD protocol summary.** Counts refer to the frozen evaluation set, not the training or validation partitions.

| Dataset | Processed input view | Recognition target | OOD protocol | ID definition | OOD definition | ID samples | OOD samples | Total |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| ElectroSense | PSD features | Signal technology | Class OOD | DAB, DVB-T, FM, and LTE classes | GSM and TETRA classes | 5,840 | 16,550 | 22,390 |
| DeepSense | I/Q features | WiFi occupancy code | Acquisition-day OOD | Retained day-one samples | Held-out day-two samples | 3,200 | 16,000 | 19,200 |
| JamShield | Tabular radio/network metrics | Normal versus abnormal interference | Scenario OOD | Retained benign and jammer scenarios | Held-out benign and jammer scenarios | 14,534 | 19,817 | 34,351 |

<!-- TRACE: N001, N002, N003 -->

### ElectroSense class OOD

ElectroSense provides crowdsensed PSD data and an official wireless-technology classification framework [@rajendran2018electrosense; @scalingi2023framework; @scalingi2023electrosensepsd]. The taxonomy and split used here are scoped to the converted OpenEW-SA subset: DAB, DVB-T, FM, and LTE are treated as known classes for classifier fitting and ID evaluation, while GSM and TETRA are withheld from classifier training and treated as OOD at evaluation. The upstream framework code also defines an `unkn` label; the analyzed frozen manifest and split artifacts contain only the six named technology labels and therefore exclude `unkn`. This six-class construction is not attributed to the Zenodo record itself.

### DeepSense acquisition-day OOD

DeepSense contributes processed I/Q windows labeled by binary occupancy codes [@uvaydov2021deepsense; @wineslab2021deepsensedataset]. All occupancy codes remain known labels, while the acquisition day defines the shift: retained day-one rows provide train, validation, and test-ID samples, and held-out day-two rows provide OOD samples. Labels such as `0000`, `0001`, `0010`, and `0100` are identifiers and are read and written as strings so their leading zeros cannot be lost. This protocol tests domain shift rather than unseen-class rejection; the official dataset record documents different transmitter orientations across the two acquisition days.

### JamShield scenario OOD

JamShield contributes tabular radio and network telemetry for normal-versus-abnormal interference recognition [@panitsas2025jamshield; @panitsas2024jamshielddataset]. Both recognition labels occur in the retained scenarios, while a frozen subset of benign and jammer scenarios is held out as OOD. The task therefore asks whether a classifier and its training geometry can identify scenario novelty even when the nominal label vocabulary remains unchanged. The exact retained and held-out domain identifiers are fixed in the split manifests. The peer-reviewed ICC 2025 publication is cited for the system, while the public dataset record supports the scenario and telemetry provenance; no explicit dataset license was identified in the verified public records.

### Leakage controls

Training features and labels are used to fit the classifier and the class centroids. ID validation predictions are used to fit temperature scaling, and ID validation component scores are used to fit score normalization. Test-ID and test-OOD labels are used only for final metric computation, audit alignment, and the explicitly labeled post-hoc DeepSense diagnostic. They are not used to choose the score orientation, normalization statistics, fusion weights, primary method, comparator set, or a deployment threshold.

## Methods

### Notation and fixed score orientation

Let (x) denote a processed RF feature vector, (y) a known-class label, (p_k(x)) the classifier probability for class (k), and (z(x)) the feature representation used by the classifier and distance models. Every OOD component is oriented before evaluation so that a larger value means more OOD-like. This convention is retained even when a dataset produces an inverted ranking. OOD labels do not enter any score definition.

### Baseline confidence scores

The supervised baseline produces class probabilities and a predicted label for each validation and evaluation sample. The maximum-softmax-probability OOD score is implemented as

\[
s_{\mathrm{MSP}}(x) = 1 - \max_k p_k(x),
\]

so lower classifier confidence becomes a larger OOD score. Predictive entropy is

\[
s_{\mathrm{ent}}(x) = -\frac{\sum_k p_k(x)\log p_k(x)}{\log K},
\]

where (K) is the number of known classes. The normalization bounds entropy across class counts while preserving the higher-is-more-OOD convention. The pipeline also supports an energy score when logits are present, but the verified publication comparison uses temperature-scaled entropy rather than logit energy. Random scoring, raw MSP, and raw entropy are retained as smoke-test or contextual v0 baselines; they are not the prespecified v3 primary method.

Probability-column suffixes are treated as symbolic class labels. This is consequential for DeepSense, where a digit-looking occupancy code is not an integer. Label matching therefore preserves strings and can recover a unique fixed-width suffix only when a prior CSV reader has already removed leading zeros.

### Temperature scaling

A single positive temperature (T) is selected on ID validation predictions by minimizing negative log likelihood. When classifier logits are unavailable, the implementation takes the logarithm of the class probabilities after numerical clipping, divides those log-probabilities by (T), and applies a softmax:

\[
\tilde p_k(x;T) = \frac{\exp(\log p_k(x)/T)}{\sum_j \exp(\log p_j(x)/T)}.
\]

The selected temperature is then frozen and applied to validation, test-ID, and test-OOD predictions. Temperature-scaled predictive entropy is the uncertainty component used in the primary fusion and is also a prespecified standalone comparator. The procedure follows validation-fitted scalar temperature scaling [@guo2017calibration]: it calibrates a closed-set probability model on ID validation data, does not use OOD labels, and does not, by construction, guarantee OOD separation.

### Feature-distance scoring

All feature-distance models are fitted on the ID training split only. Following prototype and feature-distance formulations [@snell2017prototypical; @sun2022knn], for each known class (k), the class centroid is

\[
\mu_k = \frac{1}{|\mathcal{T}_k|}\sum_{i\in\mathcal{T}_k} z(x_i).
\]

The nearest-centroid Euclidean score is the minimum Euclidean distance to a class centroid:

\[
s_{\mathrm{euc}}(x) = \min_k \|z(x)-\mu_k\|_2.
\]

The cosine score normalizes both samples and centroids and computes

\[
s_{\mathrm{cos}}(x) = 1 - \max_k \frac{z(x)^\top\mu_k}{\|z(x)\|_2\|\mu_k\|_2}.
\]

For Mahalanobis scoring, within-class residuals are pooled into a shared covariance estimate following the tied-covariance formulation of Lee et al. [@lee2018mahalanobis]. As an implementation detail of this study, a diagonal regularizer is added and a numerically stable pseudo-inverse is computed. The score is the minimum square-root Mahalanobis distance:

\[
s_{\mathrm{mah}}(x) = \min_k \sqrt{(z(x)-\mu_k)^\top\Sigma_{\mathrm{reg}}^{+}(z(x)-\mu_k)}.
\]

All three are distances, so larger scores remain more OOD-like. Nearest-centroid cosine and Euclidean distances are prespecified comparators and components of the primary fusion. Mahalanobis distance appears only in the exploratory four-component ablation.

### Validation-only robust normalization

The component scores have different units and ranges. For each component (c), the method estimates a median (m_c) and interquartile range (q_c) from ID validation scores only, then applies the frozen transform

\[
\hat s_c(x)=\frac{s_c(x)-m_c}{q_c+\epsilon}.
\]

The implementation uses a small positive stabilizer. If the validation interquartile range is zero or non-finite, the validation standard deviation is used; if that scale is also unusable, unit scale is used and recorded as a warning. Evaluation scores, sample classes, and OOD labels do not affect the center or scale. This makes the normalization deployable in the limited sense that it can be fixed before the target OOD population is observed.

### Equal-weight uncertainty-distance fusion

The prespecified primary method, `ts_entropy_cosine_euclidean`, averages the normalized temperature-scaled entropy, nearest-centroid cosine distance, and nearest-centroid Euclidean distance:

\[
s_{\mathrm{primary}}(x)=\frac{1}{|\mathcal{C}|}\sum_{c\in\mathcal{C}}\hat s_c(x),
\quad
\mathcal{C}=\{\mathrm{TS\ entropy},\mathrm{cosine},\mathrm{Euclidean}\}.
\]

Weights are equal and are not fitted on evaluation performance. The method `ts_entropy_cosine_euclidean_mahalanobis` adds the normalized Mahalanobis component with equal weighting. It is an exploratory ablation, not a replacement primary analysis. In this implementation, “multi-view” fusion refers to uncertainty and geometric score views over the same dataset-specific processed representation.

### OOD metrics and tied-score handling

OOD is the positive class for all detection metrics. AUROC evaluates global ranking. AUPR-OOD evaluates positive-class precision-recall behavior. FPR95 is the minimum ID false-positive rate at which OOD true-positive rate reaches the target operating level; lower is preferable [@hendrycks2017baseline; @liang2018enhancing]. Detection accuracy is the best accuracy over thresholds of the rule “score at or above the threshold is OOD.” Because that threshold is optimized on the evaluation sample, detection accuracy is **evaluation-descriptive** and must not be interpreted as a deployment-valid operating point.

Paper 2 uses its existing stable-order AUPR-OOD implementation. Samples are sorted by descending OOD score with a stable mergesort; precision is evaluated at each OOD-positive rank and averaged over the OOD rows. Equal-score rows therefore retain their input-CSV order. The same implementation is used for every point estimate and bootstrap replicate. This convention is documented because it can differ from grouped-threshold average-precision implementations when scores are tied.

### Bootstrap statistical analysis

The percentile-bootstrap and paired-comparison literature provides methodological underpinnings for this analysis [@efron1993bootstrap; @dietterich1998approximate], but neither source prescribes the exact composite procedure used here. In our analysis design, uncertainty is estimated with 1,000 nonparametric replicates: ID and OOD groups are resampled separately at their original evaluation counts, and identical sampled ID and OOD indices are reused across all methods within each dataset and replicate. This shared-index construction enables paired left-minus-right differences. Pointwise percentile 95% confidence intervals are reported for AUROC, AUPR-OOD, FPR95, and detection accuracy. The deterministic seed is recorded in the external analysis metadata. <!-- TRACE: N004 -->

The paired comparison set is fixed: primary versus temperature-scaled entropy, primary versus nearest-centroid cosine, primary versus nearest-centroid Euclidean, and exploratory four-component fusion versus primary. An interval that excludes zero supports a difference only for that dataset, metric, score orientation, and comparison. No family-wise multiplicity adjustment is applied, so interval exclusion is not described as universal statistical significance.

## Experimental Setup

### Artifact and split pipeline

Each processed artifact directory contains `metadata.csv`, `labels.json`, and a shared NumPy feature array when available. A unified Paper 2 manifest stores `sample_id`, dataset, task, label, domain, input type, feature path, and feature index. Protocol-specific split CSVs preserve these columns and append the split and OOD label. The evaluation file contains test-ID and test-OOD rows, matching the prediction and score files one-to-one by `sample_id`.

### Supervised classifier and calibration

The publication pipeline uses standardized logistic regression as the classifier underlying temperature-scaled entropy. It is fitted on the ID training split and writes symbolic true and predicted labels, confidence, and one probability column per known class for ID validation, test ID, and test OOD. Temperature scaling is fitted on the validation prediction file and then applied without further adjustment. Earlier nearest-centroid probability baselines and raw logistic-regression confidence scores are retained in the v0-v3 publication summary as contextual results, not as selected primary competitors.

### Distance and fusion stages

The v2 stage fits Euclidean, cosine, and shared-covariance Mahalanobis distance models using training features only. The v3 stage converts calibrated predictions to entropy scores, scores the validation and evaluation manifests with the distance models, robust-normalizes each component on ID validation data, and writes strictly sample-aligned fused scores. The analysis roles were held fixed: `ts_entropy_cosine_euclidean` is the prespecified primary method; temperature-scaled entropy, nearest-centroid cosine, and nearest-centroid Euclidean are prespecified comparators; and the Mahalanobis-augmented fusion is exploratory.

### Evaluation integrity

All compared v3 score files contain the same ordered sample IDs, true labels, and OOD labels within each dataset. DeepSense occupancy identifiers remain symbolic strings. Non-finite scores are rejected. The publication analysis consumes frozen v0-v3 snapshots and writes separate tables, figures, bootstrap summaries, and provenance metadata. The manuscript integration reported here reads those verified outputs and does not rerun training, score generation, or bootstrap sampling.

## Results

### Prespecified primary method

Table 2 reports the fixed-orientation primary results. Values are point estimates followed by percentile 95% confidence intervals. The three datasets show materially different behavior. ElectroSense has strong class-OOD ranking and the lowest primary FPR95 among the three evaluations. DeepSense is a negative result: primary AUROC is below chance and FPR95 is near the upper end of its range. JamShield has above-chance AUROC but a high FPR95, indicating that global ranking improvement does not imply a uniformly favorable high-recall operating point.

DeepSense contains 3,200 ID and 16,000 OOD rows among 19,200 evaluation observations, giving OOD prevalence 0.833333. The corresponding no-skill AUPR-OOD baseline and all-OOD trivial detection-accuracy baseline are therefore both 0.833333. The primary AUPR-OOD, 0.737936, is below its no-skill baseline, while the evaluation-descriptive detection accuracy, 0.833490, is only marginally above the all-OOD baseline. These descriptive anchors reinforce the fixed-orientation negative result; they are not additional statistical tests, and detection accuracy remains evaluation-descriptive. <!-- TRACE: N002, N010, N012, N017, N018 -->

**Table 2. Bootstrap confidence intervals for the prespecified primary method.** Detection accuracy is evaluation-descriptive because its threshold is selected on the evaluation sample.

| Dataset | AUROC [95% CI] | AUPR-OOD [95% CI] | FPR95 [95% CI] | Detection accuracy [95% CI] |
| --- | ---: | ---: | ---: | ---: |
| ElectroSense | 0.857037 [0.851138, 0.862585] | 0.934429 [0.930849, 0.937570] | 0.434589 [0.420886, 0.447774] | 0.856632 [0.853235, 0.860741] |
| DeepSense | 0.352958 [0.340919, 0.364553] | 0.737936 [0.733647, 0.742146] | 0.992188 [0.989062, 0.995313] | 0.833490 [0.833333, 0.833750] |
| JamShield | 0.657625 [0.652294, 0.663324] | 0.710403 [0.704694, 0.716541] | 0.927205 [0.922869, 0.931402] | 0.634887 [0.630957, 0.639196] |

<!-- TRACE: N005, N006, N007, N008, N009, N010, N011, N012, N013, N014, N015, N016 -->

*[Figure 1 about here: `figure_ood_auroc_with_ci`.]*

*[Figure 2 about here: `figure_fpr95_with_ci`.]*

### Paired comparisons

Table 3 states the decision for every reported paired interval. A positive sign means that the left method has a larger metric value; a negative sign means it has a smaller value. For AUROC, AUPR-OOD, and detection accuracy, larger values are ordinarily favorable. For FPR95, smaller values are favorable. Detection-accuracy comparisons remain evaluation-descriptive even when their intervals exclude zero.

**Table 3. Paired method differences and interval decisions.** Each cell refers to a left-minus-right percentile confidence interval. Exact differences and interval bounds are preserved in `paper2_v3_paired_differences.csv`.

| Dataset | Left-minus-right comparison | AUROC | AUPR-OOD | FPR95 | Detection accuracy |
| --- | --- | --- | --- | --- | --- |
| ElectroSense | Primary - TS entropy | Excludes zero (+) | Excludes zero (+) | Excludes zero (-) | Excludes zero (+) |
| ElectroSense | Primary - NC cosine | Excludes zero (+) | Excludes zero (+) | Excludes zero (-) | Excludes zero (+) |
| ElectroSense | Primary - NC Euclidean | Excludes zero (+) | Excludes zero (+) | Excludes zero (-) | Excludes zero (+) |
| ElectroSense | Exploratory four-component - primary | Excludes zero (+) | Excludes zero (+) | Excludes zero (-) | Excludes zero (+) |
| DeepSense | Primary - TS entropy | Excludes zero (-) | Excludes zero (-) | Excludes zero (+) | Includes zero |
| DeepSense | Primary - NC cosine | Excludes zero (-) | Excludes zero (-) | Excludes zero (+) | Includes zero |
| DeepSense | Primary - NC Euclidean | Excludes zero (-) | Excludes zero (-) | Excludes zero (+) | Excludes zero (-) |
| DeepSense | Exploratory four-component - primary | Excludes zero (+) | Excludes zero (+) | Excludes zero (+) | Includes zero |
| JamShield | Primary - TS entropy | Excludes zero (+) | Excludes zero (-) | Excludes zero (-) | Excludes zero (+) |
| JamShield | Primary - NC cosine | Excludes zero (+) | Excludes zero (+) | Excludes zero (+) | Includes zero |
| JamShield | Primary - NC Euclidean | Excludes zero (+) | Excludes zero (+) | Excludes zero (-) | Excludes zero (+) |
| JamShield | Exploratory four-component - primary | Excludes zero (+) | Excludes zero (-) | Excludes zero (-) | Excludes zero (+) |

<!-- TRACE: P001, P002, P003, P004, P005, P006, P007, P008, P009, P010, P011, P012 -->

For ElectroSense, all primary-versus-comparator intervals exclude zero in the favorable direction: AUROC, AUPR-OOD, and evaluation-descriptive detection accuracy are higher, while FPR95 is lower. The four-component fusion also has favorable intervals relative to the primary method on this dataset, but that result remains exploratory and cannot be used to relabel the primary analysis.

For DeepSense, the primary fusion is worse than every prespecified comparator on AUROC, AUPR-OOD, and FPR95, and all of those intervals exclude zero. Detection-accuracy intervals include zero against temperature-scaled entropy and cosine distance, whereas the interval against Euclidean distance excludes zero in the negative direction. Adding Mahalanobis distance produces exploratory increases in AUROC and AUPR-OOD whose intervals exclude zero, but it also increases FPR95 with an interval excluding zero; the detection-accuracy interval includes zero. These differences do not repair the fixed-orientation failure.

For JamShield, primary-fusion AUROC is higher than each prespecified comparator and each AUROC interval excludes zero. The other metrics expose a trade-off. Against temperature-scaled entropy, primary AUPR-OOD is lower while FPR95 is lower, with both intervals excluding zero. Against nearest-centroid cosine, primary AUPR-OOD is higher but FPR95 is also higher, with both intervals excluding zero; the detection-accuracy interval includes zero. Against Euclidean distance, the primary method is favorable on all reported metrics and every interval excludes zero. The exploratory Mahalanobis addition increases AUROC and evaluation-descriptive detection accuracy and lowers FPR95, but lowers AUPR-OOD; each of those paired intervals excludes zero. Thus JamShield does not support a claim that fusion uniformly improves every metric against every comparator.

*[Figure 3 about here: `figure_primary_fusion_comparison`. This figure reports AUROC only.]*

### Score distributions and the DeepSense inversion

The dataset-specific score distributions in Figure 4 provide a qualitative view of the fixed orientation. Their score and density axes are independently scaled and must not be compared as common units across datasets. ElectroSense shows useful separation under the primary fusion; JamShield shows partial overlap consistent with its mixed operating metrics; and DeepSense shows a direction mismatch rather than merely broad uncertainty.

DeepSense is retained as a negative fixed-orientation result. Figure 5 compares the original scores with post-hoc negated scores solely to diagnose inversion. The negated scores were not used to choose the primary method, replace any reported value, or make a primary performance claim. The diagnostic suggests that held-out day-two samples can lie closer to training prototypes or receive lower uncertainty than retained day-one test samples under the current representation.

*[Figure 4 about here: `figure_score_distributions_by_dataset`.]*

*[Figure 5 about here: `figure_deepsense_inversion_diagnostic`. POST-HOC DIAGNOSTIC ONLY.]*

### Context across v0-v3

Complete frozen stage-wise v0-v3 results are reported in Supplementary Table S1. The v0 rows cover raw confidence baselines from logistic regression and nearest centroid. The v1 rows cover temperature-scaled logistic-regression entropy and maximum-softmax scores. The v2 rows cover Euclidean, cosine, and Mahalanobis feature distances. The v3 rows contain the prespecified primary fusion and the exploratory four-component ablation. This progression shows that calibration, distance, and fusion alter OOD behavior differently across datasets; it does not define the best method by looking backward at test performance.

*[Supplementary Table S1: complete `paper2_v0_v3_publication_summary.csv`.]*

## Discussion

### Calibration and OOD separation are distinct

Temperature scaling is valuable because it supplies an explicit, validation-fitted calibration baseline without retraining the classifier [@guo2017calibration]. Its objective, however, is ID validation likelihood. It cannot guarantee that unseen classes or domains receive higher entropy than retained ID samples. The DeepSense and JamShield results make this distinction operational: a confidence transformation can be well specified and leak-free while the target shift remains weakly separated. Claims about calibrated confidence should therefore be accompanied by direct OOD and selective-prediction evaluation [@elyaniv2010foundations; @geifman2017selective].

### When uncertainty and geometry complement each other

ElectroSense supports the intended complementarity. The class-novelty protocol lets entropy and prototype distances contribute distinct evidence, and the primary fusion improves the reported comparison metrics relative to each standalone prespecified comparator. This is evidence for the frozen ElectroSense protocol, not proof that the same combination will generalize to every modulation, sensor, or frequency regime.

The standalone temperature-scaled entropy, cosine-distance, and Euclidean-distance methods were prespecified comparators because they are the constituent evidence sources of the primary fusion. Their comparison therefore tests complementarity relative to those components; it does not establish superiority over the complete OOD literature. The v0-v2 results provide contextual baselines but were not retrospectively selected as primary competitors. Adding a new external baseline post hoc merely to improve the paper would conflict with the frozen protocol; broader comparisons should instead be prespecified in future work.

JamShield offers a more qualified result. Fusion improves AUROC against all prespecified comparators, suggesting better global ordering of retained and held-out scenarios. Yet AUPR-OOD and FPR95 move differently depending on the comparator. This is not contradictory: AUROC averages ranking behavior across operating points, AUPR-OOD depends on positive-class retrieval and prevalence, and FPR95 emphasizes a high-recall region. A deployment decision should therefore specify the relevant operating metric rather than treating AUROC as a complete substitute.

### Geometry can invert under domain shift

The DeepSense result is scientifically important because it falsifies the simple assumption that a held-out domain must be farther from training prototypes. Its below-prevalence AUPR-OOD and near-trivial evaluation-descriptive detection accuracy reinforce that fixed-orientation failure rather than providing evidence of a usable operating point. A day shift can move both ID-like and OOD-labeled samples so that the held-out day becomes more concentrated around class centroids than the retained ID test set. Robust validation normalization aligns component scales but cannot correct a direction that reverses after deployment. Reversing the score after seeing OOD labels would produce a useful diagnostic but an invalid primary detector.

A next-step method should be prespecified and validation-identifiable. Candidate directions include two-sided tail scores, validation-fitted density or likelihood-ratio models, and domain-robust representations. Generative-model likelihood inversion and corrective likelihood-ratio scoring illustrate why one-sided scores can fail [@nalisnick2019deep; @ren2019likelihood]. Such methods must be selected without target OOD labels and evaluated on untouched shifts.

### Interpreting the exploratory Mahalanobis component

The exploratory four-component fusion sometimes changes AUROC in a favorable direction, but its effects are not uniform across AUPR-OOD and FPR95. A shared covariance model can emphasize feature directions that help one shift while degrading another operating region. Because this component was not the prespecified primary method, its intervals should motivate a future preregistered comparison rather than retroactively redefine the present claim.

### Statistical scope

Paired intervals exploit exact sample alignment and provide a direct uncertainty estimate for each fixed comparison. Interval exclusion of zero is reported explicitly, but it is not labeled universal statistical significance. The intervals are pointwise, multiple metrics and comparisons are shown, and no family-wise adjustment is applied. The bootstrap also remains conditional on the observed samples; it does not quantify uncertainty over unseen datasets, sensors, or acquisition campaigns.

## Limitations

The evaluation uses a single frozen split for each dataset. This supports reproducibility but limits claims about alternative class partitions, days, sensors, or jammer scenarios. The bootstrap captures sampling variation conditional on those evaluation rows and not the broader uncertainty of future domain shifts.

The title's multi-view framing is realized here as heterogeneous dataset representations and fusion of uncertainty and geometric score views. The current experiment does not train a single model that jointly consumes raw I/Q, PSD, spectrogram, and tabular views for each sample. Each dataset contributes its available processed representation, so cross-dataset performance differences may reflect both protocol difficulty and representation quality.

The supervised uncertainty path is based on a lightweight logistic-regression classifier and probability-derived temperature scaling. The verified publication comparison does not include a logit-energy model, deep ensemble, Monte Carlo dropout model, or learned uncertainty head. The feature-distance methods use the existing processed feature space; Euclidean and cosine scores assume useful class prototypes, and Mahalanobis scoring uses a regularized shared covariance model.

Equal fusion weights and the higher-is-more-OOD direction are fixed. This avoids target leakage but does not establish that equal weighting is optimal. The DeepSense result shows that a fixed one-sided distance assumption can fail under domain shift. The score-negation analysis is post-hoc diagnostic only and cannot be considered evidence for a deployable orientation-selection rule.

Detection accuracy is evaluation-descriptive because its threshold is optimized on the same evaluation sample. It should not be used as a claimed deployment operating point. FPR95 is more directly tied to a stated OOD recall target, but it can still be unstable under shifts in prevalence or score distribution.

The stable-order AUPR-OOD implementation retains input order within score ties. It is applied consistently across every method and bootstrap replicate, but it may differ from grouped-threshold implementations when ties are common. Reproduction and external comparison require preserving or explicitly translating this convention.

Finally, the paired intervals are pointwise and unadjusted for the family of datasets, metrics, and comparisons. An interval excluding zero supports only its listed comparison. The current evidence does not justify universal generalization, universal superiority, or a causal explanation for the observed score geometry.

## Conclusion

This study integrates calibrated predictive uncertainty and train-fitted feature distance into a leak-resistant OOD evaluation pipeline for OpenEW-SA RF artifacts. Validation-only temperature scaling and robust normalization make the procedure reproducible without consulting target OOD labels, and equal-weight fusion provides a simple prespecified test of complementary evidence.

The results are deliberately mixed. The primary fusion is effective for ElectroSense class novelty and improves JamShield AUROC against the prespecified comparators, but JamShield retains metric-specific trade-offs. DeepSense remains a negative result under the fixed orientation, and post-hoc negation is diagnostic only. The central conclusion is therefore not that one fused score solves open-set RF monitoring. It is that closed-set calibration, feature geometry, and OOD operating behavior must be measured separately, combined without target leakage, and interpreted at the level of the actual dataset and shift.

## Reproducibility Statement

All manuscript results are derived from the frozen Paper 2 v0-v3 artifacts and the verified publication-analysis package. The source tables are `tables/paper2_v3_bootstrap_confidence_intervals.csv`, `tables/paper2_v3_paired_differences.csv`, and `tables/paper2_v0_v3_publication_summary.csv`. The independent review report, deterministic bootstrap metadata, validation report, publication figures, and SHA256 manifest are stored in the same package. The local audit path is recorded only in the package README and is intentionally omitted from this submission-facing manuscript.

Repository scripts document manifest construction, split generation, supervised prediction, temperature scaling, entropy extraction, feature-distance scoring, validation-only fusion, metric computation, bootstrap analysis, and publication finalization. The split and score readers preserve `sample_id`, labels, domains, and split identifiers as strings; the publication validator explicitly checks DeepSense leading-zero occupancy labels. All compared methods use exact within-dataset sample alignment and the fixed higher-is-more-OOD orientation.

The prespecified method and analysis roles are named in machine-readable metadata. The primary score is `ts_entropy_cosine_euclidean`; the Mahalanobis-augmented method is exploratory; and the DeepSense negation is post-hoc diagnostic only. Detection accuracy is marked evaluation-descriptive in the generated tables. The numerical traceability matrix maps every empirical value reported in this manuscript to its source CSV row and columns.

This manuscript integration does not rerun model training, OOD score generation, or bootstrap sampling. It reads the verified tables and leaves Paper 1 and all frozen Paper 2 snapshots unchanged. Repository-level validation and remaining editorial tasks are recorded in `manuscript_completion_checklist.md`.

## Figure Captions

**Figure 1. OOD AUROC with bootstrap confidence intervals.** Fixed-orientation point estimates and percentile bootstrap confidence intervals for the prespecified comparators, the prespecified primary fusion, and the exploratory four-component fusion. Higher scores always mean more OOD-like. The dashed line marks chance AUROC. The primary result is not replaced by any score-negated analysis.

**Figure 2. FPR95 with bootstrap confidence intervals.** False-positive rate at the target OOD true-positive rate under the fixed score orientation, with percentile bootstrap confidence intervals. Lower values are preferable, and the full probability range is retained.

**Figure 3. Primary fusion comparison.** This figure reports AUROC only. Paired AUROC differences compare the prespecified primary fusion with each prespecified comparator using identical bootstrap resamples. The shared horizontal label is “Paired AUROC difference: primary - comparator,” and the focused difference scale is centered on zero.

**Figure 4. Primary-score distributions by dataset.** ID and OOD score-density outlines for the prespecified primary fusion. Distribution tails are clipped only for display. Score and density axes are dataset-specific and must not be interpreted as common scales across panels.

**Figure 5. DeepSense distance and fusion score inversion - POST-HOC DIAGNOSTIC.** Fixed-orientation AUROC is compared with AUROC after score negation. Negated values are diagnostic only and were not used to change, replace, or reinterpret the primary result.

## Table Captions

**Table 1. Dataset and OOD protocol summary.** Processed input view, recognition target, frozen OOD definition, and verified ID/OOD evaluation counts for ElectroSense, DeepSense, and JamShield.

**Table 2. Bootstrap confidence intervals.** Fixed-orientation point estimates and percentile 95% confidence intervals for the prespecified primary fusion. The full verified source table also contains all prespecified comparators and the exploratory ablation. Detection accuracy is evaluation-descriptive. <!-- TRACE: N004 -->

**Table 3. Paired method differences.** Left-minus-right interval decisions based on identical resampling indices within each dataset. `CI > 0` means the complete paired interval lies above zero, `CI < 0` means it lies below zero, and `0 in CI` means it contains zero. For FPR95, smaller values are favorable. These entries are interval-location summaries, not significance tests. Exact point differences and bounds are retained in the verified paired-differences CSV. The comparator set was fixed independently of test performance, and detection accuracy is evaluation-descriptive.

**Supplementary Table S1. v0-v3 publication summary.** Complete frozen stage-wise OOD results for raw confidence baselines, temperature-scaled confidence, feature distances, and uncertainty-distance fusion. The three-component v3 method is the prespecified primary analysis; the Mahalanobis four-component method is exploratory.

## References

Citation keys in this Markdown source resolve to the independently verified records in `reference_verification/references_verified.bib`. The IEEE manuscript renders the same verified metadata through `ieee_latex/references.bib` using the IEEEtran bibliography style. The bootstrap citations are methodological underpinnings rather than prescriptions of the exact analysis design, and the ElectroSense taxonomy claim is explicitly bounded to the verified converted subset.
