# OpenEW-SA Paper 3 Feasibility Phase

This directory contains the leakage-safe relational metadata feasibility audit for the proposed Paper 3. It does **not** contain a trained graph or hypergraph model.

Run the deterministic audit from the repository root:

```bash
PYTHONPATH=src /home/user/venvs/openew-sa/bin/python \
  scripts/paper3/audit_relational_metadata.py
```

Generated aggregate CSVs are written outside Git under `/mnt/d/openew_sa_data/paper3/audits/`. The source processed artifacts are opened read-only, the feature arrays are memory-mapped only to verify shape, and no raw sample-level data are copied into this paper directory.

Start with:

- `artifact_inventory.md` for inspected sources and schemas;
- `leakage_policy.md` for the enforceable field policy;
- `feasibility_report.md` for the GO/NO-GO decision; and
- `audit_handoff.md` for the final handoff.
