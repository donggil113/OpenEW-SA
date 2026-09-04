"""Scientific gates for the separate official-equalized WiSig diagnostic."""

from __future__ import annotations

import json
from pathlib import Path

from openew.paper3.wisig.validation import load_converted_tables


def validate_equalized_manifests(pass_a: str | Path, pass_b: str | Path) -> dict[str, object]:
    manifests = [json.loads((Path(root) / "dataset_manifest.json").read_text(encoding="utf-8")) for root in (pass_a, pass_b)]
    checks = {
        "both_complete": all(value.get("status") == "COMPLETE" for value in manifests),
        "both_use_official_equalized_index_1": all(value.get("config", {}).get("equalized_index") == 1 for value in manifests),
        "sample_counts_match": manifests[0].get("sample_count") == manifests[1].get("sample_count"),
        "source_hashes_match": manifests[0].get("source_pickle_sha256") == manifests[1].get("source_pickle_sha256"),
        "archive_hashes_match": manifests[0].get("source_archive_sha256") == manifests[1].get("source_archive_sha256"),
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}


def compare_raw_structure(raw_root: str | Path, equalized_root: str | Path) -> dict[str, object]:
    raw_acquisition, raw_annotation = load_converted_tables(raw_root)
    eq_acquisition, eq_annotation = load_converted_tables(equalized_root)
    raw_counts = (
        raw_acquisition[["sample_id", "receiver_id", "day_id"]]
        .merge(raw_annotation[["sample_id", "transmitter_id"]], on="sample_id", validate="one_to_one")
        .groupby(["receiver_id", "day_id", "transmitter_id"], observed=True)
        .size()
        .sort_index()
    )
    eq_counts = (
        eq_acquisition[["sample_id", "receiver_id", "day_id"]]
        .merge(eq_annotation[["sample_id", "transmitter_id"]], on="sample_id", validate="one_to_one")
        .groupby(["receiver_id", "day_id", "transmitter_id"], observed=True)
        .size()
        .sort_index()
    )
    checks = {
        "sample_count_matches_raw": len(raw_acquisition) == len(eq_acquisition),
        "receiver_day_transmitter_support_matches_raw": raw_counts.equals(eq_counts),
        "opaque_sample_ids_are_variant_specific": set(raw_acquisition["sample_id"]).isdisjoint(set(eq_acquisition["sample_id"])),
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}
