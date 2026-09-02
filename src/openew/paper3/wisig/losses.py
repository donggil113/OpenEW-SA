"""Source-only DG losses selected before held-out evaluation."""

from __future__ import annotations

import itertools

import torch
import torch.nn.functional as F


def covariance(features: torch.Tensor) -> torch.Tensor:
    if features.ndim != 2 or len(features) < 2:
        raise ValueError("covariance needs at least two feature rows")
    centered = features - features.mean(dim=0, keepdim=True)
    return centered.T @ centered / (len(features) - 1)


def source_coral_loss(features: torch.Tensor, domain_codes: torch.Tensor) -> torch.Tensor:
    """Pairwise covariance alignment among source receiver groups only."""

    matrices = []
    for domain in torch.unique(domain_codes):
        subset = features[domain_codes == domain]
        if len(subset) >= 2:
            matrices.append(covariance(subset))
    if len(matrices) < 2:
        return features.sum() * 0.0
    losses = [torch.mean(torch.square(left - right)) for left, right in itertools.combinations(matrices, 2)]
    return torch.stack(losses).mean()


class GroupDROState:
    def __init__(self, group_count: int, eta: float = 0.01, device: torch.device | str = "cpu") -> None:
        if group_count <= 0 or eta <= 0:
            raise ValueError("invalid GroupDRO configuration")
        self.eta = eta
        self.weights = torch.ones(group_count, device=device) / group_count

    def objective(self, per_sample_loss: torch.Tensor, group_codes: torch.Tensor) -> torch.Tensor:
        group_losses = torch.zeros_like(self.weights)
        present = torch.zeros_like(self.weights, dtype=torch.bool)
        for group in torch.unique(group_codes):
            index = int(group.item())
            group_losses[index] = per_sample_loss[group_codes == group].mean()
            present[index] = True
        with torch.no_grad():
            self.weights[present] *= torch.exp(self.eta * group_losses[present].detach())
            self.weights /= self.weights.sum().clamp_min(1e-12)
        effective = self.weights * present.to(self.weights.dtype)
        effective /= effective.sum().clamp_min(1e-12)
        return torch.sum(effective * group_losses)
