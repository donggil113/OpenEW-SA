# Top-Five Evidence: WiSig

See [wisig_evidence_matrix.md](wisig_evidence_matrix.md), [wisig_leakage_precheck.md](wisig_leakage_precheck.md), and [wisig_processing_trace.md](wisig_processing_trace.md) for the full audit.

- **Source/paper:** official UCLA CORES dataset release; IEEE Access DOI 10.1109/ACCESS.2022.3154790.
- **Licence/access:** CC BY-NC-SA 4.0; official Google Drive and official GitHub code. Research-compatible, restricted.
- **Scale:** 174 transmitters, 41 receivers, four March 2021 captures, approximately 10 million packets; compact ManyRx about 1.2 GB.
- **Allowed relation:** receiver equality only. Transmitter and target-bearing paths are forbidden.
- **Temporal:** TARGET_NESTED_SEQUENCE; no valid mixed-target acquisition clock.
- **Task fit:** highest of reviewed candidates; direct transmitter RF fingerprinting under receiver/day shifts.
- **Verdict:** CONDITIONAL GO for a static receiver-context adoption; no model authorization yet.
