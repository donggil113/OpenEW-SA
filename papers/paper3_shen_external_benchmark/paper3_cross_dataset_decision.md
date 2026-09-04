# Paper 3 cross-dataset decision

Status: **STATE E — SHEN UNAVAILABLE/INELIGIBLE; PUBLICATION NOT READY**

## Decision

The Shen corpus is verified as a scientifically attractive independent
multi-receiver LoRa dataset, but it did not pass the gates required for payload
access or exact frozen-method transfer. Therefore no external target result
exists and this workstream cannot claim cross-dataset replication.

| Question | Verdict |
|---|---|
| Shen acquired-calibration replication | NO-GO |
| Shen bounded receiver-support benchmark | CONDITIONAL IN PRINCIPLE; NOT ELIGIBLE NOW |
| Shen payload download | NOT AUTHORIZED / NOT PERFORMED |
| Shen model training | NOT AUTHORIZED / NOT PERFORMED |
| WiSig V2 primary result | FROZEN AND UNCHANGED |
| WiSig post-hoc mechanism addendum | COMPLETE |
| Cross-dataset replication | NOT PERFORMED |
| Paper 3 publication readiness | NOT_READY |

## VERIFIED DATA FACT

Primary sources verify ten LoRa transmitters, twenty physical SDR receivers,
and six receiver hardware models in the Shen dataset, IEEE DataPort DOI
`10.21227/D6VX-R538`. The associated paper is “Towards Receiver-Agnostic and
Collaborative Radio Frequency Fingerprint Identification,” IEEE Transactions
on Mobile Computing, DOI `10.1109/TMC.2023.3340039`.

Official evidence does not establish a physically acquired target-neutral
calibration episode. DataCite reports CC BY 4.0 while the author repository
reports CC BY-NC-SA 4.0. The author-hosted `pan.seu.edu.cn` links were
unavailable in the audit environment, and payload row shape/exact 256-IQ
conversion remains unverified. Official code contains bounded location/day
path clues, but those do not establish canonical payload availability,
timestamps, sessions, or a complete cross-receiver acquisition design.

## BENCHMARK DECISION

PR #86 remains correct for acquired calibration: **NO-GO**. A narrower bounded
unlabeled receiver-support benchmark could be defensible only after written
licence reconciliation, lawful official access, archive/schema inspection,
deterministic two-pass conversion, target-proxy audit, class-support audit,
split freeze, and frozen code-hash verification. A packet hash split must not
be described as a real acquired calibration episode.

## WI-SIG ADDENDUM CONSEQUENCE

The post-hoc addendum does not supply missing external evidence. It shows that
PR #84-style query chunks change V2 P2 by only `+0.000122`, whereas an entire-
receiver-partition upper diagnostic adds `+0.003225`. A shuffled-context-
trained P2 still benefits from natural versus shuffled (`+0.007162`) or null
(`+0.011203`) support, but its absolute performance (`0.794149`) is below
frozen P0 (`0.805679`). At the primary 128-packet budget, T3A (`0.833617` on
the common-query budget analysis) remains well above P2 (`0.806712`). Oracle
composition stress confirms strong method-specific support sensitivity but is
not deployable evidence.

## Maximum defensible claim

On WiSig, matched same-receiver unlabeled support measurably affects the fixed
P2 architecture relative to broken or absent support, but P2 does not provide
a meaningful advantage over independent ERM and is inferior to same-
information T3A. The query-coupling approximation does not explain the V2
attenuation, while unrestricted full-partition access provides only a small
upper-diagnostic increase. No claim of external replication, acquired
calibration realism, P2 superiority, temporal learning, dynamic modeling,
hypergraph learning, or neuro-symbolic reasoning is supported.

## Publication recommendation

**NOT_READY.** Do not create a performance-centered Paper 3 or represent the
Shen corpus as a completed replication. The evidence is suitable as an
internal methods audit and potentially as a cautionary component of a future
cross-dataset receiver-calibration paper.

No submission title is recommended now. If independent data later pass every
gate, the bounded provisional framing remains:

> Unlabeled Receiver Calibration for RF Fingerprinting Under Unseen-Receiver
> Shift: Context Conditioning Versus Test-Time Adaptation

## Next action

Request written licence clarification and a lawful checksummed payload route
from the Shen authors/DataPort. If those arrive, perform metadata-only archive
inspection and conversion/proxy/split QA before authorizing any model run. If
access cannot be resolved, execute the already-designed prospective
target-neutral receiver-calibration collection protocol rather than tuning
WiSig P2 or relaxing the acquisition-episode requirement.
