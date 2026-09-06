# Collection durability and optional SDR interfaces

SYNTHETIC SOFTWARE VALIDATION ONLY. UHD and SoapySDR are injection interfaces, not certified hardware drivers. Construction/probing does not open a device. An operator must explicitly enable a reader translating actual driver timestamps, sample counters, overflow and clock-reset status into the framed stream contract. No physical receiver or RF front end was tested.

The adapter requires canonical opaque receiver/session/reset UUIDs, positive finite rate/frequency, clock authority, complex64 little-endian samples, exact counters and complete counts. Overflow, reset or partial frames fail closed. Labels are absent from the streaming signature. Integrate finalized capture receipts with the immutable PR89 Collector; annotations remain separate.

The new deterministic stress executed 25,000 generated state transitions, including all eight requested fault types. This is a reference state-machine test, not 25,000 disk transactions. Separately, 24 actual durable-store interruption/recovery transactions and one corrupt-journal case exercised the PR89 POSIX store; six used abrupt subprocess exit. Corrupt evidence was preserved and rejected. Prior full collection tests also remain in the regression suite.

The generated trace ends during WRITING, deliberately not silently finalized. Complete counts increase only on successful finalize; quarantined captures require recovery and are never promoted. Full-state journals retain the prior bounded-scale/O(N-squared) storage limitation. Real disk-full hardware, filesystem/drive cache behavior, driver overflow timing and power-cut durability still require an operator's hardware acceptance test. Software READY; hardware validation NOT PERFORMED.
