"""Conversion helpers for bounded typed-hypergraph context tensors."""

from __future__ import annotations

import torch

from openew.paper3.static_relational.graph import ContextBatch
from openew.paper3.static_relational.models import TorchContextBatch


def to_torch_context(context: ContextBatch, device: torch.device) -> TorchContextBatch:
    return TorchContextBatch(
        anchor_positions_in_support=torch.as_tensor(
            context.anchor_positions_in_support, dtype=torch.long, device=device
        ),
        member_positions_by_type={
            relation_type: torch.as_tensor(values, dtype=torch.long, device=device)
            for relation_type, values in context.member_positions_by_type.items()
        },
    )
