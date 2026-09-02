# Top-Five Evidence: Antwerp LPWAN Localization

- **Official source:** [Zenodo record 3342253](https://doi.org/10.5281/zenodo.3342253), University of Antwerp/imec authors.
- **Verified facts:** three months of real LoRaWAN/Sigfox messages; receiving time, IDs and RSSI for receiving base stations, and GPS-derived location. The updated LoRaWAN table contains all receiving gateways and some nanosecond-precision gateway timestamps.
- **Relation evidence:** base-station identity and message reception groups are physical acquisition context. Geographic target position and device trajectory are task annotations/audit data, not relations.
- **Temporal evidence:** receiving time is explicit and messages recur across a collection period. Clock/reset semantics, device-session boundaries, mixed-target episode construction, and inference-time target neutrality still require file-level validation.
- **Data type/task:** tabular network measurements rather than raw IQ. The natural task is outdoor fingerprint localization, so task distinctness from Papers 1/2 is strong but its fit to RF situation assessment is indirect.
- **Licence/access/size:** public Zenodo access is verified; the inspected description reports small CSV-style records, but the exact active-version licence and aggregate byte count must be reverified after Zenodo rate limiting. Status UNRESOLVED for adoption.
- **Verdict:** MAYBE / CONDITIONAL metadata import; no experiment authorization.
