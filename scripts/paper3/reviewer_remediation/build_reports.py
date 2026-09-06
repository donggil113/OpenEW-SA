"""Generate bounded human-readable handoff from immutable numerical evidence."""
import argparse,json
from pathlib import Path
import pandas as pd
from openew.paper3.reviewer_remediation.contracts import file_sha
p=argparse.ArgumentParser();p.add_argument("--output-root",type=Path,required=True);p.add_argument("--repository",type=Path,default=Path.cwd());a=p.parse_args()
repo=a.repository;doc=repo/"papers/paper3_reviewer_remediation";e=doc/"evidence";root=a.output_root
s=pd.read_csv(e/"primary_summary.csv");raw=s[s.probability_variant=="raw"].set_index("method")
inf=json.loads((e/"receiver_inference.json").read_text());prior=json.loads((e/"prior_receiver_inference.json").read_text())
lineage=json.loads((e/"source_manifest.json").read_text())
def write(name,text): (doc/name).write_text(text.strip()+"\n")
def f(m,k="macro_f1",v="raw"):return f'{s[(s.method==m)&(s.probability_variant==v)].iloc[0][k]:.6f}'
write("reviewer_remediation_handoff.md",f"""
# Reviewer-remediation handoff
## VERIFIED RESULT
POST-HOC BASELINE-COMPLETENESS ADDENDUM, not independent confirmation.
Preregistration commit f30b658ff40f4d8ec3770be4c7c2b4692e5814da; scientific execution commit 028e4c770d65f25d8f85c913a267ad75788c0ba2.
Unblinding: {json.loads((root/'unblinding_manifest.json').read_text())['utc']}; create-once.
All 2,400 records COMPLETE, zero failed: 480 reference-budget and 1,920 common-query budget records. No source model was retrained from scratch; frozen P0/P2 checkpoints were reused. Source-only oracle recipe simulation is separate from target evaluations. No P2 tuning, split replacement, receiver/seed deletion or RF download occurred.

| Method | Receiver-equal macro-F1 | Status |
|---|---:|---|
| P0 | {f('P0')} | Frozen R0 |
| T3A | {f('T3A')} | Frozen R1 |
| P2 | {f('P2')} | Frozen R1 |
| SAR-GN | {f('SAR_GN')} | New bounded-support GN application |
| EMB-STD | {f('EMB_STD')} | New simple source-aligned moment control |
| Head FT | {f('SUP_FT_HEAD_128')} | Frozen labeled diagnostic |
| Full FT | {f('SUP_FT_FULL_128')} | New labeled diagnostic |

T3A remains the highest-mean unlabeled reference-budget method. SOURCE-NORM is the highest-mean source-only entry ({f('SOURCE_NORM')}); differences among source-only leaders are small and not a new inferential claim. EMB-STD improves all 32 receiver averages versus P0, mean delta {inf['EMB_STD_MINUS_P0']['bootstrap']['mean_difference']:.6f}, interval [{inf['EMB_STD_MINUS_P0']['bootstrap']['ci95_lower']:.6f}, {inf['EMB_STD_MINUS_P0']['bootstrap']['ci95_upper']:.6f}].
EMB-STD minus T3A is {inf['EMB_STD_MINUS_T3A']['bootstrap']['mean_difference']:.6f}; its narrow bootstrap interval excluding zero and exploratory sign-flip p={inf['EMB_STD_MINUS_T3A']['sign_flip']['p_value']:.6f} are both retained. Do not select one to manufacture significance.

SAR is effectively P0: three positive, four negative, 25 equal receiver means. Its reference-budget execution has two steps, four SAM backward passes and average 1.83125 source recoveries; no empty reliable subset occurred. This qualifies the short-support application, not all SAR settings. SHOT is excluded for incompatible official source-training contract. Shen-GRL bridge is NO-GO, with no payload download.

## Probability quality
Raw T3A has ECE {f('T3A','ece')}, NLL {f('T3A','nll')}, Brier {f('T3A','brier')}, mean confidence {f('T3A','mean_confidence')} and confidence-minus-accuracy {f('T3A','confidence_accuracy_gap')}. Average underconfidence, not overconfidence, is the correct direction. ECE alone understated its better proper scores. Source-only temperature ECE is {f('T3A','ece','source_temperature')}, NLL {f('T3A','nll','source_temperature')}, Brier {f('T3A','brier','source_temperature')}. Argmax decisions are unchanged.

## INTERPRETATION
A simple feature-statistics control explains substantial available improvement, but it is not established as the causal explanation for every adaptation method. A much stronger labeled diagnostic invalidates the old near-ceiling wording. No new baseline rescues P2. Small support is a meaningful limitation for T3A; no budget is selected after results.

## Reproducibility and manuscript
New analysis package SHA256: {lineage['analysis_sha256']}. The portable evidence manifest maps every exported file to this immutable package. Thirty-one verified references, shared-source TMLCN/Access builds, all-receiver raw/scaled reliability and a payload-absent reproduction command are included. Official Access template dependencies remain external.
Timing-only replay covered all 32 receivers, seed 829, three repetitions for six methods; 576 records matched frozen probabilities. These are not new accuracy runs.

## UNRESOLVED
Single dataset, six-class task, constructed support rather than acquired episodes, overlapping LOSO source training, three hardware families, broader representation-changing baseline coverage, external data/license access, physical SDR validation, author/venue metadata and derivative release review remain open. Publication readiness remains CONDITIONAL.
""")
write("probability_calibration_report.md",f"""
# Probability-quality interpretation
VERIFIED RESULT: receiver-equal scalar metrics come from evidence/primary_summary.csv, five seeds averaged inside each receiver. Detailed adaptive ECE, NLL, multiclass Brier (sum, not class average), entropy and confidence gap are preserved.
Raw T3A mean confidence {f('T3A','mean_confidence')} is below mean correctness {f('T3A','accuracy')}; its gap is {f('T3A','confidence_accuracy_gap')}. Thus average underconfidence is supported directly. The reliability curve also shows shape deviations, so the evidence does not prove a pure scalar-temperature generative explanation.
T3A ECE {f('T3A','ece')} exceeds P0 {f('P0','ece')}, whereas NLL {f('T3A','nll')} and Brier {f('T3A','brier')} are lower than P0 ({f('P0','nll')}, {f('P0','brier')}). Calling this simply degraded calibration is misleading.
Source-validation-only temperatures reduce T3A ECE to {f('T3A','ece','source_temperature')}; residual nonzero error remains. No target-label temperature fit or post-fit classification replacement occurred.
Equal-width reliability bins use 15 common bins, including explicit sample mass. Adaptive ECE uses 15 equal-count top-label groups with stable confidence ordering, not a claim to reproduce every published ACE definition. Empty bins are omitted, not assigned zero correctness.
All 32 receiver panels, raw and source-temperature, are provided. Aggregate bin curves pool repeated seed predictions descriptively; they are never used for packet-level inference. All newly recomputed probability diagnostics are POST-HOC.
""")
write("compute_latency_report.md","""
# Compute fairness
See evidence/timing_summary.csv and execution_cost_summary.csv. Every timing replay used the same RTX4090, resident converted data, seed829, all32 receivers and3 repetitions. Six methods produced576 timing-only records. Frozen probabilities matched; no new accuracy measurements replaced prior results.
Cross-method throughput MUST use total_samples_per_second=query_count/total_seconds. The raw samples_per_second diagnostic has different scopes in reused helpers (prediction-only for new adapters, total for old methods); it is not the comparison column.
SAR updates672 GN-affine parameters; full FT updates64774; EMB/T3A/P2 do not update weights at inference. SAR has4 backward passes at reference budget. P0/P2 parameter totals64774/75143 are frozen.
P2 total includes CPU hash-based context assembly and support/query encodings. Prototype construction and query scoring are not isolated for T3A; absent sub-timers are not zero cost. EMB support encoding is isolated; source-moment estimation is an additional offline pass over source training embeddings, not target cost. New full-network oracle cost is not a deployable comparison.
GPU peak includes resident models, not just incremental adapter allocation. Checkpoint loading, raw data conversion and prior source training are excluded from test-time totals. Operation-count/FLOP precision is unresolved; measured backward-pass count and parameter updates are reported instead of fabricated FLOPs. These measurements do not establish device-independent latency or asymptotic efficiency.
""")
write("submission_readiness_v1.md","""
# Submission readiness v1
**CONDITIONAL**, not READY_FOR_SUBMISSION or merely READY_AFTER_HUMAN_METADATA.

Baseline completeness improved: GN-compatible gradient adaptation was implemented and fidelity checked; a source-aligned embedding control is strong; full-network labeled adaptation exposes real headroom. SHOT and Shen exclusions remain substantive compatibility limits, not completed replications. Post-hoc timing remains visible.

Probability-quality wording is corrected; all new inferential p-values remain exploratory. No novel architecture, P2 superiority, external generality or acquired calibration realism is claimed.

Remaining scientific blockers: one WiSig task, six-class subset, constructed support/query separation, limited hardware families and overlapping source training. External validation and actual acquisition episodes are still absent. Whether a carefully bounded single-dataset benchmark is publishable requires human and venue judgment.

Remaining release/administrative blockers: authors/affiliations/ORCIDs, correspondence, funding/conflicts, related Paper1/2 overlap review, institutional derivative-release/license approval, final reference/retraction check, AI disclosure approval and venue choice. No manuscript or cover letter has been sent.

Maximum defensible claim: on this fixed WiSig receiver-LOSO task, T3A is the highest-mean evaluated unlabeled method at support128; EMB-STD is a strong post-hoc control; P2 and the tested short-support SAR application remain near P0; labeled full-network adaptation leaves substantial headroom. Probability scores must be interpreted separately from classification.
""")
write("claim_evidence_ledger.md","""
# Claim ledger and terminology audit
| ID | Claim | Evidence | Allowed wording | Prohibited wording |
|---|---|---|---|---|
| C01 | T3A has highest mean at128 | primary_summary; frozen reference | highest mean among evaluated unlabeled entries | universal/SOTA winner |
| C02 | EMB-STD improvesP0 | receiver_inference; POST-HOC | all32 receiver averages improve | independently confirmed new algorithm |
| C03 | P2 remains neutral | frozen V2 | no meaningful advantage overP0 here | rescued/superior P2 |
| C04 | SAR result is nearP0 | new grid/costs; POST-HOC | tested bounded-support recipe changes little | gradient TTA never works |
| C05 | Full FT exposes headroom | labeled oracle; POST-HOC | stronger empirical diagnostic | proven upper bound/deployable method |
| C06 | T3A average underconfidence | confidence gap/reliability | average underconfidence with shape residuals | ECE proves overconfidence |
| C07 | Source temperature helps | source_temperatures/probability rows | improved aggregate probability metrics | target-calibrated classifier |
| C08 | Support efficiency varies | complete common-query curves | no best-budget selection | target-optimized support size |
| C09 | Receiver statistics | fixed inference | conditional receiver-level interval | independent packets or hardware families |
| C10 | External readiness | Shen audit | software/source analysis only | external replication result |
| C11 | Runtime durability | synthetic stress | generated transitions and POSIX fault tests | physical SDR validation |
| C12 | Reproducibility | public command/hash audits | same-environment fresh checkout | independent platform replication |
| C13 | Publication | readiness report | conditional internal-review manuscript | submission-ready because it builds |
| C14 | Manuscript title | bounded task | receiver adaptation | acquired calibration/temporal reasoning |
All numerical manuscript macros are generated from evidence. Claims labeled INTERPRETATION are not extra measurements. FUTURE WORK requires lawful external data or independent physical collection. LIMITATIONS stay in abstract, discussion and conclusion.
""")
write("structural_numerical_traceability.md","""
# Structural and protocol numerical lineage
The numeric result matrix covers generated estimates. Structural numbers in prose map here rather than being mistaken for measured effects.

| Numbers | Source/key | Status |
|---|---|---|
|32 receivers;5 seeds;128 support;32 peers|protocol.json; preserved V2 split/source code|FROZEN DESIGN|
|28 train;3 validation;1 test|split summaries checked in preflight|FROZEN DESIGN|
|249666;10tx;4days;256complexIQ;6eligibleclasses|PR89 evidence; converted manifest/class mapping|PRIOR DATA FACT|
|2462MHz;20MHz;25MS/s|prior verified WiSig metadata|PRIOR DATA FACT|
|480primary;1920budget;2400complete;0failed|execution grid and analysis_validation|VERIFIED EXECUTION|
|15 bins;1e-12;0.05..20|calibration.py and preregistration|FROZEN ANALYSIS|
|1e-6 moment floor;float64/32|methods.py|FROZEN METHOD|
|SAR64batch;0.05rho;0.9momentum/EMA;0.2reset;0.4logC;0.00025LR|official SAR audit plus methods.py|FROZEN APPLICATION|
|6oracle recipes;5/20steps;three LR values|methods.py ORACLE_GRID|SOURCE-ONLY SELECTION|
|10000bootstrap;100000sign flips;20260906RNG|analysis.py;receiver_inference.json|POST-HOC INFERENCE|
|0.05catastrophic threshold;22P2 seed failures;1full-FT seed failure|preregistration;catastrophic_adaptation.csv|FROZEN RULE/OBSERVED COUNT|
|3hardware families|PR89 hardware source audit|DESCRIPTIVE ONLY|
|31references;14figures;8tables|reference/figure/build audits|ARTIFACT COUNTS|
|25000transitions;24durable faults+1corrupt case;6process exits|collection_stress.json|SYNTHETIC ONLY|
No manual result number is a substitute for its row/key and analysis Git/hash.
""")
# Preserve the original36 risks while recording only defensible remediation.
lines=(repo/"papers/paper3_receiver_adaptation_manuscript/internal_reviewer_risk_register.md").read_text().splitlines()
rows=["# Independent-audit response matrix","",
"Reviewer concerns are taken from the visible user audit and PR89 risk register. This is an internal response, not a claim that an external reviewer approved the revision.","",
"| ID | Reviewer concern | Status/action | New evidence | Remaining limitation | Manuscript location |","|---|---|---|---|---|---|"]
improvements={"R19":("PARTIALLY ADDRESSED: SAR-GN audited and run","SAR fidelity +2400 grid","Tent/AdaBN original BN contract still absent","IV.B"),
"R20":("ADDRESSED wording/metrics","NLL/Brier/adaptiveECE/gap/source temperatures","Residual shape/receiver calibration error","V.D"),
"R21":("ADDRESSED weak-ceiling interpretation","Full-network labeled diagnostic","Not a mathematical upper bound","IV.D,V.B"),
"R25":("PARTIALLY ADDRESSED measurement scope","576 timing-only replays","One seed; CPU assembly; missing isolated prototype timer","V.E"),
"R27":("SOFTWARE ONLY expanded","25000 generated transitions;25 durable fault cases","No real hardware power-cut test","Supplement"),
"R23":("MITIGATED","Generated numerical macros,322 result/key rows","Human review still required","All"),
"R24":("MITIGATED","Raw/conversion/prediction/analysis SHA checks","Checksums are not external signatures","VII"),
"R08":("EXCLUDED transparently","Shen representation bridge NO-GO","No faithful Shen RF baseline result","II.A")}
for line in lines:
 if not line.startswith("| R"):continue
 parts=[x.strip() for x in line.split("|")[1:-1]];ident,reviewer,risk,consequence,action,status=parts
 if ident in improvements:st,ev,lim,loc=improvements[ident]
 else:st=status+": "+action;ev="Prior evidence retained; no fabricated new dataset";lim=consequence;loc="VII / Supplement"
 rows.append("| "+" | ".join([ident,risk,st,ev,lim,loc])+" |")
for ident,concern,action,lim,loc in [
("N01","Prototype diversity","SHOT official source pipeline audited, excluded","Not a second faithful prototype algorithm result","II.B"),
("N02","Simple embedding correction","EMB-STD source-aligned control implemented","Post-hoc and not novel","IV.C,V.A"),
("N03","Dual use of calibration","Receiver adaptation and probability calibration separated","No acquired episodes","III,V.D"),
("N04","Venue/release portability","Two shared-source layouts and public command","Human metadata/license gates remain","Availability"),
("N05","SAR edge-case fidelity","Official noncollapse equivalence and explicit recovery fixes","Not universal implementation equivalence","IV.B")]:
 rows.append("| "+" | ".join([ident,concern,action,"New documented audit",lim,loc])+" |")
write("claude_overnight_audit_response_matrix.md","\n".join(rows))
print("REPORTS_GENERATED_FROM_FROZEN_EVIDENCE")
