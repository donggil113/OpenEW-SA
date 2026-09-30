# Shen representation transfer v2 — source analysis only

VERIFIED SOURCE FACT: the inspected official receiver-agnostic implementation uses a 128-sample STFT window, 64-sample hop and adjacent spectral ratios, producing a 52-by-126 representation from an 8192-I/Q source segment. Its LoRa preprocessing is not the WiSig 256-I/Q task.

NO-GO for a faithful Shen-GRL bridge in this manuscript. A 256-I/Q WiFi packet cannot establish the chirp/preamble semantics of a longer LoRa segment. Concatenating target-specific packets, padding, or calling a shortened CNN the Shen method would not reproduce the source method. No longer continuous WiSig capture has been verified in the bounded compact payload.

FUTURE DESIGN: after lawful Shen access, inspect raw segment length, sample rate, bandwidth, spreading factor, packet-extraction alignment and preamble boundaries against official code. Preserve the source-paper-faithful preamble/8192 segment if verified. A single chirp has symbol length determined by spreading factor and sampling ratio; it is not automatically 256 samples. Select full preamble or chirp only from those physical semantics, before target evaluation. Record every transform and an explicit method/task-head ledger.

The previous centered-256 mock adapter remains SOFTWARE ONLY and is not validation of scientific transfer. A future different representation requires a separate frozen replication protocol, not silent replacement. License/access remain blocked. No Shen RF payload was downloaded and no Shen result exists.
