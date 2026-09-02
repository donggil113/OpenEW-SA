# Top-Five Evidence: OSU LoRa RFFP

- **Official source:** Oregon State NetSTAR [dataset hub](https://research.engr.oregonstate.edu/hamdaoui/datasets), [release note](https://research.engr.oregonstate.edu/hamdaoui/sites/research.engr.oregonstate.edu.hamdaoui/files/release_note_lora_datasets_final_oct2023_v2.pdf), and institutional file index.
- **Paper:** A. Elmaghbub and B. Hamdaoui, *LoRa Device Fingerprinting in the Wild*, IEEE Access 2021.
- **Verified acquisition facts:** 25 Pycom target devices; USRP B210 receivers; 915 MHz; 1 MS/s; I/Q and FFT data. Setups vary days, indoor/outdoor/wired channel, distance, configuration, location, and receiver. The different-receiver setup has two receiver directories.
- **Metadata:** each binary has an associated plain JSON/SigMF-like metadata file with sample rate, recording time/day, carrier frequency, and setup-specific values. The hierarchy and filenames expose device identity.
- **Licence/access:** release note explicitly permits download/use for research and asks for citation. It does not state a standard payload licence or clear redistribution/derived-artifact terms. Licence is therefore RESTRICTED/UNRESOLVED for redistribution.
- **Size:** official release describes more than 1.2 TB and individual 153 MB data files; automatic full download is forbidden.
- **Proxy risk:** device is the target and appears in path/file names. Receiver/location/day are potentially target-neutral, but some setups confound one context axis at a time and must be audited per file.
- **Temporal:** timestamps are real provenance, but each transmission file is target-pure. No mixed-target session/reset contract is documented. Verdict TARGET_NESTED_SEQUENCE.
- **Task fit:** strong for static domain generalization; weaker relation diversity than WiSig.
- **Verdict:** CONDITIONAL GO for metadata-first static DG; NO-GO for temporal/dynamic adoption.
