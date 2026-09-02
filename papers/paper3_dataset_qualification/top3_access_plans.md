# Top-Three Access and Download Plans

## WiSig

- **Mechanism:** official UCLA page -> official Google Drive compact archive.
- **Recommended first artifact:** ManyRx (official page reports approximately 1.2 GB), never Raw (approximately 1.4 TB).
- **Licence:** CC BY-NC-SA 4.0; cite DOI 10.1109/ACCESS.2022.3154790.
- **Storage:** `/mnt/d/openew_sa_data/paper3/candidate_downloads/wisig/`; expected extraction must be measured from archive listing before extraction; reserve at least 4 GB.
- **Integrity:** record resolved official URL, download UTC, exact bytes, SHA-256, archive member list, and licence snapshot.
- **Procedure:** obtain human licence approval; download one archive; verify hash if publisher provides one, otherwise record locally computed hash; scan without executing pickle; use restricted parsing; convert acquisition metadata and annotations separately; run validation/proxy/readiness gates.
- **Approval:** full or compact RF payload requires explicit human approval in this workstream because the official Google Drive endpoint did not expose a stable unattended response and the licence is restricted.

## OPERAnet

- **Mechanism:** official Springer Nature Figshare collection DOI 10.6084/m9.figshare.c.5551209.v1.
- **Metadata-first item:** item metadata for `wificsi1`, `wificsi2`, `pwr`, `uwb1`, and `uwb2`; then one smallest RF modality item only.
- **Licence:** resolve each Figshare item licence through the API/page before data access; collection-level public visibility is insufficient.
- **Storage:** `/mnt/d/openew_sa_data/paper3/candidate_downloads/operanet/`; exact bytes and extraction ratio must be obtained from item metadata.
- **Procedure:** preserve experiment, receiver/channel, room, timestamp, and clock provenance; move activity/person/position to annotations; audit mixed-label episodes and target proxies.
- **Approval:** required until item licence and size are verified.

## OSU LoRa RFFP

- **Mechanism:** official NetSTAR institutional HTTP index.
- **Metadata-first item:** release note plus SigMF metadata sidecars from one setup. Do not fetch `.dat` payload in the metadata stage.
- **Potential first payload:** one officially indexed I/Q file (typically about 153 MB) only after licence/redistribution review.
- **Licence:** research use and citation request are documented; standard licence and derived-artifact redistribution remain unresolved.
- **Storage:** `/mnt/d/openew_sa_data/paper3/candidate_downloads/osu_lora/`; expected extraction equals raw `.dat` size.
- **Procedure:** compute SHA-256; ensure source path/device name is annotation-only; parse JSON without mtime inference; audit receiver/day/location groups and target-pure transmissions.
- **Approval:** required because payload terms are not fully resolved.

No unofficial mirror or authentication secret is permitted. A full dataset over 5 GB is never automatically downloaded.
