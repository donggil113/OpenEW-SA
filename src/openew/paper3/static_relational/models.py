"""Pure-PyTorch independent, pairwise, and typed-hypergraph classifiers."""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch import nn

from openew.models.baselines import IQCNN1D


class NonFiniteModelOutput(RuntimeError):
    """Raised when a model emits NaN or infinite logits."""


class TabularNodeEncoder(nn.Module):
    """Paper 1-capacity individual node encoder without batch-composition state."""

    def __init__(self, input_dim: int, hidden_dim: int, dropout: float) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.network(values.flatten(start_dim=1))


@dataclass(frozen=True)
class TorchContextBatch:
    anchor_positions_in_support: torch.Tensor
    member_positions_by_type: dict[str, torch.Tensor]


class StaticRelationalClassifier(nn.Module):
    """M0/M1/M2 classifier with value-agnostic relation-type transformations."""

    def __init__(
        self,
        input_dim: int,
        num_classes: int,
        hidden_dim: int,
        dropout: float,
        model_stage: str,
        relation_types: tuple[str, ...],
    ) -> None:
        super().__init__()
        if model_stage not in {"m0", "m1", "m2"}:
            raise ValueError(f"Unsupported model stage: {model_stage}")
        if model_stage == "m0" and relation_types:
            raise ValueError("M0 cannot receive relation types")
        self.model_stage = model_stage
        self.relation_types = tuple(relation_types)
        # Construct the encoder and head before relation modules so paired seeds
        # initialize the shared M0 capacity identically.
        self.encoder = TabularNodeEncoder(input_dim, hidden_dim, dropout)
        self.classifier = nn.Linear(hidden_dim, num_classes)
        self.relation_transforms = nn.ModuleDict(
            {relation_type: nn.Linear(hidden_dim, hidden_dim, bias=False) for relation_type in relation_types}
        )

    def forward(
        self, support_features: torch.Tensor, context: TorchContextBatch | None = None
    ) -> torch.Tensor:
        support_embeddings = self.encoder(support_features)
        if self.model_stage == "m0":
            logits = self.classifier(support_embeddings)
            _require_finite(logits)
            return logits
        if context is None:
            raise ValueError(f"{self.model_stage} requires a relation context")
        anchors = support_embeddings[context.anchor_positions_in_support]
        updates = torch.zeros_like(anchors)
        available_type_count = torch.zeros(
            (len(anchors), 1), dtype=anchors.dtype, device=anchors.device
        )
        for relation_type in self.relation_types:
            member_positions = context.member_positions_by_type[relation_type]
            valid = member_positions >= 0
            safe_positions = member_positions.clamp_min(0)
            gathered = support_embeddings[safe_positions]
            original_counts = valid.sum(dim=1)
            if self.model_stage == "m1":
                self_positions = context.anchor_positions_in_support.unsqueeze(1)
                valid = valid & (member_positions != self_positions)
            counts = valid.sum(dim=1)
            denominator = counts.clamp_min(1).to(anchors.dtype).unsqueeze(1)
            means = (gathered * valid.unsqueeze(2)).sum(dim=1) / denominator
            active = original_counts >= 2
            if self.model_stage == "m1":
                active &= counts >= 1
            transformed = torch.relu(self.relation_transforms[relation_type](means))
            updates += transformed * active.unsqueeze(1)
            available_type_count += active.to(anchors.dtype).unsqueeze(1)
        updates = updates / available_type_count.clamp_min(1.0)
        logits = self.classifier(anchors + updates)
        _require_finite(logits)
        return logits


def build_classifier(
    dataset: str,
    model_stage: str,
    relation_types: tuple[str, ...],
    input_dim: int,
    num_classes: int,
    hidden_dim: int,
    dropout: float,
) -> nn.Module:
    if dataset == "deepsense":
        if model_stage != "m0" or relation_types:
            raise ValueError("DeepSense is M0-only under the frozen relation audit")
        return IQCNN1D(in_channels=2, num_classes=num_classes, hidden=hidden_dim)
    return StaticRelationalClassifier(
        input_dim=input_dim,
        num_classes=num_classes,
        hidden_dim=hidden_dim,
        dropout=dropout,
        model_stage=model_stage,
        relation_types=relation_types,
    )


def parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def _require_finite(values: torch.Tensor) -> None:
    if not torch.isfinite(values).all():
        raise NonFiniteModelOutput("Model produced NaN or infinite logits")


def relation_update_scale(relation_type_count: int) -> float:
    """Inspectable bound used only for reasoning/tests, not value identity."""

    return 0.0 if relation_type_count <= 0 else 1.0 / math.sqrt(relation_type_count)
