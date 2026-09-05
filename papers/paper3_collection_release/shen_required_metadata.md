# Required Shen metadata for lawful external evaluation

Request the official file/schema version and checksums; data, label, SNR, CFO shapes/dtypes; I/Q packing and units; sample rate and center frequency; window length, extraction and preprocessing; all physical receiver IDs; serial-to-anonymous-ID continuity; hardware family/manufacturer/model and count; transmitter ID annotation semantics and class support; capture/session/source-record boundaries; ordering, timestamps and clock/reset semantics if they exist; collection sites/days/campaigns; missing records; and filename/directory target encoding.

Receiver identity must not be inferred from a target-bearing filename. Confirm whether physically acquired, target-neutral calibration and query sessions exist. If absent, acquired-calibration replication remains NO-GO even if a bounded support benchmark later qualifies.

The adapter currently follows PR88's documented real-half/imag-half HDF5 contract and centered contiguous 256-complex crop (C2). That is a frozen software transfer candidate, not proof that LoRa fingerprint content survives. No C1/C3/C4 selection or target-visible optimization is authorized. Source-only semantic review remains necessary.
