# Compute-budget fairness protocol

Status: **COMPLETE — PROTOCOL FROZEN BEFORE TARGET-METRIC UNBLINDING**

This audit accompanies the information-budget matrix. Accuracy comparisons do not imply equal deployment cost: receiver-context and adaptation methods encode an unlabeled support bank before classifying disjoint queries.

## Parameter control

The corrected six-class source-only smoke run established these trainable parameter counts before target evaluation:

| Condition | Trainable parameters |
|---|---:|
| P0 / DG-CORAL / DG-GROUPDRO / SOURCE-NORM | 64,774 |
| DG-DANN | 70,754 |
| P0-WIDE | 74,827 |
| P1 | 73,030 |
| P2 and architectural controls | 75,143 |
| RX-NORM / T3A | 64,774 |

P0-WIDE is 0.42% smaller than P2 and satisfies the preregistered ±5% capacity-matching rule. P2-SHUFFLED, P2-NULL, and P2-MISMATCHED-RX load the exact P2 architecture/checkpoint for their fold and seed.

## Measured quantities

Each run record retains total wall time, peak process RSS, peak CUDA allocated memory, completed epochs, query count, context diagnostic timing when instrumented, and parameter count. A separate label-free benchmark measures deterministic support-bank freezing plus query-to-support index assembly five times per receiver and seed.

A standardized inference benchmark is additionally frozen at seed 829 for all 32 receivers and all 13 executable conditions. It reloads each frozen checkpoint, excludes checkpoint-load time, includes support encoding and any test-time prototype/statistics work, performs one warm-up plus three measured repeats, and verifies that reproduced probabilities match the corresponding immutable blind archive to absolute error at most `1e-5`. It never reads target labels. This benchmark supplies comparable test-time latency where the original run record contained only training-plus-inference wall time.

The analysis will report:

- mean and standard deviation of total run wall time;
- median peak CPU RSS and CUDA allocated memory;
- separately instrumented context inference time where available;
- source-training and test-time operation-count approximations;
- target-receiver versus source-validation-donor support bytes;
- support-backbone encoding FLOPs and RX-NORM raw-statistics operations
  separately from per-query inference FLOPs.

## Operation-count scope

The transparent approximation counts multiply/add operations in convolution, linear, and attention-score/weighted-sum layers. It excludes normalization, activation, optimizer bookkeeping, data transfer, the CORAL penalty, and serialization. Backward computation is declared as an approximate two times forward cost, yielding a three-times-forward training approximation. These are comparative engineering estimates, not profiler-exact hardware FLOPs.

For P1/P2, RX-NORM, and T3A, the 128 target-receiver support packets are included in support bytes and support-encoding cost. P2-SHUFFLED and P2-MISMATCHED-RX instead disclose 128 source-validation donor packets. P2-NULL discloses zero support processing. No query packet is counted as support.

Only P1, P2, T3A, and the shuffled/mismatched P2 controls encode support
packets with the RF backbone. RX-NORM instead receives a separate transparent
operation estimate for two streaming I/Q-statistics passes; it is not charged
128 fictitious backbone forwards. Prototype-update arithmetic, like
normalization and transfer overhead, remains outside the FLOP approximation
and is represented in the measured standardized latency.

## Interpretation boundary

No method is declared compute-matched merely because its parameter count is similar. Final interpretation must jointly report predictive results, target information access, support-processing cost, adaptation state, latency, and memory. Missing independent-model inference instrumentation is labeled missing rather than imputed from a favorable method.

## VERIFIED RESULT

The standardized seed-829 benchmark reproduced all 416 blind receiver-by-model probability archives with maximum absolute error 0.0 and did not read target labels. Median timings include support encoding or adaptation but exclude checkpoint loading.

| Method | Parameters | Median latency (s) | Median throughput (samples/s) | Median peak GPU allocation (MiB) |
|---|---:|---:|---:|---:|
| P0 | 64,774 | 0.020513 | 227,196 | 158.79 |
| P0-WIDE | 74,827 | 0.020529 | 222,468 | 158.94 |
| P1 | 73,030 | 0.544335 | 8,572 | 173.04 |
| P2 | 75,143 | 0.557081 | 8,373 | 177.20 |
| RX-NORM | 64,774 | 0.023858 | 194,298 | 68.34 |
| T3A | 64,774 | 0.024697 | 186,983 | 70.33 |

P2's median standardized latency was approximately 27.2 times P0 and 22.6 times T3A. Its approximate full-query test cost was 22.110 billion counted operations, including 577.765 million support-encoding operations, versus 21.402 billion for T3A. These are transparent comparative estimates under the exclusions above.

Across 160 P2 training records, mean total run wall time was 98.296 s, compared with 30.992 s for P0. Derived controls reuse checkpoints, so their recorded run wall time is not a substitute for source-training cost. Median label-free context-index assembly over 160 receiver-by-seed banks was 0.478204 s (range 0.403421--0.492423) across five repeats.

## INTERPRETATION

P2's receiver-matched support is more useful than shuffled or mismatched support to the same architecture, but its near-zero advantage over P0 is obtained at materially higher test-time cost. T3A is both more accurate and much faster under the same 128-packet target-receiver information budget. Compute therefore reinforces, rather than rescues, the `NOT_READY` publication assessment.
