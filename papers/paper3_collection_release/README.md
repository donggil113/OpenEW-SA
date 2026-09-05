# Receiver collection and external-replication readiness

**Software-only readiness. No SDR hardware, physical clock, real acquired episode or new RF dataset was validated. No training is authorized by this toolkit.**

The runtime registers completed files produced by a hardware-specific SDR capture program. It does not transmit RF, configure radios, acquire live I/Q or claim hardware independence has been physically tested. Linux/POSIX and WSL are the tested runtime platforms; native Windows flock/fsync support is not claimed.

Entry points:

- scripts/paper3/collection_runtime/paper3-collect
- scripts/paper3/collection_runtime/qualify-shen-payload
- scripts/paper3/collection_runtime/collection_release_tools.py

See real_collection_operator_runbook.md, capture_adapter_contract.md, recovery_and_atomicity.md, collection_tiers.md and the one-page printable checklist. For Shen, read shen_data_access_request.md (UNSENT), licence questions and payload_receipt_runbook.md.

Every synthetic fixture and validation output is SYNTHETIC, not scientific evidence. Template metadata is not a verified receiver/site record. Before real use, select physical hardware, lawful RF operating conditions, a clock authority, storage/backup plan and collection supervisor. A supervised on-device dry run is mandatory.
