# Paper 3 Public Dataset Qualification

This workstream qualifies public RF datasets before any new model experiment. It preserves the PR #81 static-relational NO-GO and applies the frozen PR #82 metadata readiness contract.

## Reproduce the machine-readable WiSig decision

```bash
source /home/user/venvs/openew-sa/bin/activate
cd /home/user/src/openew-sa
PYTHONPATH=src python scripts/paper3/dataset_qualification/qualify_candidate_dataset.py \
  --config configs/paper3/dataset_qualification/wisig_candidate_v1.yaml \
  --output /mnt/d/openew_sa_data/paper3/dataset_qualification/wisig_qualification_report.json \
  --free-bytes "$(df -B1 --output=avail /mnt/d | tail -1)"
```

The evaluator uses no model metrics. It checks official evidence, payload licence, download/storage policy, target-proxy fields, temporal evidence, and the unchanged PR #82 metadata thresholds. Unknown facts fail closed.

## External outputs

- `/mnt/d/openew_sa_data/paper3/candidate_metadata/wisig/metadata_manifest.json`
- `/mnt/d/openew_sa_data/paper3/candidate_metadata/wisig/official_metadata_summary.json`
- `/mnt/d/openew_sa_data/paper3/dataset_qualification/wisig_metadata_index_proxy_audit.csv`
- `/mnt/d/openew_sa_data/paper3/dataset_qualification/wisig_qualification_report.json`
- `/mnt/d/openew_sa_data/paper3/dataset_qualification/external_candidate_matrix.csv`

No downloaded RF payload, raw archive, prediction, checkpoint, or model result is committed.

## Safety boundary

Transmitter/class/label/OOD/prediction/correctness fields and target-bearing paths are rejected. Filesystem mtime is never accepted as acquisition time. Dataset-code licences do not establish dataset-payload rights. A public download link is not sufficient for adoption.
