from __future__ import annotations

from pathlib import Path

import numpy as np


def compact_fixture(signal_length: int = 4, packets: int = 3) -> dict[str, object]:
    data = []
    for tx in range(2):
        by_rx = []
        for rx in range(2):
            by_day = []
            for day in range(2):
                by_eq = []
                for equalized in range(2):
                    base = tx * 1000 + rx * 100 + day * 10 + equalized
                    by_eq.append(np.full((packets, signal_length, 2), base, dtype=np.float64))
                by_day.append(by_eq)
            by_rx.append(by_day)
        data.append(by_rx)
    return {
        "tx_list": ["01", "02"],
        "rx_list": ["001", "002"],
        "capture_date_list": ["day_a", "day_b"],
        "equalized_list": [0, 1],
        "max_sig": packets,
        "data": data,
    }


def tiny_arrays() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    sample_ids = np.asarray([f"s{i:02d}" for i in range(12)])
    receivers = np.asarray(["001"] * 5 + ["002"] * 4 + ["003"] * 3)
    indices = np.arange(len(sample_ids), dtype=np.int64)
    return indices, receivers, sample_ids
