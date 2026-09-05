# Shen replication-ready adapter and transfer ledger

Status: **SOFTWARE CONTRACT ONLY — NO SHEN PAYLOAD OR RESULT**

The PR #87 licence conflict and unavailable author route remain unresolved. This branch does not download payload. Synthetic HDF5 fixtures validate only software behavior.

The loader accepts exactly `data`, `label`, `SNR`, `CFO`. Numeric `data` stores real and imaginary halves; companion arrays must match rows. Receiver identity comes from the verified receiver manifest. Unknown keys/types/shapes/receivers and nonfinite samples fail closed. Acquisition output keeps opaque ID, receiver, hardware, record index, 1 MHz sample rate, and 868.1 MHz center. Transmitter is separate annotation.

Candidate rules are C1 first 256, C2 centered 256, C3 maximum-energy 256, and C4 first/center/last crops. **C2 centered 256 is frozen for a future first payload qualification**: it is target-independent, has no signal-derived search, avoids a file-boundary preference, and preserves single-crop V2 input. Actual signal-validity QA may reject it before modeling, but Shen target performance may not change it.

| Method | Byte-identical reuse | Required change | Prohibited |
|---|---|---|---|
| P0 | backbone/training/normalization | ten-class head; adapter | architecture/optimizer/target tuning |
| T3A | template adaptation and source-validation selection | ten-class head/support IDs | labels/query adaptation |
| P2 | attention/backbone/training/k=32 | ten-class head/support IDs | attention/backbone/support tuning |
| P2-SHUFFLED | receiver-breaking control | Shen donor map | label shuffle |
| SHEN-GRL | none under 256-IQ | official method needs 52x126 transform/2-D CNN | renaming DG-DANN |

All 20 receivers are future LOSO units only if lawful payload, completeness, proxy, and support gates pass. Three validation receivers are deterministic; five seeds, 128 support, and disjoint queries are frozen. No scientific result exists.
