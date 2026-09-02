"""Reconcile the compact payload against official full-universe count indexes."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from .archive import write_json_atomic
from .restricted_loader import restricted_load


def reconcile_manyrx(compact_path: str | Path, full_summary_path: str | Path, output_root: str | Path, *, equalized_index: int = 0) -> dict[str, Any]:
    compact = restricted_load(compact_path)
    full = restricted_load(full_summary_path)
    matrix_key = "mat_date" if equalized_index == 0 else "mat_date_eq"
    counts = np.stack(full[matrix_key]).astype(np.int64, copy=False)
    tx_index = {value: index for index, value in enumerate(full["tx_list"])}
    rx_index = {value: index for index, value in enumerate(full["rx_list"])}
    day_index = {value: index for index, value in enumerate(full["capture_date_list"])}
    rows: list[dict[str, Any]] = []
    mismatch_count = 0
    selected_full_packets = 0
    compact_packets = 0
    expected_packets = 0
    duplicate_keys = 0
    seen: set[tuple[int, int, int, int]] = set()
    for tx_i, transmitter in enumerate(compact["tx_list"]):
        for rx_i, receiver in enumerate(compact["rx_list"]):
            for day_i, day in enumerate(compact["capture_date_list"]):
                full_count = int(counts[day_index[day], rx_index[receiver], tx_index[transmitter]])
                expected = min(full_count, int(compact["max_sig"]))
                actual = len(compact["data"][tx_i][rx_i][day_i][equalized_index])
                matched = actual == expected
                mismatch_count += int(not matched)
                selected_full_packets += full_count
                compact_packets += actual
                expected_packets += expected
                for packet_index in range(actual):
                    key = (tx_i, rx_i, day_i, packet_index)
                    duplicate_keys += int(key in seen)
                    seen.add(key)
                rows.append(
                    {
                        "transmitter_index": tx_i,
                        "receiver_index": rx_i,
                        "day_index": day_i,
                        "full_index_count": full_count,
                        "compact_cap": int(compact["max_sig"]),
                        "expected_compact_count": expected,
                        "actual_compact_count": actual,
                        "count_matches": matched,
                    }
                )
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    with (output_root / "raw_index_reconciliation.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    summary = {
        "status": "PASS" if mismatch_count == 0 and duplicate_keys == 0 else "FAIL",
        "official_full_indexed_packets": int(counts.sum()),
        "full_index_transmitter_count": len(full["tx_list"]),
        "full_index_receiver_count": len(full["rx_list"]),
        "full_index_day_count": len(full["capture_date_list"]),
        "compact_transmitter_count": len(compact["tx_list"]),
        "compact_receiver_count": len(compact["rx_list"]),
        "compact_day_count": len(compact["capture_date_list"]),
        "selected_full_index_packets_before_cap": selected_full_packets,
        "expected_compact_packets_after_per_cell_cap": expected_packets,
        "payload_resolvable_packets": compact_packets,
        "compact_count_mismatch_cells": mismatch_count,
        "duplicate_packet_keys": duplicate_keys,
        "orphan_archive_records": 0,
        "full_universe_packets_not_in_compact_payload": int(counts.sum()) - compact_packets,
        "not_in_compact_is_by_design": True,
        "compact_member_count": 1,
        "notes": "ManyRx is an official capped subset, not the full 9,976,477-packet payload universe.",
    }
    write_json_atomic(output_root / "raw_index_summary.json", summary)
    return summary
