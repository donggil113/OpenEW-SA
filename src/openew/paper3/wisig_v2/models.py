"""Shared-backbone V2 models, DANN, and verified test-time adjustments."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

from openew.paper3.wisig.models import IndependentClassifier, RFBackbone


class GradientReversal(torch.autograd.Function):
    @staticmethod
    def forward(ctx: object, x: torch.Tensor, coefficient: float) -> torch.Tensor:
        ctx.coefficient = coefficient  # type: ignore[attr-defined]
        return x.view_as(x)

    @staticmethod
    def backward(ctx: object, gradient: torch.Tensor) -> tuple[torch.Tensor, None]:
        return -float(ctx.coefficient) * gradient, None  # type: ignore[attr-defined]


class DANNClassifier(nn.Module):
    """Source-only receiver-adversarial baseline; receiver IDs are never inputs."""

    def __init__(self, class_count: int, source_domain_count: int, hidden: int = 64) -> None:
        super().__init__()
        self.backbone = RFBackbone()
        self.classifier = nn.Linear(64, class_count)
        self.domain_discriminator = nn.Sequential(nn.Linear(64, hidden), nn.ReLU(inplace=True), nn.Linear(hidden, source_domain_count))

    def forward(self, x: torch.Tensor, *, reversal: float = 0.0) -> tuple[torch.Tensor, torch.Tensor]:
        embedding = self.backbone(x)
        class_logits = self.classifier(embedding)
        reversed_embedding = GradientReversal.apply(embedding, float(reversal))
        domain_logits = self.domain_discriminator(reversed_embedding)
        if not torch.isfinite(class_logits).all() or not torch.isfinite(domain_logits).all():
            raise FloatingPointError("non-finite DANN output")
        return class_logits, domain_logits


@dataclass
class ContextPrediction:
    logits: torch.Tensor
    attention: torch.Tensor | None


class ReceiverSupportClassifier(nn.Module):
    """Mean/attentive set conditioning with no receiver-value embeddings."""

    def __init__(self, class_count: int, *, attention: bool) -> None:
        super().__init__()
        self.backbone = RFBackbone()
        self.attention = bool(attention)
        self.scorer = nn.Sequential(nn.Linear(64, 32), nn.Tanh(), nn.Linear(32, 1)) if attention else None
        self.fusion = nn.Sequential(nn.Linear(128, 64), nn.ReLU(inplace=True), nn.Dropout(0.2), nn.Linear(64, class_count))

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

    def predict_from_embeddings(
        self,
        anchors: torch.Tensor,
        peers: torch.Tensor,
        peer_mask: torch.Tensor,
    ) -> ContextPrediction:
        if anchors.ndim != 2 or peers.ndim != 3 or peer_mask.shape != peers.shape[:2]:
            raise ValueError("incompatible anchor/support embedding shapes")
        if anchors.shape[0] != peers.shape[0] or anchors.shape[-1] != peers.shape[-1]:
            raise ValueError("anchor/support embedding dimensions differ")
        if self.attention:
            assert self.scorer is not None
            scores = self.scorer(peers).squeeze(-1)
            masked = scores.masked_fill(~peer_mask, -torch.inf)
            maximum = torch.where(peer_mask.any(dim=1), masked.max(dim=1).values, torch.zeros(len(peers), device=peers.device))
            numerators = torch.exp(scores - maximum[:, None]) * peer_mask.to(scores.dtype)
            denominators = numerators.sum(dim=1, keepdim=True)
            weights = torch.where(denominators > 0, numerators / denominators.clamp_min(1e-12), torch.zeros_like(numerators))
        else:
            numerators = peer_mask.to(peers.dtype)
            denominators = numerators.sum(dim=1, keepdim=True)
            weights = torch.where(denominators > 0, numerators / denominators.clamp_min(1.0), torch.zeros_like(numerators))
        context = torch.einsum("bk,bkd->bd", weights, peers)
        logits = self.fusion(torch.cat([anchors, context], dim=-1))
        if not torch.isfinite(logits).all():
            raise FloatingPointError("non-finite receiver-context output")
        return ContextPrediction(logits=logits, attention=weights if self.attention else None)

    def forward(self, anchors: torch.Tensor, peers: torch.Tensor, peer_mask: torch.Tensor) -> ContextPrediction:
        if anchors.ndim != 3 or peers.ndim != 4:
            raise ValueError("expected raw anchors [B,T,2] and peers [B,K,T,2]")
        batch, width = peers.shape[:2]
        anchor_embeddings = self.encode(anchors)
        peer_embeddings = self.encode(peers.reshape(batch * width, *peers.shape[2:])).reshape(batch, width, -1)
        return self.predict_from_embeddings(anchor_embeddings, peer_embeddings, peer_mask)

    def forward_source_episodes(self, x: torch.Tensor, valid_mask: torch.Tensor) -> ContextPrediction:
        """Classify every source anchor using other members of its receiver episode."""

        if x.ndim != 4 or valid_mask.shape != x.shape[:2]:
            raise ValueError("source episode tensor and mask have incompatible shapes")
        episode_count, width = x.shape[:2]
        embeddings = self.encode(x.reshape(episode_count * width, *x.shape[2:])).reshape(episode_count, width, -1)
        peer_mask = valid_mask[:, None, :].expand(-1, width, -1).clone()
        diagonal = torch.eye(width, dtype=torch.bool, device=x.device)[None, :, :]
        peer_mask &= ~diagonal
        peer_embeddings = embeddings[:, None, :, :].expand(-1, width, -1, -1).reshape(episode_count * width, width, -1)
        output = self.predict_from_embeddings(
            embeddings.reshape(episode_count * width, -1),
            peer_embeddings,
            peer_mask.reshape(episode_count * width, width),
        )
        logits = output.logits.reshape(episode_count, width, -1)
        attention = output.attention.reshape(episode_count, width, width) if output.attention is not None else None
        return ContextPrediction(logits=logits, attention=attention)


def trainable_parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def make_model(stage: str, class_count: int, *, source_domain_count: int = 0) -> nn.Module:
    if stage == "P0_WIDE":
        return IndependentClassifier(class_count, wide=True)
    if stage in {"P0", "DG_CORAL", "DG_GROUPDRO", "SOURCE_NORM"}:
        return IndependentClassifier(class_count, wide=False)
    if stage == "DG_DANN":
        if source_domain_count <= 1:
            raise ValueError("DANN needs at least two source receiver domains")
        return DANNClassifier(class_count, source_domain_count)
    if stage in {"P1", "P2"}:
        return ReceiverSupportClassifier(class_count, attention=stage == "P2")
    raise ValueError(f"stage {stage} is derived at inference and has no independently trained model")


@dataclass(frozen=True)
class NormalizationStatistics:
    mean_i: float
    mean_q: float
    rms: float
    sample_count: int

    def validate(self) -> "NormalizationStatistics":
        if self.sample_count <= 0 or not np.isfinite([self.mean_i, self.mean_q, self.rms]).all() or self.rms <= 0:
            raise ValueError("invalid normalization statistics")
        return self


def estimate_iq_normalization(features: np.ndarray, epsilon: float = 1e-8) -> NormalizationStatistics:
    values = np.asarray(features, dtype=np.float64)
    if values.ndim != 3 or values.shape[-1] != 2 or not np.isfinite(values).all():
        raise ValueError("normalization expects finite [N,T,2] features")
    means = values.mean(axis=(0, 1))
    residual = values - means.reshape(1, 1, 2)
    rms = max(float(np.sqrt(np.mean(np.square(residual)))), epsilon)
    return NormalizationStatistics(float(means[0]), float(means[1]), rms, len(values)).validate()


def apply_iq_normalization(features: np.ndarray, statistics: NormalizationStatistics) -> np.ndarray:
    values = np.asarray(features, dtype=np.float32)
    mean = np.asarray([statistics.mean_i, statistics.mean_q], dtype=np.float32).reshape(1, 1, 2)
    result = (values - mean) / np.float32(statistics.rms)
    if not np.isfinite(result).all():
        raise FloatingPointError("normalization produced non-finite values")
    return result


def entropy_from_logits(logits: torch.Tensor) -> torch.Tensor:
    probabilities = torch.softmax(logits, dim=-1)
    return -(probabilities * torch.log(probabilities.clamp_min(1e-12))).sum(dim=-1)


class T3AAdapter:
    """Bounded-support implementation of the official T3A template rule."""

    def __init__(self, classifier: nn.Linear, filter_k: int = 20) -> None:
        if not isinstance(classifier, nn.Linear):
            raise TypeError("T3A requires a linear final classifier")
        if filter_k == 0 or filter_k < -1:
            raise ValueError("filter_k must be positive or -1")
        self.classifier = classifier
        self.filter_k = filter_k

    @torch.no_grad()
    def adapted_weights(self, target_support_embeddings: torch.Tensor) -> torch.Tensor:
        if target_support_embeddings.ndim != 2 or target_support_embeddings.shape[1] != self.classifier.in_features:
            raise ValueError("support embeddings do not match classifier")
        warmup = self.classifier.weight.detach().clone()
        supports = torch.cat([warmup, target_support_embeddings.detach()], dim=0)
        logits = self.classifier(supports)
        pseudo = logits.argmax(dim=1)
        entropy = entropy_from_logits(logits)
        selected: list[torch.Tensor] = []
        for class_index in range(self.classifier.out_features):
            indices = torch.nonzero(pseudo == class_index, as_tuple=False).flatten()
            if len(indices) == 0:
                continue
            indices = indices[torch.argsort(entropy[indices])]
            if self.filter_k != -1:
                indices = indices[: self.filter_k]
            selected.append(indices)
        if not selected:
            raise RuntimeError("T3A support selection is empty")
        keep = torch.cat(selected)
        selected_supports = F.normalize(supports[keep], dim=1)
        one_hot = F.one_hot(pseudo[keep], num_classes=self.classifier.out_features).to(selected_supports.dtype)
        weights = selected_supports.T @ one_hot
        return F.normalize(weights, dim=0)

    @torch.no_grad()
    def predict(self, query_embeddings: torch.Tensor, target_support_embeddings: torch.Tensor) -> torch.Tensor:
        weights = self.adapted_weights(target_support_embeddings)
        logits = query_embeddings @ weights
        if not torch.isfinite(logits).all():
            raise FloatingPointError("T3A produced non-finite logits")
        return logits


def batchnorm_module_count(model: nn.Module) -> int:
    return sum(isinstance(module, (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d)) for module in model.modules())
