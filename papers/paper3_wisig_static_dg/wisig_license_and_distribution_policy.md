# WiSig licence and distribution policy

## Authorization and source

Local, noncommercial research processing of the official WiSig ManyRx compact dataset is authorized by the user under CC BY-NC-SA 4.0. The official release page is `https://cores.ee.ucla.edu/downloads/datasets/wisig/`; the required WiSig paper citation is DOI `10.1109/ACCESS.2022.3154790`.

This authorization does not remove attribution, NonCommercial, or ShareAlike obligations and does not authorize original or derived RF payload redistribution. It does not authorize use of unofficial mirrors or bypassing access controls.

## Artifact policy

| Artifact | Policy | Rationale |
|---|---|---|
| Official ManyRx ZIP and extracted pickle | **EXTERNAL ONLY** | Copyrighted RF payload; never committed or uploaded to GitHub. |
| Converted RF tensors or feature shards | **EXTERNAL ONLY** | Signal-derived payload remains subject to licence review and ShareAlike obligations. |
| Exact original paths and filenames | **RESTRICTED AUDIT-ONLY, EXTERNAL** | Official names may reveal the transmitter target. |
| Source-to-opaque-ID mapping | **RESTRICTED AUDIT-ONLY, EXTERNAL** | Contains target-bearing provenance inputs. |
| Acquisition metadata with opaque sample IDs | **REVIEW BEFORE DISTRIBUTION** | It must first pass target-path and proxy audits. |
| Annotation table | **EXTERNAL ONLY BY DEFAULT** | Although small, it is derived from the licensed payload and exposes target identity. |
| Opaque aggregate manifests, hashes, and counts | **REVIEW BEFORE DISTRIBUTION** | Commit only when they contain no payload, exact target-bearing paths, or reversible identifiers. |
| Split definitions by opaque IDs/hashes | **COMMIT ALLOWED AFTER REVIEW** | Required for reproducibility, provided no target-bearing source names are present. |
| Source code, tests, configs, protocol, aggregate reports | **COMMIT ALLOWED** | No RF payload or copyrighted archive content. |

## Operational controls

- Store payload only below `/mnt/d/openew_sa_data/paper3/wisig/`.
- Never log exact target-bearing source paths in model manifests, prediction outputs, Git diffs, or exception messages intended for publication.
- Record source URL, resolved official endpoint, retrieval time, exact bytes, SHA-256, and archive safety manifest externally.
- Preserve the original archive and extraction immutably; derived passes use new directories and atomic writes.
- If institutional policy later imposes an additional approval, stop payload processing, record `LICENSE_GATE_BLOCKED`, and continue only code/documentation work.
