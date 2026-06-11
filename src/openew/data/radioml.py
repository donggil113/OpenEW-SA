"""RadioML 2016.10A optional baseline/pretraining conversion utilities."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np

from openew.data.common import save_conversion
from openew.data.schema import MetadataRecord, records_to_frame

DATASET_SOURCE = "radioml_2016_10a"


def convert(config: dict[str, Any]) -> None:
    """Convert the manually downloaded RadioML 2016.10A pickle into OpenEW-SA artifacts."""

    input_path = Path(config["input_path"]).expanduser()
    if not input_path.exists():
        raise FileNotFoundError(
            f"RadioML file not found at {input_path}; place RML2016.10a_dict.pkl manually."
        )

    max_samples = config.get("max_samples")
    with input_path.open("rb") as handle:
        data = pickle.load(handle, encoding="latin1")

    arrays: list[np.ndarray] = []
    records: list[MetadataRecord] = []
    for (modulation, snr), samples in sorted(data.items(), key=lambda item: str(item[0])):
        for sample in samples:
            if max_samples is not None and len(records) >= int(max_samples):
                break
            index = len(records)
            arrays.append(np.asarray(sample, dtype=np.float32))
            records.append(
                MetadataRecord(
                    sample_id=f"radioml2016a_{index:08d}",
                    dataset_source=DATASET_SOURCE,
                    input_type="iq",
                    time_index=index,
                    frequency_band=config.get("frequency_band", f"snr_{snr}"),
                    modulation_label=str(modulation),
                    domain_id=f"snr_{snr}",
                    synthetic_mission_context=config.get("synthetic_mission_context", "modulation_pretraining"),
                    situation_label="baseline_pretraining",
                    threat_level=0,
                    human_review_required=False,
                )
            )
        if max_samples is not None and len(records) >= int(max_samples):
            break

    labels = {"task": "modulation_classification", "dataset_source": DATASET_SOURCE, "num_samples": len(records)}
    save_conversion(config["output_dir"], records_to_frame(records), np.stack(arrays), labels, config.get("feature_format", "npy"))
