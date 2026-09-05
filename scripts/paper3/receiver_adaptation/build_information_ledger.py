#!/usr/bin/env python3
"""Render the method information-budget registry as CSV."""

from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from openew.paper3.receiver_adaptation.contracts import information_budget_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    pd.DataFrame(information_budget_rows()).to_csv(temporary, index=False, lineterminator="\n")
    temporary.replace(destination)
    print(destination)


if __name__ == "__main__":
    main()
