# Real collection operator runbook

## Before the site visit

1. Obtain institutional/spectrum/privacy approval and consent for controlled transmitters. This software does not authorize RF transmissions. Confirm frequency, bandwidth, sample rate, gain policy and permitted site conditions.
2. Select the tier and inventory every physical receiver, hardware family, antenna and host. Resolve serial aliases. Do not assume any SDR is currently owned.
3. Choose a clock authority (GNSS/PTP/NTP/device disciplined clock as appropriate), measure its uncertainty and retain evidence outside task annotations. Decide what device restart/reset means for counters.
4. Provision disk using the storage estimator, including two raw copies, two conversion passes and additional checkpoint reserve. Test fsync and an actual power interruption on the intended host/storage stack.
5. Create target-neutral directories and a separate annotation workspace. Fill templates with verified values; their placeholder timestamps/rates must not be used as measurements.

## Activate and initialize

Use the approved Python environment and repository script on Linux/WSL:

    export PYTHONPATH=src
    scripts/paper3/collection_runtime/paper3-collect --root /data/campaign-opaque campaign-init --spec campaign.json
    scripts/paper3/collection_runtime/paper3-collect --root /data/campaign-opaque receiver-register --spec receiver.json

Repeat receiver-register for each approved UUID. The campaign is site-specific. Across sites/days retain the physical receiver UUID, create new campaign/session/capture UUIDs, and never reuse payload records.

## Clock and calibration session

Verify UTC against the chosen authority. Open a new CALIBRATION session before the target-neutral collection period. Calibration timing/participation is fixed by acquisition schedule, not selected after label inspection. Multiple controlled transmitters should be active or interleaved by a schedule independent of receiver identity. Record schedule/provenance separately, not in model metadata.

    scripts/paper3/collection_runtime/paper3-collect --root /data/campaign-opaque session-open --spec calibration_session.json

The external SDR adapter writes and closes <opaque_capture_uuid>.bin. It must report real sample counters and sample count, not infer order from filenames or mtime.

    scripts/paper3/collection_runtime/paper3-collect --root /data/campaign-opaque capture-register --spec capture.json

Do not register an active/growing file. Check command exit status and JSON, then preserve the original until the checksum-backed day freeze and backup have passed. Capture filenames and all source directory components must be target-neutral.

## Query session

Close calibration with measured end UTC/counter:

    scripts/paper3/collection_runtime/paper3-collect --root /data/campaign-opaque session-close --spec calibration_close.json

Start a physically separate QUERY session with a different session UUID. Repeat capture registration. Do not create “query” by randomly relabeling captures from calibration. Both roles are required per physical receiver for a completed campaign. Same-receiver sessions cannot overlap. A clock reset needs a new reset UUID plus operator provenance; metadata cannot excuse an unexplained backward UTC jump.

## Annotation and QA

Only the annotation operator joins capture IDs to targets, with annotation source/time. Raw capture naming remains opaque. The collection runtime need not access labels during acquisition.

    scripts/paper3/collection_runtime/paper3-collect --root /data/campaign-opaque annotation-qa --annotations annotations.csv

A target-pure or incompletely annotated calibration session FAILS mix QA. Do not rebuild session boundaries or cherry-pick packets to make it pass. Preserve the failure, diagnose acquisition design and preregister a future collection correction. All QA is diagnostic; it never launches training.

## End of day

Close every session, then:

    scripts/paper3/collection_runtime/paper3-collect --root /data/campaign-opaque validate
    scripts/paper3/collection_runtime/paper3-collect --root /data/campaign-opaque freeze-day --day YYYY-MM-DD
    scripts/paper3/collection_runtime/paper3-collect --root /data/campaign-opaque status

Freeze files are create-once and bound into the journal. Copy payload, metadata, journal/state and freeze manifest to a separate backup device; compare SHA256 on the backup. Read-only media/offline copies protect against accidental or malicious rewriting better than local checksums alone. Never delete the only copy.

After all days and approved receivers/roles are complete:

    scripts/paper3/collection_runtime/paper3-collect --root /data/campaign-opaque campaign-close

Run cross-campaign tier/mix QA and obtain human physical/provenance sign-off before any scientific split or modeling gate.

## Failure recovery

Stop capture writes; retain all files. Record the last observed command and hardware status.

    scripts/paper3/collection_runtime/paper3-collect --root /data/campaign-opaque recover

Read every issue. Valid durable journal transitions may replay. Partial payloads, orphan metadata/payload, unclosed sessions and checksum changes are never silently promoted. Quarantine evidence using a separately recorded operator procedure; recapture with new IDs where necessary. Do not delete a partial freeze to pretend it never occurred. See recovery_and_atomicity.md.

## Handoff

Supply campaign/receiver provenance, all freeze hashes, backup verification, mix-QA failures as well as passes, operating/licence approvals and measured clock behavior. No training authorization follows from a clean status report alone.
