# WiSig execution environment

The preregistered suite ran sequentially under WSL2 Ubuntu 24.04 on one NVIDIA GeForce RTX 4090 (24,564 MiB reported memory; driver 591.86) and a 13th Gen Intel Core i9-13900K exposed as 32 logical CPUs. No two training runs shared the GPU.

Software versions recorded during execution:

- Python 3.12.3
- PyTorch 2.11.0+cu128
- CUDA runtime reported by PyTorch: 12.8
- NumPy 2.5.1
- pandas 3.0.3

The external converted data were read from the `/mnt/d` WSL mount. Run records preserve device, source Git SHA, data-manifest SHA, split SHA, configuration hash, parameter count, peak GPU allocation, process peak RSS, wall time, checkpoint state, and prediction hash. A separate no-model benchmark measures logical dataset bytes, bundle-load time, and receiver-context construction overhead; OS page-cache effects mean logical bytes are reproducible whereas physical storage traffic is not claimed.
