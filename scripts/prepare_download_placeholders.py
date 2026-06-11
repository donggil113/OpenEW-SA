#!/usr/bin/env python
"""Print manual download guidance without fetching large RF datasets."""

GUIDANCE = {
    "deepsense": "Download DeepSense Spectrum Sensing files from the official provider and set configs/data/deepsense.yaml:input_dir.",
    "wisig": "Download WiSig RF Fingerprinting archives from the official WiSig release and set configs/data/wisig.yaml:input_dir.",
    "electrosense": "Export ElectroSense PSD data from the public ElectroSense interface/API according to its terms and set configs/data/electrosense.yaml:input_dir.",
    "jamshield": "Place JamShield CSV metric files in the configured input directory and set feature_columns if needed.",
    "radioml": "Place RML2016.10a_dict.pkl in data/raw/radioml/ or update configs/data/radioml.yaml:input_path.",
}


def main() -> None:
    for name, text in GUIDANCE.items():
        print(f"[{name}] {text}")
    print("\nNo files were downloaded. This script is intentionally a placeholder.")


if __name__ == "__main__":
    main()
