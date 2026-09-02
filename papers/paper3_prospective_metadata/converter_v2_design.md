# OpenEW-SA metadata converter v2 design

Converter v2 is a new, opt-in pipeline. It does not replace Paper 1/Paper 2
converters or rewrite current processed artifacts.

## Pipeline

| Stage | Input | Output | Gate |
|---|---|---|---|
| source registration | raw files plus official documentation | immutable source manifest and SHA-256 | source/licence review |
| acquisition extraction | raw headers, acquisition logs, capture sidecars | target-free acquisition rows | schema + provenance validation |
| annotation extraction | separate label/adjudication sources | long-form annotation rows | task-definition review |
| provenance sidecar | field extraction trace | `metadata_provenance.json` | populated-field completeness |
| safety audit | acquisition + separately loaded annotations | aggregate proxy/missingness report | conservative eligibility classification |
| artifact freeze | validated tables + raw hash links | versioned manifest | no mutable source references |
| split construction | capture/session/campaign-safe identifiers | train/validation/test manifests | no session/capture overlap |
| model access | features + whitelisted acquisition fields | partition-local relation structures | annotations absent from structure API |

## Parser requirements

Each parser writes its name/version, source hash, extracted fields, extraction
method, official verification source, confidence, transformation history,
warnings, and unresolved tokens. It rejects rather than guesses ambiguous
filename tokens, random binary offsets, or filesystem mtime.

No retrospective parser prototype is supplied in this workstream because the
raw-source audit recovered no new experiment-enabling field. Future parsers
must write only to a new versioned output root and never overwrite existing
OpenEW-SA artifacts.

## Freeze boundaries

Field eligibility, target-proxy thresholds, relation whitelists, split families,
episode semantics, and temporal readiness are frozen before target evaluation.
Target performance cannot repair metadata validity.
