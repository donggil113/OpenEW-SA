# Frozen prior evidence for the WiSig static receiver-context study

This snapshot was created before payload conversion, split construction, or model evaluation. It preserves the merged PR #83 decision at Git commit `8d7d3cfca85a200a781fada3c5ca15dbaef3cfe2`.

## Verified facts

- WiSig contains 174 transmitter identities, 41 USRP receiver identities, and four captures/days in the full official metadata universe.
- The official metadata indexes represent approximately 9,976,477 extracted packets.
- Acquisition used Wi-Fi channel 13, a 2,462 MHz center frequency, 20 MHz Wi-Fi bandwidth, and 25 MS/s complex sampling.
- The official dataset licence is Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International. The required dataset-paper citation is DOI `10.1109/ACCESS.2022.3154790`.
- The compact ManyRx subset is reported by the official page as 10 transmitters, 32 receivers, 200 signals per transmitter-receiver pair, and four days. It is not the full 174-by-41 metadata universe.
- No valid acquisition timestamp is available in the released compact schema.
- Packet/extraction order is nested inside target-specific captures. It is audit-only and cannot define temporal neighbors.
- `receiver_id` passed the aggregate target-proxy audit: full indexed coverage, 41 groups, maximum group target purity 0.022712, and normalized mutual-information diagnostic 0.022617.
- Capture day is `SPLIT_ONLY`. Transmitter identity is the task annotation and is forbidden as relation/context.
- Temporal relational modeling and dynamic modeling remain NO-GO.

## Frozen scientific boundary

The authorized question is whether target-neutral same-receiver context helps transmitter recognition under prespecified unseen-receiver and unseen-day shifts. This work does not rerun or reinterpret PR #81 and does not authorize temporal, dynamic, uncertainty-gated, neuro-symbolic, or transmitter-derived context.

The ManyRx-specific sample universe, exact class/domain support, and split feasibility are unresolved until deterministic conversion and full sample-level QA complete.
