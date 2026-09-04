# Official equalized-signal diagnostic protocol

Status: **FROZEN BEFORE TARGET-METRIC UNBLINDING**

The official WiSig ManyRx object contains an unprocessed 256-sample preamble representation and an official equalized representation of the same 256 samples. The [official UCLA release page](https://cores.ee.ucla.edu/downloads/datasets/wisig/) and the authors' [`WiSig-dataset` source organization](https://github.com/WiSig-dataset) establish this pairing; the locally immutable pickle also declares two exact `equalized_list` values. The equalized variant is therefore a valid RF preprocessing diagnostic; it is not a new dataset, not pooled with the raw primary analysis, and not selected using V2 results.

## Fixed design

- Reuse the immutable official `ManyRx.pkl` source and PR #84 restricted loader/converter.
- Set `equalized_index=1`; write two deterministic conversion passes under the V2 external root.
- Verify byte-identical deterministic manifests and numerically identical feature shards.
- Rebuild V2 split IDs for the equalized sample-ID namespace with the same hardware-balanced LOSO rule and common support-feasible transmitter intersection.
- Evaluate all 32 LOSO test receivers, seed 829 only, for P0, P2, and P2-SHUFFLED: 96 condition records.
- Use the same 128-packet support bank, disjoint query rule, and `k=32` as the raw primary analysis.
- Keep target metrics blind until the raw primary suite has completed and its one-time unblinding manifest exists.

The single-seed equalized study is diagnostic and cannot by itself establish confirmatory receiver-level uncertainty. Its question is narrower: does the direction of P2 versus P0 and P2-SHUFFLED remain visible after the official WiSig equalization preprocessing? If conversion determinism, sample reconciliation, or split feasibility fails, the diagnostic is skipped and the failure is reported without changing the raw study.
