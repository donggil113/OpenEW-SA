# Final integrity report
VERIFIED PASS against PR89 base7b83dbcf25dc05f9130b75fdb92ce2d3ce225e92: every pre-existing tracked file is unchanged. All branch changes are new files in the authorized new paths, including the explicitly requested new reproducibility_release subdirectory. Paper1, Paper2 and PR80–89 frozen source, tests, protocols and reports have empty modification diffs.

Read-only external audit scope:
- official WiSig archive SHA d2b23108c3f6f63a10ebbb149d7b08d6e1c1961cf5184926fbab452def3049de matched;
- conversion passesA/B:124 members each,249666 packets each, all recorded shard hashes matched;
- all2080 primary V2 registries/predictions/checkpoint-manifest entries matched;
- all260 day and180 grouped V2 prediction hashes matched;
-64 listed V2 analysis files,23 prior mechanistic-addendum analysis files,32 receiver-benchmark analysis files matched;
- all2400 NEW addendum records reconciled again after analysis, including exact query IDs, support disjointness, split/data/method hashes, original P0/P2 checkpoints and adapted checkpoints where applicable.

Final new-prediction manifest SHA45b46519d1e9c4841a9a8c2fe4e40c3e552de96ff7f0087200ec7b9c18185369 is unchanged from the one-time unblinding. Final execution-integrity report SHA32714a53e58d111badaca575b772c84901c69942923d673f5fc8bfe63b5f2316. Unblinding was not repeated.

No frozen output root was written. No P2 change, receiver/seed removal, target-selected support budget, target-dependent method revision, new RF download, or model-from-scratch restart occurred. Timing replay is separately labeled and matches frozen probabilities.

Scope limit: older non-WiSig raw datasets and nonprimary checkpoint payloads were not all rehashed anew. Their repository packages remain unchanged; no writes were directed there. This is a scoped integrity proof, not an assertion that every byte on the workstation was audited.
