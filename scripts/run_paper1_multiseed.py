#!/usr/bin/env python
"""Run Paper 1 OpenEW-SA baselines across multiple random seeds."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from statistics import mean, stdev
from typing import Any

import yaml

DEFAULT_CONFIGS = (
    Path("configs/train/tabular_mlp_jamshield.yaml"),
    Path("configs/train/jamshield_domain_holdout.yaml"),
    Path("configs/train/jamshield_reactive_holdout.yaml"),
    Path("configs/train/deepsense_occupancy_mlp.yaml"),
    Path("configs/train/deepsense_day2_holdout_mlp.yaml"),
    Path("configs/train/deepsense_occupancy_iqcnn.yaml"),
    Path("configs/train/electrosense_psd_mlp.yaml"),
    Path("configs/train/electrosense_sensor_holdout_mlp.yaml"),
)
DEFAULT_SEEDS = (0, 1, 2)
DEFAULT_OUTPUT_ROOT = Path("runs") / "multiseed"
DEFAULT_SUMMARY_OUTPUT = Path(r"D:\openew_sa_data\paper1\tables\table_multiseed_summary.csv")
METRIC_NAMES = ("accuracy", "macro_f1", "weighted_f1", "AUROC", "AUPRC")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run selected Paper 1 training configs for multiple random seeds.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--configs",
        nargs="+",
        type=Path,
        default=None,
        metavar="CONFIG",
        help="Training config YAML files to run. Defaults to the Paper 1 config set.",
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Reuse an existing metrics.json instead of rerunning that seed.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    output_root = args.output_root
    summary_rows = []
    config_paths = args.configs if args.configs is not None else list(DEFAULT_CONFIGS)
    for config_path in config_paths:
        resolved_config_path = _resolve_path(repo_root, config_path)
        run_rows = []
        for seed in args.seeds:
            run_rows.append(
                _run_seed(
                    repo_root=repo_root,
                    config_path=resolved_config_path,
                    output_root=output_root,
                    seed=seed,
                    skip_existing=args.skip_existing,
                )
            )
        summary_rows.append(_aggregate_config_runs(resolved_config_path, output_root, run_rows))

    _write_summary_csv(args.summary_output, summary_rows)
    print(f"Wrote {args.summary_output}")


def _run_seed(
    repo_root: Path,
    config_path: Path,
    output_root: Path,
    seed: int,
    skip_existing: bool,
) -> dict[str, Any]:
    config_stem = config_path.stem
    run_output_dir = output_root / config_stem / f"seed_{seed}"
    run_output_dir_for_io = _resolve_path(repo_root, run_output_dir)
    metrics_path = run_output_dir_for_io / "metrics.json"
    run_config_path = run_output_dir_for_io / "config.yaml"

    run_output_dir_for_io.mkdir(parents=True, exist_ok=True)
    config = _read_yaml(config_path)
    config["seed"] = int(seed)
    config["output_dir"] = str(run_output_dir)
    _write_yaml(run_config_path, config)

    if skip_existing and metrics_path.exists():
        print(f"[skip] {config_stem} seed {seed}: {metrics_path}")
    else:
        print(f"[run] {config_stem} seed {seed}")
        _run_training_cli(repo_root, run_config_path)

    metrics = _read_json(metrics_path)
    return {
        "seed": seed,
        "metrics": metrics,
        "run_dir": str(run_output_dir),
        "metrics_path": str(metrics_path),
    }


def _run_training_cli(repo_root: Path, run_config_path: Path) -> None:
    env = os.environ.copy()
    src_path = str(repo_root / "src")
    env["PYTHONPATH"] = src_path + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    command = [
        sys.executable,
        str(repo_root / "scripts" / "train_baseline.py"),
        "--config",
        str(run_config_path),
    ]
    subprocess.run(command, cwd=repo_root, env=env, check=True)


def _aggregate_config_runs(
    config_path: Path,
    output_root: Path,
    run_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    config_stem = config_path.stem
    row: dict[str, Any] = {
        "config": config_stem,
        "config_path": _display_path(config_path),
        "seeds": ";".join(str(run["seed"]) for run in run_rows),
        "n_runs": len(run_rows),
        "run_root": str(output_root / config_stem),
        "metrics_files": json.dumps([run["metrics_path"] for run in run_rows]),
    }
    for metric_name in METRIC_NAMES:
        values = [_metric_value(run["metrics"], metric_name) for run in run_rows]
        values = [value for value in values if value is not None]
        row[f"{metric_name}_mean"] = mean(values) if values else None
        row[f"{metric_name}_std"] = stdev(values) if len(values) > 1 else 0.0 if values else None
        row[f"{metric_name}_min"] = min(values) if values else None
        row[f"{metric_name}_max"] = max(values) if values else None
    return row


def _metric_value(metrics: dict[str, Any], metric_name: str) -> float | None:
    value = metrics.get(metric_name)
    if value is None:
        return None
    return float(value)


def _write_summary_csv(output: Path, rows: list[dict[str, Any]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "config",
        "config_path",
        "seeds",
        "n_runs",
        "run_root",
        "metrics_files",
    ]
    for metric_name in METRIC_NAMES:
        fieldnames.extend(
            [
                f"{metric_name}_mean",
                f"{metric_name}_std",
                f"{metric_name}_min",
                f"{metric_name}_max",
            ]
        )
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return value


def _resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at top level of YAML config: {path}")
    return data


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Expected metrics file was not created: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object in metrics file: {path}")
    return data


if __name__ == "__main__":
    main()
