"""Model factory for configurable experiments."""

from __future__ import annotations

from typing import Any

from openew.models.baselines import IQCNN1D, MultiTaskTransformer, PSDCNN, PSDMLP, SpectrogramCNN, TabularMLP


def build_model(config: dict[str, Any]):
    """Build a baseline model from a YAML-derived dictionary."""

    name = config["name"]
    kwargs = config.get("kwargs", {})
    if name == "iq_cnn_1d":
        return IQCNN1D(**kwargs)
    if name == "spectrogram_cnn":
        return SpectrogramCNN(**kwargs)
    if name == "psd_mlp":
        return PSDMLP(**kwargs)
    if name == "psd_cnn":
        return PSDCNN(**kwargs)
    if name == "tabular_mlp":
        return TabularMLP(**kwargs)
    if name == "multitask_transformer":
        return MultiTaskTransformer(**kwargs)
    raise ValueError(f"Unknown model name: {name}")
