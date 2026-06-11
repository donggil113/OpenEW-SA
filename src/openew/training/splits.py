"""Dataset split helpers for OpenEW-SA training and evaluation."""

from __future__ import annotations

import warnings
from typing import Any

import pandas as pd

SPLIT_RANDOM = "random"
SPLIT_DOMAIN_HOLDOUT = "domain_holdout"
SPLIT_JAMMER_TYPE_HOLDOUT = "jammer_type_holdout"
SUPPORTED_SPLIT_STRATEGIES = {
    SPLIT_RANDOM,
    SPLIT_DOMAIN_HOLDOUT,
    SPLIT_JAMMER_TYPE_HOLDOUT,
}


def infer_jammer_type(domain_id: Any) -> str:
    """Infer a coarse JamShield jammer type from a source CSV stem."""

    text = "" if pd.isna(domain_id) else str(domain_id).lower()
    if text.startswith("data_benign"):
        return "benign"
    if text.startswith("constant_jammer"):
        return "constant"
    if text.startswith("random_jammer"):
        return "random"
    if text.startswith("reactive_jammer"):
        return "reactive"
    return "unknown"


def build_holdout_split_indices(metadata: pd.DataFrame, config: dict[str, Any]) -> tuple[list[int], list[int]] | None:
    """Return train/validation indices for configured holdout strategies.

    Random splitting is intentionally left to the existing torch ``random_split`` path, so this
    function returns ``None`` when ``split_strategy`` is ``random`` or unset.
    """

    strategy = config.get("split_strategy", SPLIT_RANDOM)
    if strategy not in SUPPORTED_SPLIT_STRATEGIES:
        supported = ", ".join(sorted(SUPPORTED_SPLIT_STRATEGIES))
        raise ValueError(f"Unsupported split_strategy '{strategy}'. Expected one of: {supported}")
    if strategy == SPLIT_RANDOM:
        return None
    if strategy == SPLIT_DOMAIN_HOLDOUT:
        holdout_mask = _domain_holdout_mask(
            metadata,
            config.get("holdout_domains", []),
            config.get("holdout_benign_domains", []),
        )
    else:
        holdout_mask = _jammer_type_holdout_mask(
            metadata,
            config.get("holdout_jammer_types", []),
            config.get("holdout_benign_domains", []),
        )

    val_indices = [index for index, held_out in enumerate(holdout_mask.tolist()) if held_out]
    train_indices = [index for index, held_out in enumerate(holdout_mask.tolist()) if not held_out]
    _validate_split(strategy, train_indices, val_indices)
    return train_indices, val_indices


def _domain_holdout_mask(
    metadata: pd.DataFrame,
    holdout_domains: list[str],
    holdout_benign_domains: list[str],
) -> pd.Series:
    if "domain_id" not in metadata.columns:
        raise ValueError("domain_holdout split requires metadata column: domain_id")
    if not holdout_domains:
        raise ValueError("domain_holdout split requires non-empty holdout_domains")
    holdout_set = {str(domain) for domain in holdout_domains + holdout_benign_domains}
    return metadata["domain_id"].fillna("").astype(str).isin(holdout_set)


def _jammer_type_holdout_mask(
    metadata: pd.DataFrame,
    holdout_jammer_types: list[str],
    holdout_benign_domains: list[str],
) -> pd.Series:
    if "domain_id" not in metadata.columns:
        raise ValueError("jammer_type_holdout split requires metadata column: domain_id")
    if not holdout_jammer_types:
        raise ValueError("jammer_type_holdout split requires non-empty holdout_jammer_types")
    holdout_set = {str(jammer_type).lower() for jammer_type in holdout_jammer_types}
    jammer_mask = metadata["domain_id"].map(infer_jammer_type).isin(holdout_set)
    benign_mask = metadata["domain_id"].fillna("").astype(str).isin({str(domain) for domain in holdout_benign_domains})
    holdout_mask = jammer_mask | benign_mask
    if not holdout_benign_domains and not _contains_normal_samples(metadata.loc[holdout_mask]):
        warnings.warn(
            "jammer_type_holdout validation contains no normal samples; set holdout_benign_domains "
            "for balanced binary metrics.",
            stacklevel=2,
        )
    return holdout_mask


def _contains_normal_samples(metadata: pd.DataFrame) -> bool:
    if "abnormal_event_label" in metadata.columns:
        return metadata["abnormal_event_label"].fillna("").astype(str).str.lower().eq("normal").any()
    if "situation_label" in metadata.columns:
        return metadata["situation_label"].fillna("").astype(str).str.lower().eq("normal").any()
    return metadata["domain_id"].map(infer_jammer_type).eq("benign").any()


def _validate_split(strategy: str, train_indices: list[int], val_indices: list[int]) -> None:
    if not train_indices:
        raise ValueError(f"{strategy} produced an empty training split")
    if not val_indices:
        raise ValueError(f"{strategy} produced an empty validation/evaluation split")
