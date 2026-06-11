"""PyTorch baseline models for OpenEW-SA experiments."""

from __future__ import annotations

import torch
from torch import nn


class IQCNN1D(nn.Module):
    """Compact 1D CNN for I/Q sequences shaped as ``[batch, channels, length]``."""

    def __init__(self, in_channels: int = 2, num_classes: int = 2, hidden: int = 128) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(in_channels, 64, kernel_size=7, padding=3),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(64, hidden, kernel_size=5, padding=2),
            nn.BatchNorm1d(hidden),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.classifier = nn.Linear(hidden, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.encoder(x).squeeze(-1))


class SpectrogramCNN(nn.Module):
    """Small 2D CNN for time-frequency spectrogram inputs."""

    def __init__(self, in_channels: int = 1, num_classes: int = 2, hidden: int = 128) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.classifier = nn.Sequential(nn.Flatten(), nn.Linear(64, hidden), nn.ReLU(), nn.Linear(hidden, num_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.encoder(x))


class PSDMLP(nn.Module):
    """MLP baseline for flattened PSD vectors."""

    def __init__(self, input_dim: int, num_classes: int = 2, hidden: int = 256) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden, hidden // 2),
            nn.ReLU(),
            nn.Linear(hidden // 2, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x.flatten(start_dim=1))


class PSDCNN(nn.Module):
    """1D CNN baseline for PSD traces."""

    def __init__(self, in_channels: int = 1, num_classes: int = 2, hidden: int = 128) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(in_channels, 64, kernel_size=9, padding=4),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(64, hidden, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.classifier = nn.Linear(hidden, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim == 2:
            x = x.unsqueeze(1)
        return self.classifier(self.encoder(x).squeeze(-1))


class TabularMLP(nn.Module):
    """MLP baseline for JamShield-style tabular metrics."""

    def __init__(self, input_dim: int, num_classes: int = 2, hidden: int = 128) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.BatchNorm1d(input_dim),
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x.flatten(start_dim=1))


class MultiTaskTransformer(nn.Module):
    """Transformer encoder with heads for modulation, occupancy, abnormal event, situation, and threat."""

    def __init__(
        self,
        input_dim: int,
        num_modulations: int = 12,
        num_occupancy: int = 2,
        num_events: int = 4,
        num_situations: int = 4,
        num_threat_levels: int = 5,
        d_model: int = 128,
        nhead: int = 4,
        num_layers: int = 2,
    ) -> None:
        super().__init__()
        self.projection = nn.Linear(input_dim, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=4 * d_model,
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.heads = nn.ModuleDict(
            {
                "modulation": nn.Linear(d_model, num_modulations),
                "occupancy": nn.Linear(d_model, num_occupancy),
                "abnormal_event": nn.Linear(d_model, num_events),
                "situation": nn.Linear(d_model, num_situations),
                "threat": nn.Linear(d_model, num_threat_levels),
            }
        )

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        if x.ndim == 2:
            x = x.unsqueeze(1)
        encoded = self.encoder(self.projection(x))
        pooled = encoded.mean(dim=1)
        return {name: head(pooled) for name, head in self.heads.items()}
