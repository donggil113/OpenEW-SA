# WiSig Processing Trace

## Verified flow

1. **Acquisition.** One transmitter sends random bytes at a time on Wi-Fi channel 13. Multiple USRPs independently capture approximately 0.512 s at 25 MS/s and 2462 MHz. Receivers are not time/frequency synchronized.
2. **Raw file identity.** The authors' parser recognizes names containing transmitter, receiver, frequency, gain, capture length, and sample rate. This file identity is target-bearing.
3. **Packet extraction.** `split_signal_fun.py` energy-detects packets, removes AP acknowledgements, and iterates detected packets in raw source order. The first 256 preamble samples are retained; an equalized variant is also produced.
4. **Index creation.** Official raw and signal-info pickle indexes retain date, receiver, transmitter, archive/file descriptors, and packet counts. The inspected index matrix covers 4 dates, up to 41 receivers, 174 transmitters, and 9,976,477 extracted packets.
5. **Compact subsets.** `create_subset.py`/related code selects dates, receivers, transmitters, and signal counts into pickle dictionaries. `tx_list`, `rx_list`, and `capture_date_list` survive, but a stable per-packet raw-capture/source-record identifier and per-packet acquisition timestamp do not.
6. **Example model input.** Example code assembles packet arrays and labels and can randomly shuffle examples. This final order is not acquisition order.

## Field disposition

| Raw/source property | Survives official compact data? | Qualification |
|---|---|---|
| Receiver ID | Yes | target-neutral relation candidate |
| Capture date/day | Yes | split-only coarse domain |
| Transmitter ID | Yes | target annotation |
| Frequency and sample rate | Encoded in raw naming/config; not needed per compact sample | provenance/model feature only |
| Receive gain/capture length | Raw naming/config | provenance only unless explicitly retained |
| Raw capture identity | Not as a target-neutral sample key | target-bearing; forbidden relation |
| Within-capture packet index | Detection loop has order, but compact sample provenance does not preserve it | lost for defensible temporal use |
| Acquisition timestamp | No explicit timestamp found | lost/unavailable |
| Receiver hardware/model | Dataset-level descriptions exist | record-level mapping needs verification |
| ORBIT geometry | Node grid semantics exist | not normalized into compact metadata |

## Temporal conclusion

**TARGET_NESTED_SEQUENCE.** Packet order inside a raw capture is a physical extraction order, but every capture contains one transmitter. Using adjacent packets would recreate same-target grouping. There is no verified cross-target acquisition clock, synchronized receiver sequence, gap semantics, or target-neutral mixed-class episode. Four dates are coarse domains, not dynamic context.

## Security note

Official metadata indexes and compact datasets use Python pickle. The forensic scripts use a restricted unpickler that permits only the minimal NumPy reconstruction types required by the trusted official indexes. General candidate tooling must not load arbitrary pickle content.

## Prospectively preservable fields

A future capture should add an opaque session UUID, capture UUID, UTC timestamp with uncertainty and clock-reset semantics, within-capture source index, receiver hardware hash, and target-neutral collection episode. Transmitter annotation must be stored separately and must not appear in paths.
