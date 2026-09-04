# Shen external benchmark qualification handoff

## Outcome first

The official-source qualification verified an attractive independent LoRa
receiver benchmark but did **not** authorize RF payload access or training.
The official licence evidence conflicts and the current author-hosted download
links were unavailable. Exact acquired-calibration replication is separately
NO-GO because no physical target-neutral calibration episode is documented.
No Shen target metric exists.

## VERIFIED DATA FACT

- Canonical dataset: *Radio Frequency Fingerprint LoRa Dataset With Multiple
  Receivers*, IEEE DataPort DOI `10.21227/D6VX-R538`.
- Associated paper: G. Shen, J. Zhang, A. Marshall, R. Woods, A. Cavallaro,
  and L. Chen, *IEEE Transactions on Mobile Computing*, 23(7):7618--7634,
  2024, DOI `10.1109/TMC.2023.3340039`.
- Ten physical transmitters: five LoPy4 and five mbed SX1261 units.
- Twenty physical SDR receivers from six hardware models: nine RTL-SDR, two
  ADALM-PLUTO, two USRP B200, two B200mini, two B210, and three N210.
- Paper settings: 868.1 MHz carrier, 125 kHz LoRa bandwidth, spreading factor
  7, and 1 MHz receiver sample rate.
- Collection: fixed line-of-sight positions in a residential room at
  approximately one metre and reported SNR above 50 dB.
- Reported evaluation subset: 800 training and 100 testing packets for each of
  200 transmitter-receiver pairs.
- Official loader schema: HDF5 arrays named `data`, `label`, `SNR`, and `CFO`;
  complex samples are reconstructed from real/imaginary halves.
- Timestamps and synchronized receiver semantics are not documented.
- Packet indexing is transmitter-nested and is not temporal context.

## VERIFIED SOURCE ACQUISITION

Metadata-only artifacts are external at
`/mnt/d/openew_sa_data/paper3/shen/official_metadata/`:

- official repository `gxhen/receiverAgnosticRFFI`, commit
  `ffad4828c267324fc514a5a729aac93a9b6ff556`;
- accepted TMC manuscript, 1,985,289 bytes, SHA-256
  `ef594aac7d0dd8bd8cecb50a4162c7e4b44790ea24f3bd1ffbe5e917022c30d8`;
- DataCite JSON, 7,780 bytes, SHA-256
  `02774bbc8ba7a4e5138d1147a044e335c8a8aa46f16963f5ee1766f1bae56e38`;
- create-once `metadata_manifest.json`; and
- fail-closed `qualification/qualification_report.json`.

No RF archive, packet payload, checkpoint, prediction, or derived tensor was
downloaded or produced.

## UNRESOLVED GATES

1. DataCite describes CC BY 4.0 while the official author repository states
   CC BY-NC-SA 4.0. Paper copyright cannot resolve dataset rights.
2. Both current and legacy author links target `pan.seu.edu.cn`, which did not
   resolve in this environment. The DataPort record was not available as an
   unattended official payload route.
3. The official code establishes complex-signal storage but payload row shape,
   dtype, full row count, tree semantics, and exact deterministic conversion to
   the frozen 256-IQ contract cannot be verified without payload.
4. Target-proxy, class-support, split-integrity, and two-pass conversion QA were
   correctly not run.

## Benchmark eligibility

| Question | Verdict | Boundary |
|---|---|---|
| Dataset identity/provenance | PASS | Official paper, code, DataCite record |
| Task compatibility | PASS IN PRINCIPLE | Multi-receiver transmitter identification |
| Storage | PASS | 1.87 TB free at preflight; payload size remains unverified |
| Licence | FAIL CLOSED | Conflicting official terms |
| Official access | FAIL | Author host unavailable |
| Raw-IQ frozen-method conversion | UNRESOLVED | Payload not inspected |
| Bounded receiver-support benchmark | NOT ELIGIBLE YET | Q0/Q1/Q3/Q4 incomplete |
| Acquired-calibration exact replication | NO-GO | No acquired calibration episode |
| Training | NOT AUTHORIZED | No source-only smoke or target run performed |

## Next action

Obtain a written licence clarification and a lawful, checksummed official
payload route from the authors/DataPort. If obtained, perform archive safety,
schema, two-pass 256-IQ conversion, proxy, support-cube, and split QA. Only a
committed PASS of those pre-model gates can authorize the conditional blinded
benchmark. It cannot create acquired-calibration realism retrospectively.
