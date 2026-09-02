# Top-Five Evidence: OPERAnet

- **Official source/paper:** [Springer Nature Figshare collection](https://doi.org/10.6084/m9.figshare.c.5551209.v1) and Scientific Data DOI 10.1038/s41597-022-01573-2.
- **Verified acquisition facts:** approximately 8 h from six people in two rooms; two Intel 5300 CSI receivers, three passive Wi-Fi radar surveillance channels, two passive UWB systems (4 and 5 nodes), and synchronized Kinect data.
- **Temporal evidence:** per-row millisecond timestamps; modalities synchronized to one local NTP server with reported <20 ms accuracy; experiment boundaries; activities transition within some long experiments. This is the strongest potential mixed-target temporal structure among the shortlist.
- **Relation evidence:** receiver/channel IDs, UWB transmitter-receiver pairs, room, and experiment exist. Activity, person, and target-position columns are annotations and cannot be relations.
- **Separation risk:** acquisition features and activity/person/location annotations are columns in the same released files, so a converter must enforce logical separation before any relation API sees data.
- **Licence/access:** public modular Figshare downloads are verified. Item-level licence, sizes, and redistribution conditions were not conclusively exposed by the inspected collection view; fail closed as UNRESOLVED until checked through the Figshare API/item records.
- **Task fit:** context-conditioned RF sensing is scientifically distinct, but it is human activity/localization rather than spectrum-situation classification.
- **Verdict:** CONDITIONAL GO for deeper metadata-only inspection; not authorized for adoption or training.
