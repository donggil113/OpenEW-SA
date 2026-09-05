# Paper 3 internal-review manuscript v0

**Decision: READY_FOR_INTERNAL_REVIEW, not submission ready. Publication gate remains CONDITIONAL.**

Recommended title: **Receiver Adaptation for RF Fingerprinting Under Unseen-Receiver Shift**.

This package consolidates PR #85–#88 evidence without new model runs. It does not alter their decisions. T3A is the strongest evaluated deployable same-information method on the six-class WiSig protocol. P2 is neutral relative to P0; no P2 rescue is proposed. External validity and physically acquired calibration episodes remain unresolved.

## Review route

1. Read the IEEE main manuscript and supplementary lookup (build instructions in ieee_latex/README.md).
2. Check claim_evidence_ledger.md and numerical_traceability_matrix.md.
3. Read novelty_boundary.md, internal_reviewer_risk_register.md and submission_readiness_v0.md.
4. Inspect the independent operator toolkit in ../paper3_collection_release/.
5. Use reproducibility_audit.md for the exact validation scope.

The evidence directory contains small aggregate/receiver-seed tables and provenance, not RF payload, packet predictions, checkpoints or packet annotations. Output PDFs/PNGs and validation logs remain external under /mnt/d/openew_sa_data/paper3/manuscript_v1/. The committed vector figure assets are generated from these small evidence exports.

## Rebuild without RF data

From repository root, with the documented Python environment and PYTHONPATH=src:

    python scripts/paper3/collection_runtime/render_manuscript_assets.py --manuscript papers/paper3_receiver_adaptation_manuscript --output /tmp/paper3-figures
    papers/paper3_receiver_adaptation_manuscript/ieee_latex/build.sh /tmp/paper3-pdf

Do not rerun the frozen benchmark to rebuild the manuscript. The source-evidence exporter and full frozen-source audit require the original external artifacts; the renderer, tests and synthetic toolkit do not.
