# Collection runtime validation handoff

**READY SOFTWARE ONLY for supervised integration/dry-run review. NOT HARDWARE VALIDATED.**

Delivered commands: campaign-init, receiver-register, session-open, capture-register, session-close, campaign-close, validate, freeze-day, status, recover; separate annotation-qa. Metadata CSV/Parquet export, cross-campaign tier QA and storage estimator are available through collection_release_tools.py.

Validation: 356 new tests including manuscript checks (337 runtime/adapter/release tests), 10,000 deterministic generated contract cases, 2,036 full-stress durable transitions, and a separate 150-transition SMALL-tier synthetic campaign. No scientific RF accuracy was measured. A real process exit plus injected write failures exercise recovery; partial/orphan evidence never becomes valid automatically.

Measured on the recorded WSL /mnt/d environment:
- Full stress: 269.880 seconds; 380.623 MiB/s SHA256 on a 32-MiB synthetic probe.
- Small atomic JSON mean: 6.814 ms.
- SMALL-tier 32-row site export: CSV 15.921 ms; Parquet 32.339 ms.
- SMALL-tier site validation: 0.924 s; recovery/status validation: 0.502 s.

These timings include this filesystem/cache/load, not live SDR overhead or guaranteed real-disk throughput. Full-state journal growth is quadratic; use bounded campaigns and profile real storage. The runtime registers closed files from an external SDR adapter; it does not drive or validate radios.

Shen mock conversion: 20 documented receiver IDs, six hardware families, 800 synthetic rows; two passes byte-identical for metadata/annotations/IDs/manifests and numerical features. No real payload was downloaded. The staged qualification command remains fail-closed without bound lawful access, provenance, QA, split/method hashes and preregistered blinding evidence.

Next operator actions: select hardware and lawful RF conditions, verify physical IDs/clocks, fill invalid-by-design real templates, perform supervised hardware and actual power-loss tests, then collect separate calibration/query sessions. Labels are supplied afterward for mix QA, not used to reconstruct sessions. No collection or adapter PASS automatically launches scientific training.
