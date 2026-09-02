# Assessment of already-local RF dataset candidates

The filesystem inventory found no fourth experiment-ready RF dataset. The
machine-readable assessment is
`/mnt/d/openew_sa_data/paper3/metadata_audit/local_candidate_dataset_inventory.csv`.

| Candidate | Local payload | Metadata readiness | Assessment |
|---|---|---|---|
| JamShield | yes | station only; no valid time/session | current PR #81 NO-GO; no new experiment |
| DeepSense SDR | yes | no varying safe relation; no valid time/session | current NO-GO |
| DeepSense simulated LTE | yes, ten HDF5 files | simulated train/test/SNR products; no receiver/site/session | independent-sample only; not an acquisition-context candidate |
| ElectroSense PSD | yes | receiver/date already tested; target-associated band; no time | no new experiment |
| `processed/tiny` | yes | synthetic software fixture | never scientific evidence |
| WiSig | no local payload | official source describes four days and multiple receivers | promising externally, unavailable locally |
| RadioML 2016.10A | no local payload | simulated modulation/SNR conditions | not a prospective acquisition-context source |

Repository converters/configs for WiSig and RadioML are capability stubs, not
evidence that data are locally present. Duplicated professor-share snapshots
are copies of existing OpenEW-SA artifacts, not alternative datasets.

**EXISTING LOCAL ALTERNATIVE DATASET: NONE.**
