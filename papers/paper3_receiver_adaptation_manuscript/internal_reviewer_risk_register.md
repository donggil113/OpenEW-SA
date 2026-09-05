# Internal reviewer risk register

This is an adversarial internal pass, not external peer review. Publication remains conditional.

| ID | Reviewer | Risk | Consequence | Action / limit | Status |
|---|---|---|---|---|---|
| R01 | RF | Single WiSig dataset | External receiver generality is unsupported | Independent lawful/prospective replication | OPEN |
| R02 | RF | Six-class support-qualified subset | May simplify transmitter discrimination | Disclose subset and freeze; no post-hoc expansion | OPEN |
| R03 | RF | Constructed support banks | Not acquired calibration episodes | Acquire separate mixed-activity sessions | OPEN |
| R04 | RF | Three hardware families | Few families cannot support population inference | Descriptive only; diversify future hardware | OPEN |
| R05 | RF | Shared capture/testbed design | Receivers may share environmental dependencies | Document testbed; independent campaigns | OPEN |
| R06 | RF | 256-IQ representation | May not transfer LoRa fingerprint semantics | Frozen Shen C2 remains software candidate | OPEN |
| R07 | RF | Shen licence conflict | No external data result permissible | Written lawful terms and payload provenance | BLOCKED |
| R08 | RF | Missing faithful RF baseline | DANN is not Shen-GRL | Explicit exclusion; do not relabel approximation | OPEN |
| R09 | RF | Packet independence | Adjacent packets share acquisition factors | Receiver-level statistics, no packet bootstrap | MITIGATED |
| R10 | RF | Receiver identity aliases | Registry software cannot prove physical units | Serial/hardware inventory verification | OPEN |
| R11 | ML | T3A comparison timing | Earlier outcomes known before later family | Disclose dependent evidence | OPEN |
| R12 | ML | Overlapping LOSO training | Receiver deltas not fully independent draws | Conditional interval interpretation | OPEN |
| R13 | ML | No pure-DG claim for P2 | Unlabeled target information changes regime | Explicit R0/R1/R2 table | MITIGATED |
| R14 | ML | Pseudo-label failure at small support | T3A can harm recognition | Full grid; no best-budget selection | MITIGATED |
| R15 | ML | P2 neutral result | Architecture novelty unsupported | Preserve negative conclusion | MITIGATED |
| R16 | ML | Attention not causal | Weights/context sensitivity do not identify mechanism | No causal language | MITIGATED |
| R17 | ML | Donor-domain confound | Shuffled/mismatched donors from source validation | Explicit method caveat | OPEN |
| R18 | ML | Oracle composition leakage | Label-dependent stress can inflate/alter results | Non-deployable supplementary labeling | MITIGATED |
| R19 | ML | Tent/AdaBN coverage | GroupNorm prevents faithful original adaptation | No retrofit; limitation disclosed | OPEN |
| R20 | ML | Calibration metric disagreement | Accuracy/ECE/NLL move differently | Report all, no target temperature tuning | MITIGATED |
| R21 | ML | Supervised oracle ceiling wording | One head-update procedure is not upper bound | Empirical comparator only | MITIGATED |
| R22 | ML | Multiple study stages | Selective narrative could hide attenuation | Evidence progression and prior results retained | MITIGATED |
| R23 | Repro | Numerical transcription | Rounded/manual errors change claims | Generated macros plus row/hash trace | MITIGATED |
| R24 | Repro | External source drift | Frozen outputs might change silently | Manifest and checkpoint/prediction reconciliation | MITIGATED |
| R25 | Repro | Incomplete timing boundaries | Record time is not deployment latency | Scope-separated tables, missingness explicit | OPEN |
| R26 | Repro | Native platform portability | flock/directory fsync are POSIX-specific | Linux/WSL contract; native Windows not claimed | OPEN |
| R27 | Repro | Real power-loss durability | Fault injection cannot certify controller caches | On-device power test before collection | OPEN |
| R28 | Repro | Clock authority attestation | UTC strings do not prove synchronization | Record authority; hardware verification | OPEN |
| R29 | Repro | Journal growth | Full-state transaction snapshots scale quadratically | Bounded campaign size and field profiling | OPEN |
| R30 | Repro | Partial/orphan evidence | Automatic promotion could contaminate collection | Quarantine/review; never promote | MITIGATED |
| R31 | Repro | Licence derivatives | Small summaries are not automatic legal clearance | Institutional review before wider release | OPEN |
| R32 | Repro | Synthetic fixtures | Passing mock tests is not data readiness | Scientific authorization stays false | MITIGATED |
| R33 | Repro | Authorship/venue placeholders | PDF completion not submission completion | Human authorship and venue approval | OPEN |
| R34 | Repro | Environment reuse | Fresh clone on same environment is not independent platform | State scope; future clean-machine validation | OPEN |
| R35 | Repro | Source schema provenance | A matching HDF5 shape does not prove official data | Human receipt/source/version evidence gate | OPEN |
| R36 | Repro | Malicious local state edits | Checksums without external signature are not tamperproof | Separate read-only backup of freeze manifests | OPEN |

Top priorities: R01, R02, R03, R04, R08, R11, R12, R17, R19 and R27. None warrants tuning P2 on the known WiSig targets.
