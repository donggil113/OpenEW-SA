#!/usr/bin/env python
"""Create a tiny synthetic OpenEW-SA dataset for smoke tests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from openew.data.schema import MetadataRecord, records_to_frame, validate_metadata_frame

DATASET_SOURCES = ["deepsense", "wisig", "electrosense", "jamshield", "radioml"]
SITUATIONS = ["normal", "congested", "abnormal"]
THREAT_LEVELS = ["low", "medium", "high"]
MODULATIONS = ["bpsk", "qpsk", "8psk", "qam16", "ofdm"]
FREQUENCY_BANDS = ["sub6_2_4ghz", "sub6_3_5ghz", "ism_915mhz", "vhf_150mhz"]
FEATURE_DIM = 64
DEFAULT_NUM_SAMPLES = 240
MIN_NUM_SAMPLES = 200

INPUT_TYPES = {
    "deepsense": "iq_features",
    "wisig": "iq_features",
    "electrosense": "psd_features",
    "jamshield": "tabular_metrics",
    "radioml": "iq_features",
}

THREAT_BY_SITUATION = {
    "normal": "low",
    "congested": "medium",
    "abnormal": "high",
}

OCCUPANCY_BY_SITUATION = {
    "normal": "light",
    "congested": "occupied",
    "abnormal": "occupied",
}

EVENT_BY_SITUATION = {
    "normal": "none",
    "congested": "congestion",
    "abnormal": "jamming",
}


def make_tiny_dataset(output_dir: str | Path, num_samples: int = DEFAULT_NUM_SAMPLES, seed: int = 7) -> None:
    """Write metadata.csv, features.npy, and labels.json for a tiny mixed-source dataset."""

    if num_samples < MIN_NUM_SAMPLES:
        raise ValueError(f"num_samples must be at least {MIN_NUM_SAMPLES}; got {num_samples}")

    rng = np.random.default_rng(seed)
    features: list[np.ndarray] = []
    records: list[MetadataRecord] = []
    source_offsets = {source: rng.normal(0.0, 0.15, size=FEATURE_DIM) for source in DATASET_SOURCES}

    situation_indices = np.arange(num_samples) % len(SITUATIONS)
    rng.shuffle(situation_indices)

    for index, situation_index in enumerate(situation_indices):
        situation = SITUATIONS[int(situation_index)]
        threat = THREAT_BY_SITUATION[situation]
        source = DATASET_SOURCES[index % len(DATASET_SOURCES)]
        modulation = MODULATIONS[index % len(MODULATIONS)]
        feature = _make_feature_vector(situation, threat, source_offsets[source], rng)
        features.append(feature)
        records.append(
            MetadataRecord(
                sample_id=f"tiny_{index:06d}",
                dataset_source=source,
                input_type=INPUT_TYPES[source],
                time_index=index,
                frequency_band=FREQUENCY_BANDS[index % len(FREQUENCY_BANDS)],
                tx_id=f"tx_{index % 12:02d}",
                rx_id=f"rx_{index % 6:02d}",
                modulation_label=modulation,
                occupancy_label=OCCUPANCY_BY_SITUATION[situation],
                abnormal_event_label=EVENT_BY_SITUATION[situation],
                domain_id=f"tiny_domain_{index % 4}",
                synthetic_mission_context="tiny_spectrum_situation_awareness",
                situation_label=situation,
                threat_level=threat,
                human_review_required=situation == "abnormal",
            )
        )

    labels = {
        "dataset_source": "tiny_synthetic_openew",
        "dataset_sources": DATASET_SOURCES,
        "feature_dim": FEATURE_DIM,
        "feature_file": "features.npy",
        "num_samples": num_samples,
        "tasks": {
            "situation_label": SITUATIONS,
            "threat_level": THREAT_LEVELS,
            "occupancy_label": sorted(set(OCCUPANCY_BY_SITUATION.values())),
            "abnormal_event_label": sorted(set(EVENT_BY_SITUATION.values())),
            "modulation_label": MODULATIONS,
        },
    }
    _save_tiny_artifacts(output_dir, records, np.stack(features).astype(np.float32), labels)


def _make_feature_vector(situation: str, threat: str, source_offset: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Create a simple feature vector with learnable class signal plus source/domain noise."""

    feature = rng.normal(0.0, 0.35, size=FEATURE_DIM)
    feature += source_offset
    feature[: len(SITUATIONS)] += _one_hot(SITUATIONS.index(situation), len(SITUATIONS)) * 2.5
    feature[8 : 8 + len(THREAT_LEVELS)] += _one_hot(THREAT_LEVELS.index(threat), len(THREAT_LEVELS)) * 1.5

    if situation == "congested":
        feature[16:32] += np.linspace(0.2, 1.0, 16)
    elif situation == "abnormal":
        feature[32:48] += rng.normal(1.2, 0.2, size=16)
    else:
        feature[48:] -= 0.4
    return feature


def _one_hot(index: int, size: int) -> np.ndarray:
    vector = np.zeros(size, dtype=np.float32)
    vector[index] = 1.0
    return vector


def _save_tiny_artifacts(
    output_dir: str | Path,
    records: list[MetadataRecord],
    features: np.ndarray,
    labels: dict[str, object],
) -> None:
    output_path = Path(output_dir).expanduser()
    output_path.mkdir(parents=True, exist_ok=True)
    validate_metadata_frame(records_to_frame(records)).to_csv(output_path / "metadata.csv", index=False)
    np.save(output_path / "features.npy", features)
    with (output_path / "labels.json").open("w", encoding="utf-8") as handle:
        json.dump(labels, handle, indent=2, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a tiny synthetic OpenEW-SA dataset.")
    parser.add_argument("--output-dir", required=True, help="Directory for metadata.csv, features.npy, and labels.json.")
    parser.add_argument("--num-samples", type=int, default=DEFAULT_NUM_SAMPLES, help="Number of samples to generate.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for deterministic synthetic data.")
    args = parser.parse_args()

    make_tiny_dataset(args.output_dir, num_samples=args.num_samples, seed=args.seed)
    print(f"Wrote {args.num_samples} synthetic samples to {Path(args.output_dir)}")


if __name__ == "__main__":
    main()
