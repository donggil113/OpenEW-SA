#!/usr/bin/env python
"""Generate a task summary table for OpenEW-SA paper drafts."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

TASKS = [
    {"task": "Spectrum occupancy", "labels": "occupancy_label", "datasets": "DeepSense, ElectroSense", "models": "IQCNN1D, SpectrogramCNN, PSDCNN"},
    {"task": "RF fingerprinting", "labels": "tx_id", "datasets": "WiSig", "models": "IQCNN1D, MultiTaskTransformer"},
    {"task": "Modulation classification", "labels": "modulation_label", "datasets": "RadioML 2016.10A", "models": "IQCNN1D, MultiTaskTransformer"},
    {"task": "Jamming/interference detection", "labels": "abnormal_event_label", "datasets": "JamShield", "models": "TabularMLP, MultiTaskTransformer"},
    {"task": "Situation/threat assessment", "labels": "situation_label, threat_level", "datasets": "All converted datasets", "models": "MultiTaskTransformer"},
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create task summary table.")
    parser.add_argument("--output", default="tables/task_summary.csv", help="Output CSV path.")
    args = parser.parse_args()
    table = pd.DataFrame(TASKS)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
