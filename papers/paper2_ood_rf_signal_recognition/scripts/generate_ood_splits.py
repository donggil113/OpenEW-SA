#!/usr/bin/env python
"""Generate Paper 2 OOD split manifests from OpenEW-SA metadata.

The script reads a converted OpenEW-SA ``metadata.csv`` file and writes train, validation-ID,
test-ID, and OOD CSV manifests. It does not load feature tensors; model-specific feature loading is
left to the future Paper 2 training pipeline.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML is a project dependency.
    yaml = None

SUPPORTED_PROTOCOLS = ("class_ood", "domain_ood", "hybrid_ood")


@dataclass(frozen=True)
class SplitOptions:
    """Resolved command-line and config values for split generation."""

    metadata_path: Path
    output_dir: Path
    protocol: str
    label_column: str
    domain_column: str
    sample_id_column: str
    known_classes: list[str]
    ood_classes: list[str]
    train_domains: list[str]
    id_domains: list[str]
    ood_domains: list[str]
    validation_fraction: float
    test_fraction: float
    seed: int


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Generate class, domain, or hybrid OOD split manifests from OpenEW-SA metadata.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", type=Path, help="Optional Paper 2 YAML config.")
    parser.add_argument("--metadata", type=Path, help="Path to an OpenEW-SA metadata.csv file.")
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        help="Converted OpenEW-SA artifact directory containing metadata.csv.",
    )
    parser.add_argument("--output-dir", type=Path, help="Directory for generated split CSV files.")
    parser.add_argument("--protocol", choices=SUPPORTED_PROTOCOLS, help="OOD split protocol.")
    parser.add_argument("--label-column", help="Metadata label column used for recognition.")
    parser.add_argument("--domain-column", help="Metadata domain column used for domain OOD.")
    parser.add_argument("--sample-id-column", help="Metadata sample identifier column.")
    parser.add_argument(
        "--known-classes",
        action="append",
        help="Known class labels. Comma-separated values may be repeated.",
    )
    parser.add_argument(
        "--ood-classes",
        action="append",
        help="OOD class labels. Comma-separated values may be repeated.",
    )
    parser.add_argument(
        "--train-domains",
        action="append",
        help="Training domain identifiers. Comma-separated values may be repeated.",
    )
    parser.add_argument(
        "--id-domains",
        action="append",
        help="Optional ID evaluation domains. Defaults to train domains.",
    )
    parser.add_argument(
        "--ood-domains",
        action="append",
        help="OOD domain identifiers. Comma-separated values may be repeated.",
    )
    parser.add_argument("--validation-fraction", type=float, help="Fraction of ID rows for val-ID.")
    parser.add_argument("--test-fraction", type=float, help="Fraction of ID rows for test-ID.")
    parser.add_argument("--seed", type=int, help="Random seed for deterministic shuffling.")
    return parser.parse_args()


def main() -> None:
    """Run split generation and write manifests."""

    args = parse_args()
    config = _load_config(args.config)
    options = _resolve_options(args, config)
    metadata = _read_metadata(options.metadata_path)
    splits, summary = build_splits(metadata, options)
    _write_splits(splits, summary, options)


def build_splits(metadata: pd.DataFrame, options: SplitOptions) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    """Build protocol-specific split frames and a JSON-serializable summary."""

    _require_columns(metadata, [options.label_column, options.sample_id_column])
    if options.protocol in {"domain_ood", "hybrid_ood"}:
        _require_columns(metadata, [options.domain_column])

    if options.protocol == "class_ood":
        splits, details = _build_class_ood(metadata, options)
    elif options.protocol == "domain_ood":
        splits, details = _build_domain_ood(metadata, options)
    elif options.protocol == "hybrid_ood":
        splits, details = _build_hybrid_ood(metadata, options)
    else:
        raise ValueError(f"Unsupported protocol: {options.protocol}")

    summary = {
        "protocol": options.protocol,
        "metadata_path": str(options.metadata_path),
        "label_column": options.label_column,
        "domain_column": options.domain_column,
        "sample_id_column": options.sample_id_column,
        "seed": options.seed,
        "counts": {name: int(len(frame)) for name, frame in splits.items()},
        **details,
    }
    return splits, summary


def _build_class_ood(
    metadata: pd.DataFrame,
    options: SplitOptions,
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    labels = _text_series(metadata[options.label_column])
    known_classes, ood_classes = _resolve_label_sets(labels, options.known_classes, options.ood_classes)

    id_pool = metadata.loc[labels.isin(known_classes)].copy()
    ood_pool = metadata.loc[labels.isin(ood_classes)].copy()
    _validate_required_pool("ID known-class", id_pool)
    _validate_required_pool("OOD class", ood_pool)

    train, val_id, test_id = _split_id_pool(
        id_pool,
        options.validation_fraction,
        options.test_fraction,
        options.seed,
    )
    splits = {
        "train": _annotate_split(train, "train", 0),
        "val_id": _annotate_split(val_id, "val_id", 0),
        "test_id": _annotate_split(test_id, "test_id", 0),
        "ood": _annotate_split(_shuffle(ood_pool, options.seed + 17), "ood", 1),
    }
    details = {
        "known_classes": known_classes,
        "ood_classes": ood_classes,
        "ignored_rows": int((~labels.isin(known_classes + ood_classes)).sum()),
    }
    return splits, details


def _build_domain_ood(
    metadata: pd.DataFrame,
    options: SplitOptions,
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    labels = _text_series(metadata[options.label_column])
    domains = _text_series(metadata[options.domain_column])
    candidate = metadata.loc[labels.ne("") & domains.ne("")].copy()
    candidate_domains = _text_series(candidate[options.domain_column])
    train_domains, id_domains, ood_domains = _resolve_domain_sets(
        candidate_domains,
        options.train_domains,
        options.id_domains,
        options.ood_domains,
    )

    train_pool = candidate.loc[candidate_domains.isin(train_domains)].copy()
    id_eval_pool = candidate.loc[candidate_domains.isin(id_domains)].copy()
    ood_pool = candidate.loc[candidate_domains.isin(ood_domains)].copy()
    _validate_required_pool("training domain", train_pool)
    _validate_required_pool("ID evaluation domain", id_eval_pool)
    _validate_required_pool("OOD domain", ood_pool)

    if set(id_domains) == set(train_domains):
        train, val_id, test_id = _split_id_pool(
            train_pool,
            options.validation_fraction,
            options.test_fraction,
            options.seed,
        )
    else:
        train = _shuffle(train_pool, options.seed)
        val_id, test_id = _split_eval_pool(
            id_eval_pool,
            options.validation_fraction,
            options.test_fraction,
            options.seed + 11,
        )

    splits = {
        "train": _annotate_split(train, "train", 0),
        "val_id": _annotate_split(val_id, "val_id", 0),
        "test_id": _annotate_split(test_id, "test_id", 0),
        "ood": _annotate_split(_shuffle(ood_pool, options.seed + 17), "ood", 1),
    }
    details = {
        "train_domains": train_domains,
        "id_domains": id_domains,
        "ood_domains": ood_domains,
        "ignored_rows": int(len(metadata) - len(candidate)),
    }
    return splits, details


def _build_hybrid_ood(
    metadata: pd.DataFrame,
    options: SplitOptions,
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    labels = _text_series(metadata[options.label_column])
    domains = _text_series(metadata[options.domain_column])
    known_classes, ood_classes = _resolve_label_sets(labels, options.known_classes, options.ood_classes)
    train_domains, id_domains, ood_domains = _resolve_domain_sets(
        domains,
        options.train_domains,
        options.id_domains,
        options.ood_domains,
    )

    known_mask = labels.isin(known_classes)
    train_mask = known_mask & domains.isin(train_domains)
    id_eval_mask = known_mask & domains.isin(id_domains)
    ood_mask = labels.isin(ood_classes) | domains.isin(ood_domains)

    train_pool = metadata.loc[train_mask].copy()
    id_eval_pool = metadata.loc[id_eval_mask].copy()
    ood_pool = metadata.loc[ood_mask].copy()
    _validate_required_pool("hybrid training", train_pool)
    _validate_required_pool("hybrid ID evaluation", id_eval_pool)
    _validate_required_pool("hybrid OOD", ood_pool)

    if set(id_domains) == set(train_domains):
        train, val_id, test_id = _split_id_pool(
            train_pool,
            options.validation_fraction,
            options.test_fraction,
            options.seed,
        )
    else:
        train = _shuffle(train_pool, options.seed)
        val_id, test_id = _split_eval_pool(
            id_eval_pool,
            options.validation_fraction,
            options.test_fraction,
            options.seed + 11,
        )

    splits = {
        "train": _annotate_split(train, "train", 0),
        "val_id": _annotate_split(val_id, "val_id", 0),
        "test_id": _annotate_split(test_id, "test_id", 0),
        "ood": _annotate_split(_shuffle(ood_pool, options.seed + 17), "ood", 1),
    }
    details = {
        "known_classes": known_classes,
        "ood_classes": ood_classes,
        "train_domains": train_domains,
        "id_domains": id_domains,
        "ood_domains": ood_domains,
        "ignored_rows": int((~(train_mask | id_eval_mask | ood_mask)).sum()),
    }
    return splits, details


def _resolve_options(args: argparse.Namespace, config: dict[str, Any]) -> SplitOptions:
    protocol = args.protocol or _config_value(config, ("split", "protocol"), ("protocol", "name")) or "class_ood"
    if protocol not in SUPPORTED_PROTOCOLS:
        supported = ", ".join(SUPPORTED_PROTOCOLS)
        raise ValueError(f"Unsupported protocol '{protocol}'. Expected one of: {supported}")

    metadata_path = _resolve_metadata_path(args, config)
    output_dir = args.output_dir or _path_config(config, ("outputs", "split_dir"))
    if output_dir is None:
        output_dir = Path("papers") / "paper2_ood_rf_signal_recognition" / "splits" / protocol

    return SplitOptions(
        metadata_path=metadata_path,
        output_dir=Path(output_dir),
        protocol=protocol,
        label_column=args.label_column
        or _config_value(config, ("target", "label_column"), ("split", "label_column"))
        or "modulation_label",
        domain_column=args.domain_column
        or _config_value(config, ("target", "domain_column"), ("split", "domain_column"))
        or "domain_id",
        sample_id_column=args.sample_id_column
        or _config_value(config, ("target", "sample_id_column"), ("split", "sample_id_column"))
        or "sample_id",
        known_classes=_list_option(args.known_classes, _config_value(config, ("split", "known_classes"))),
        ood_classes=_list_option(args.ood_classes, _config_value(config, ("split", "ood_classes"))),
        train_domains=_list_option(args.train_domains, _config_value(config, ("split", "train_domains"))),
        id_domains=_list_option(args.id_domains, _config_value(config, ("split", "id_domains"))),
        ood_domains=_list_option(args.ood_domains, _config_value(config, ("split", "ood_domains"))),
        validation_fraction=float(
            args.validation_fraction
            if args.validation_fraction is not None
            else _config_value(config, ("split", "validation_fraction"), default=0.15)
        ),
        test_fraction=float(
            args.test_fraction
            if args.test_fraction is not None
            else _config_value(config, ("split", "test_fraction"), default=0.20)
        ),
        seed=int(args.seed if args.seed is not None else _config_value(config, ("split", "seed"), default=42)),
    )


def _resolve_metadata_path(args: argparse.Namespace, config: dict[str, Any]) -> Path:
    if args.metadata is not None:
        return args.metadata
    config_metadata = _path_config(config, ("artifacts", "metadata"), ("metadata",))
    if config_metadata is not None:
        return config_metadata
    artifact_dir = args.artifact_dir or _path_config(config, ("artifacts", "artifact_dir"), ("artifact_dir",))
    if artifact_dir is None:
        raise ValueError("Provide --metadata, --artifact-dir, or an artifacts.artifact_dir config value.")
    metadata_file = _config_value(config, ("artifacts", "metadata_file"), default="metadata.csv")
    return Path(artifact_dir) / str(metadata_file)


def _load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    if yaml is None:
        raise RuntimeError("PyYAML is required to read --config files.")
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Config must be a YAML mapping: {path}")
    return loaded


def _read_metadata(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Metadata CSV not found: {path}")
    metadata = pd.read_csv(path)
    if metadata.empty:
        raise ValueError(f"Metadata CSV is empty: {path}")
    return metadata


def _require_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Metadata is missing required columns: {missing}")


def _resolve_label_sets(
    labels: pd.Series,
    known_classes: list[str],
    ood_classes: list[str],
) -> tuple[list[str], list[str]]:
    available = sorted(value for value in labels.dropna().unique().tolist() if value)
    if not known_classes and not ood_classes:
        raise ValueError("Class OOD protocols require --known-classes, --ood-classes, or config values.")
    if known_classes and not ood_classes:
        ood_classes = [label for label in available if label not in set(known_classes)]
    if ood_classes and not known_classes:
        known_classes = [label for label in available if label not in set(ood_classes)]
    _validate_members("known_classes", known_classes, available)
    _validate_members("ood_classes", ood_classes, available)
    overlap = sorted(set(known_classes) & set(ood_classes))
    if overlap:
        raise ValueError(f"Known and OOD classes overlap: {overlap}")
    if not known_classes or not ood_classes:
        raise ValueError("Resolved known and OOD class sets must both be non-empty.")
    return known_classes, ood_classes


def _resolve_domain_sets(
    domains: pd.Series,
    train_domains: list[str],
    id_domains: list[str],
    ood_domains: list[str],
) -> tuple[list[str], list[str], list[str]]:
    available = sorted(value for value in domains.dropna().unique().tolist() if value)
    if not train_domains and not ood_domains:
        raise ValueError("Domain OOD protocols require --train-domains, --ood-domains, or config values.")
    if train_domains and not ood_domains:
        ood_domains = [domain for domain in available if domain not in set(train_domains)]
    if ood_domains and not train_domains:
        train_domains = [domain for domain in available if domain not in set(ood_domains)]
    if not id_domains:
        id_domains = list(train_domains)
    _validate_members("train_domains", train_domains, available)
    _validate_members("id_domains", id_domains, available)
    _validate_members("ood_domains", ood_domains, available)
    overlap = sorted(set(train_domains) & set(ood_domains))
    if overlap:
        raise ValueError(f"Train and OOD domains overlap: {overlap}")
    if not train_domains or not id_domains or not ood_domains:
        raise ValueError("Resolved train, ID, and OOD domain sets must be non-empty.")
    return train_domains, id_domains, ood_domains


def _validate_members(name: str, values: list[str], available: list[str]) -> None:
    missing = sorted(set(values) - set(available))
    if missing:
        raise ValueError(f"{name} values not found in metadata: {missing}. Available values: {available}")


def _split_id_pool(
    frame: pd.DataFrame,
    validation_fraction: float,
    test_fraction: float,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    shuffled = _shuffle(frame, seed)
    n_rows = len(shuffled)
    n_val, n_test = _split_counts(n_rows, validation_fraction, test_fraction)
    test = shuffled.iloc[:n_test].copy()
    val = shuffled.iloc[n_test : n_test + n_val].copy()
    train = shuffled.iloc[n_test + n_val :].copy()
    return train, val, test


def _split_eval_pool(
    frame: pd.DataFrame,
    validation_fraction: float,
    test_fraction: float,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    shuffled = _shuffle(frame, seed)
    n_rows = len(shuffled)
    n_val, n_test = _split_counts(n_rows, validation_fraction, test_fraction)
    if n_val + n_test == 0:
        return shuffled.iloc[0:0].copy(), shuffled.copy()
    test = shuffled.iloc[:n_test].copy()
    val = shuffled.iloc[n_test : n_test + n_val].copy()
    return val, test


def _split_counts(n_rows: int, validation_fraction: float, test_fraction: float) -> tuple[int, int]:
    _validate_fraction("validation_fraction", validation_fraction)
    _validate_fraction("test_fraction", test_fraction)
    if validation_fraction + test_fraction >= 1.0:
        raise ValueError("validation_fraction + test_fraction must be less than 1.0")
    if n_rows < 3:
        return 0, 0
    n_val = int(round(n_rows * validation_fraction))
    n_test = int(round(n_rows * test_fraction))
    if validation_fraction > 0:
        n_val = max(1, n_val)
    if test_fraction > 0:
        n_test = max(1, n_test)
    while n_val + n_test >= n_rows:
        if n_test >= n_val and n_test > 0:
            n_test -= 1
        elif n_val > 0:
            n_val -= 1
        else:
            break
    return n_val, n_test


def _validate_fraction(name: str, value: float) -> None:
    if value < 0.0 or value >= 1.0:
        raise ValueError(f"{name} must be in [0, 1): {value}")


def _annotate_split(frame: pd.DataFrame, split_name: str, ood_label: int) -> pd.DataFrame:
    annotated = frame.copy()
    annotated["paper2_split"] = split_name
    annotated["ood_label"] = int(ood_label)
    return annotated


def _validate_required_pool(name: str, frame: pd.DataFrame) -> None:
    if frame.empty:
        raise ValueError(f"{name} pool is empty; adjust class/domain selections.")


def _shuffle(frame: pd.DataFrame, seed: int) -> pd.DataFrame:
    return frame.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def _text_series(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str)


def _write_splits(splits: dict[str, pd.DataFrame], summary: dict[str, Any], options: SplitOptions) -> None:
    options.output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in splits.items():
        frame.to_csv(options.output_dir / f"{name}.csv", index=False)
    combined = pd.concat(splits.values(), ignore_index=True)
    combined.to_csv(options.output_dir / "all_splits.csv", index=False)
    with (options.output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


def _list_option(cli_values: list[str] | None, config_value: Any) -> list[str]:
    source = cli_values if cli_values is not None else config_value
    if source is None:
        return []
    if isinstance(source, str):
        source = [source]
    values: list[str] = []
    for item in source:
        if item is None:
            continue
        values.extend(part.strip() for part in str(item).split(",") if part.strip())
    return values


def _path_config(config: dict[str, Any], *paths: tuple[str, ...]) -> Path | None:
    value = _config_value(config, *paths)
    return Path(value) if value else None


def _config_value(
    config: dict[str, Any],
    *paths: tuple[str, ...],
    default: Any | None = None,
) -> Any:
    for path in paths:
        current: Any = config
        for key in path:
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]
        if current not in (None, ""):
            return current
    return default


if __name__ == "__main__":
    main()
