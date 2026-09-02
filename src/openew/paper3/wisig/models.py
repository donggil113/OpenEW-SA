"""Shared-backbone independent and static receiver-context WiSig models."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


class ResidualBlock1d(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, stride: int = 1) -> None:
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels, out_channels, 5, stride=stride, padding=2, bias=False)
        self.norm1 = nn.GroupNorm(4 if out_channels >= 4 else 1, out_channels)
        self.conv2 = nn.Conv1d(out_channels, out_channels, 3, padding=1, bias=False)
        self.norm2 = nn.GroupNorm(4 if out_channels >= 4 else 1, out_channels)
        self.skip = (
            nn.Identity()
            if in_channels == out_channels and stride == 1
            else nn.Conv1d(in_channels, out_channels, 1, stride=stride, bias=False)
        )
        self.activation = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = self.skip(x)
        x = self.activation(self.norm1(self.conv1(x)))
        x = self.norm2(self.conv2(x))
        return self.activation(x + residual)


class RFBackbone(nn.Module):
    """Compact 1-D residual encoder for 256 complex I/Q samples."""

    embedding_dim = 64

    def __init__(self) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Conv1d(2, 16, 7, stride=2, padding=3, bias=False),
            nn.GroupNorm(4, 16),
            nn.ReLU(inplace=True),
            ResidualBlock1d(16, 32, stride=2),
            ResidualBlock1d(32, 64, stride=2),
            ResidualBlock1d(64, 64),
            nn.AdaptiveAvgPool1d(1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim != 3 or x.shape[-1] != 2:
            raise ValueError(f"expected [batch, samples, 2], got {tuple(x.shape)}")
        return self.network(x.transpose(1, 2)).squeeze(-1)


class IndependentClassifier(nn.Module):
    def __init__(self, class_count: int, *, wide: bool = False) -> None:
        super().__init__()
        self.backbone = RFBackbone()
        self.wide = wide
        self.classifier = (
            nn.Sequential(nn.Linear(64, 147), nn.ReLU(inplace=True), nn.Dropout(0.2), nn.Linear(147, class_count))
            if wide
            else nn.Linear(64, class_count)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        logits = self.classifier(self.backbone(x))
        if not torch.isfinite(logits).all():
            raise FloatingPointError("non-finite model output")
        return logits


@dataclass
class ContextOutput:
    logits: torch.Tensor
    attention_weights: torch.Tensor | None


class ReceiverContextClassifier(nn.Module):
    def __init__(self, class_count: int, *, attention: bool) -> None:
        super().__init__()
        self.backbone = RFBackbone()
        self.attention = attention
        self.scorer = (
            nn.Sequential(nn.Linear(64, 32), nn.Tanh(), nn.Linear(32, 1))
            if attention
            else None
        )
        self.fusion = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(64, class_count),
        )

    def forward(
        self,
        x: torch.Tensor,
        valid_mask: torch.Tensor,
        context_mask: torch.Tensor,
    ) -> ContextOutput:
        if x.ndim != 4 or valid_mask.shape != x.shape[:2] or context_mask.shape != x.shape[:2]:
            raise ValueError("episode tensor and masks have incompatible shapes")
        batch, width = x.shape[:2]
        embeddings = self.backbone(x.reshape(batch * width, *x.shape[2:])).reshape(batch, width, -1)
        eligible = valid_mask & context_mask
        if self.attention:
            assert self.scorer is not None
            scores = self.scorer(embeddings).squeeze(-1)
            masked_scores = scores.masked_fill(~eligible, -torch.inf)
            maximum = torch.where(eligible.any(dim=1), masked_scores.max(dim=1).values, torch.zeros(batch, device=x.device))
            numerators = torch.exp(scores - maximum[:, None]) * eligible.to(scores.dtype)
            denominators = numerators.sum(dim=1, keepdim=True)
            weights = torch.where(denominators > 0, numerators / denominators.clamp_min(1e-12), torch.zeros_like(numerators))
        else:
            numerators = eligible.to(embeddings.dtype)
            denominators = numerators.sum(dim=1, keepdim=True)
            weights = torch.where(denominators > 0, numerators / denominators.clamp_min(1.0), torch.zeros_like(numerators))
        context = torch.einsum("bc,bcd->bd", weights, embeddings)
        context = context[:, None, :].expand(-1, width, -1)
        logits = self.fusion(torch.cat([embeddings, context], dim=-1))
        if not torch.isfinite(logits).all():
            raise FloatingPointError("non-finite context model output")
        return ContextOutput(logits=logits, attention_weights=weights if self.attention else None)


def trainable_parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def capacity_match_report(class_count: int) -> dict[str, float | int | bool]:
    wide = trainable_parameter_count(IndependentClassifier(class_count, wide=True))
    attention = trainable_parameter_count(ReceiverContextClassifier(class_count, attention=True))
    relative = abs(wide - attention) / attention
    return {
        "p0_wide_parameters": wide,
        "p2_parameters": attention,
        "relative_difference": relative,
        "within_five_percent": relative <= 0.05,
    }
