"""Command-line dispatcher for dataset conversion."""

from __future__ import annotations

import argparse
from importlib import import_module

from openew.utils.config import load_yaml

CONVERTERS = {
    "deepsense": "openew.data.deepsense",
    "wisig": "openew.data.wisig",
    "electrosense": "openew.data.electrosense",
    "jamshield": "openew.data.jamshield",
    "radioml": "openew.data.radioml",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert public RF datasets to OpenEW-SA artifacts.")
    parser.add_argument("dataset", choices=CONVERTERS, help="Dataset converter to run.")
    parser.add_argument("--config", required=True, help="Path to YAML conversion config.")
    args = parser.parse_args()

    config = load_yaml(args.config)
    module = import_module(CONVERTERS[args.dataset])
    module.convert(config)


if __name__ == "__main__":
    main()
