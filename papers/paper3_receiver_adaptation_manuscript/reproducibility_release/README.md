# Paper 3 payload-absent reproducibility release

This NEW release directory supplements PR89 without modifying its manuscript or frozen science. The revised scientific source lives in `papers/paper3_reviewer_remediation/manuscript`. New evidence is explicitly POST-HOC. No RF payload, checkpoint, sample-level probability archive, original target-bearing path, or credential is included.

## One command

From a repository checkout with the observed Python dependencies and TeX Live (IEEEtran, latexmk, lmodern, Poppler) available:

```sh
PYTHONPATH=src python scripts/paper3/reviewer_remediation/reproduce_public.py --output ./reproduction-output
```

Choose a new output directory. This validates method/evidence hashes, runs all Paper3 and Paper2 tests, compiles Python, regenerates all small-summary figures/tables, and builds the TMLCN-oriented manuscript and supplement. It needs no private RF data or network. Optional `--access-template` supplies the verified official IEEE Access template ZIP for the second venue output. No template or proprietary font is vendored here.

The observed lock includes the CUDA-specific PyTorch build. Install PyTorch from the official matching CUDA index before resolving the remaining exact pins; a CPU-only environment can run software/release tests, but is not bitwise scientific GPU reproduction. This is an observed environment record, not a guarantee that every package is obtainable on every OS. Linux/WSL is the runtime contract; native Windows flock/fsync compatibility is not claimed.

## Full scientific reproduction

Full reproduction additionally requires a lawfully obtained official WiSig ManyRx archive, existing frozen V2 checkpoints and split manifests. Supply a caller-selected data root; no private workstation path is required by this document. Expected raw SHA256: d2b23108c3f6f63a10ebbb149d7b08d6e1c1961cf5184926fbab452def3049de. Converted manifest SHA256: ffd98dcb8182435c1aaf416c3bb137e6f56f353811e7d1d7a6fc0cc4817ae4b6.

Support reconstruction uses the byte-preserved V2 stable-hash code and namespace, receiver ID, seed and opaque sample ID. Primary reserves 128; sensitivity reserves 256 then takes nested prefixes. Never reconstruct by transmitter label. Split hashes and original class mapping must match the frozen manifests. `execution_freeze.json` records the addendum grid/protocol/method tree, not a replacement for the V2 data manifest.

Run the frozen scripts into a NEW external root, not existing results. Do not run the blind suite to reproduce a figure: the public summary route already does that. Scientific reruns require review of data/license/checkpoint provenance and a new execution record. One-time unblinding is guarded; no original results are replaced.

## Release and legal boundary

Share code, protocol, hashes, reviewed small summaries, original figures and manuscript source subject to repository policy. Do not redistribute WiSig or Shen payloads, checkpoints containing restricted derivatives without review, target-bearing source paths, or third-party fonts. CC BY-NC-SA payload conditions remain distinct from an eventual article license. Institutional review of derived-summary distribution remains a human gate.
