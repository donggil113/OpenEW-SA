# Reproducibility audit
VERIFIED: fresh local clone of commit32667ac77874df55a6e549296a86c976ac53679a ran the public payload-absent command successfully. All1724 tests passed (1707 Paper3 including258 new;17 Paper2), plus7 subtests. Six existing warnings were not suppressed or fixed by changing old code. Compileall and git diff --check passed.

The six-step command verifies method/evidence/release hashes, runs tests, compiles Python, rebuilds figures/tables, builds all three PDFs with the externally supplied official Access template, audits PDF fonts/references, and checks whitespace. Rebuilt canonical figures/tables/evidence match expected SHA256 exactly; the fresh clone remains clean. No RF data were loaded by this command.

PDF page counts and technical properties reproduce (8 TMLCN,9 Access,10 supplement; all fonts embedded; zero Type3, undefined references/citations and overfull boxes). Binary PDF hashes differ because TeX includes build-time metadata. Bitwise PDF reproducibility is NOT claimed; deterministic scientific tables/figures and semantic PDF properties are verified.

Environment scope: new checkout, same installed Linux/WSL Python3.12.3/PyTorch2.11.0+cu128 environment and TeX installation. This is not a clean-machine dependency installation or independent GPU replication. The observed package lock contains exact installed versions, not secret-bearing direct URLs. CPU-only portability of every scientific GPU operation is not asserted.

Release scan found no private workstation paths, token patterns or private keys in the public release directory. It includes32 split hashes, opaque-code reconstruction rules, method hashes and52 expected small-artifact checksums. Existing historical scripts retain their original defaults; public instructions use caller-selected roots.

The 25000 generated transitions are SYNTHETIC state-model cases. Twenty-five actual synthetic POSIX fault transactions include six abrupt subprocess exits; corruption is rejected. UHD/SoapySDR are optional adapter interfaces, not physically validated receivers.

Remaining human actions: review derivative-release permissions, install/verify the environment on a separate machine if claiming cross-machine reproducibility, supply lawful external data or acquire real episodes, and complete author/venue metadata. No RF payload, checkpoints or sample-level predictions are in the release.
