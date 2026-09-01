# Paper 3 prospective acquisition-context infrastructure

This package follows the frozen PR #81 static-relational NO-GO result. It does
not rerun or optimize M0–M2. It supplies a target-free acquisition schema,
field-level provenance, conservative eligibility engine, read-only forensic
audits, prospective QA, structural readiness scorecard, and collection/split
protocols for a genuinely new dataset.

## Key decisions

- Current JamShield, DeepSense, and ElectroSense artifacts do not authorize a
  new relational experiment.
- No valid temporal context was recovered retrospectively.
- The software infrastructure can represent static, temporal, and dynamic
  structures, but scientific eligibility requires newly collected metadata.
- Acquisition metadata and task annotations are separate objects.
- Unknown relation fields fail closed and every experiment freezes an explicit
  whitelist.

## Commands

Run from the repository root with the OpenEW-SA environment:

```bash
PYTHONPATH=src python scripts/paper3/metadata/inventory_sources.py
PYTHONPATH=src python scripts/paper3/metadata/inspect_raw_metadata.py
PYTHONPATH=src python scripts/paper3/metadata/audit_metadata_proxies.py
PYTHONPATH=src python scripts/paper3/metadata/inventory_local_candidates.py
PYTHONPATH=src python -m unittest discover -s tests/paper3/metadata -v
```

Validate the synthetic software-contract fixture:

```bash
PYTHONPATH=src python scripts/paper3/metadata/validate_prospective_metadata.py \
  --acquisition tests/paper3/metadata/fixtures/acquisition_metadata.json \
  --annotations tests/paper3/metadata/fixtures/annotations.json \
  --provenance tests/paper3/metadata/fixtures/metadata_provenance.json \
  --relation-field receiver_id --relation-field site_id \
  --relation-whitelist receiver_id --relation-whitelist site_id \
  --verified-relation-field receiver_id --verified-relation-field site_id \
  --temporal-verdict VALID_TEMPORAL_CONTEXT \
  --mixed-target-episode-fraction 1.0 \
  --output /mnt/d/openew_sa_data/paper3/prospective_validation/metadata_readiness_scorecard.json
```

The fixture proves API behavior only. It is not a scientific dataset and has no
model-accuracy result.

Generated audit outputs are intentionally external under
`/mnt/d/openew_sa_data/paper3/`; raw or sample-level data are not committed.

