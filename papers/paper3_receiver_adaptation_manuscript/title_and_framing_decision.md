# Title and scientific framing

| Candidate | Strength | Risk | Decision |
|---|---|---|---|
| A. Receiver Adaptation for RF Fingerprinting Under Unseen-Receiver Shift | Direct, neutral about method superiority | Must specify dataset scope in abstract | RECOMMENDED |
| B. Unlabeled Receiver Adaptation for RF Fingerprinting Under Receiver Shift | Explicit target information | Omits supervised oracle's diagnostic role; less clear physical receiver unit | Acceptable alternative |
| C. Receiver Calibration for RF Fingerprinting: A Benchmark of Source Generalization, Test-Time Adaptation, and Context Conditioning | Describes information regimes | “Calibration” can imply physically acquired sessions or instrument calibration | Do not lead with this |
| D. Test-Time Receiver Adaptation for RF Fingerprinting: What Works Under Unseen Receiver Shift? | Question-driven benchmark | Broad “what works” can imply comprehensive method coverage | Too expansive without qualification |

Question: among the frozen source-only, unlabeled-support and context-conditioning procedures, which most reliably improves recognition on unseen physical WiSig receivers under explicit information budgets?

The answer concerns the evaluated methods, six classes, deterministic support banks and one dataset. T3A is an existing algorithm. The contribution, if reviewers accept it, is the systematic comparison, receiver-level accounting, transparent negative context result and reproducible information-access protocol—not architecture novelty.
