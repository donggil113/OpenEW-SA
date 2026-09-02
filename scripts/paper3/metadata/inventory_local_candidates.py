#!/usr/bin/env python3
"""Inventory already-local RF candidates without downloading data."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path


COLUMNS = (
    "dataset", "local_availability", "local_path", "task", "timestamp", "receiver",
    "site", "frequency", "session", "order", "labels", "target_proxy_risk",
    "license_provenance_status", "paper3_readiness", "notes",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="/mnt/d/openew_sa_data")
    parser.add_argument(
        "--output",
        default="/mnt/d/openew_sa_data/paper3/metadata_audit/local_candidate_dataset_inventory.csv",
    )
    args = parser.parse_args()
    root = Path(args.data_root)
    candidates = [
        row("JamShield", root / "raw/jamshield", "jamming detection", "NO", "station", "NO", "2.4 GHz testbed only", "NO", "target-nested counter", "attack", "HIGH: target-bearing files", "official GitHub/paper; dataset terms require human review", "NO-GO", "Current dataset; PR #81 frozen NO-GO."),
        row("DeepSense SDR", root / "raw/deepsense", "spectrum occupancy", "NO", "one receiver", "NO", "four 5 MHz channels", "NO", "target-nested stream", "four-bit occupancy", "HIGH: occupancy-bearing files", "official GitHub; MIT code repository", "NO-GO", "Current dataset; no safe varying relation."),
        row("DeepSense simulated LTE", root / "raw/deepsense/sdr_wifi", "simulated spectrum occupancy", "NO", "NO", "NO", "10 MHz simulated band/SNR", "train/test file", "sample row only", "H5 y", "HIGH: SNR/train-test filename and generated labels", "official DeepSense repository; simulated", "INDEPENDENT SAMPLE ONLY", "Local H5 files add no physical acquisition context."),
        row("ElectroSense PSD", root / "raw/electrosense", "technology classification", "coarse date only", "sensor", "sensor/site token", "filename band", "receiver-date only", "unverified array row", "technology", "HIGH: technology-bearing files and target-associated band", "official GitHub/Zenodo; BSD-style dataset licence text", "NO-GO FOR NEW EXPERIMENT", "Current dataset; receiver/date already tested in PR #81."),
        row("OpenEW-SA tiny fixture", root / "processed/tiny", "software smoke fixture", "NO", "NO", "NO", "placeholder", "NO", "row only", "synthetic", "NOT SCIENTIFIC DATA", "repository fixture", "SOFTWARE TEST ONLY", "Must not be treated as an alternative scientific dataset."),
        row("WiSig", root / "raw/wisig", "RF fingerprinting", "official source describes four days", "official source describes multiple receivers", "UNRESOLVED", "Wi-Fi capture", "day/receiver containers", "UNRESOLVED", "transmitter ID", "requires target-proxy audit", "official source known; no local payload", "NONE: NOT LOCAL", "Config/converter exists but no local dataset path."),
        row("RadioML 2016.10A", root / "raw/radioml", "modulation classification", "NO", "NO", "NO", "synthetic channel conditions", "NO", "synthetic sample index", "modulation/SNR", "HIGH for generator condition fields", "no local payload; terms unresolved", "NONE: NOT LOCAL", "Config/converter exists but no local dataset path."),
    ]
    destination = Path(args.output); destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS); writer.writeheader(); writer.writerows(candidates)
    os.replace(temporary, destination)
    print(f"wrote {len(candidates)} candidate rows to {destination}")


def row(dataset: str, path: Path, task: str, timestamp: str, receiver: str, site: str,
        frequency: str, session: str, order: str, labels: str, risk: str, licence: str,
        readiness: str, notes: str) -> dict[str, object]:
    exists = path.exists()
    return {
        "dataset": dataset, "local_availability": exists, "local_path": str(path),
        "task": task, "timestamp": timestamp, "receiver": receiver, "site": site,
        "frequency": frequency, "session": session, "order": order, "labels": labels,
        "target_proxy_risk": risk, "license_provenance_status": licence,
        "paper3_readiness": readiness, "notes": notes,
    }


if __name__ == "__main__":
    main()
