#!/usr/bin/env python
"""Create the Paper 1 OpenEW-SA pipeline overview figure."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

DEFAULT_OUTPUT = Path(r"D:\openew_sa_data\paper1\figures\figure_pipeline_overview.png")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create the Paper 1 OpenEW-SA pipeline overview figure.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path)
    parser.add_argument("--dpi", default=300, type=int)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig = _build_figure()
    fig.savefig(args.output, dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {args.output}")


def _build_figure() -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12.0, 6.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.axis("off")

    colors = {
        "datasets": "#DCE9F7",
        "converters": "#E5F3E4",
        "artifacts": "#FFF2CC",
        "models": "#F7E3D3",
        "evaluation": "#E8E0F5",
        "outputs": "#E2F0F0",
        "future": "#F1F1F1",
    }

    boxes = {
        "datasets": _box(
            ax,
            xy=(0.45, 4.6),
            text="Public RF datasets\nJamShield\nDeepSense\nElectroSense",
            color=colors["datasets"],
        ),
        "converters": _box(
            ax,
            xy=(3.0, 4.6),
            text="Dataset-specific\nconverters\njamshield.py\ndeepsense.py\nelectrosense.py",
            color=colors["converters"],
        ),
        "artifacts": _box(
            ax,
            xy=(5.55, 4.6),
            text="Unified artifacts\nmetadata.csv\nfeatures.npy / .pt\nlabels.json",
            color=colors["artifacts"],
            width=2.15,
        ),
        "models": _box(
            ax,
            xy=(8.25, 4.6),
            text="Baseline models\nTabular MLP\nIQ-CNN\nPSD MLP",
            color=colors["models"],
            width=2.15,
        ),
        "evaluation": _box(
            ax,
            xy=(8.25, 1.9),
            text="Domain-aware\nevaluation\nscenario holdout\nday holdout\nsensor holdout",
            color=colors["evaluation"],
            width=2.15,
        ),
        "outputs": _box(
            ax,
            xy=(5.55, 1.9),
            text="Paper outputs\nDataset table\nBaseline table\nDomain holdout table",
            color=colors["outputs"],
            width=2.15,
        ),
        "future": _box(
            ax,
            xy=(3.0, 1.9),
            text="Future extension\nNeuro-symbolic\ndynamic hypergraph\nreasoning",
            color=colors["future"],
            width=2.15,
        ),
    }

    _arrow(ax, boxes["datasets"], boxes["converters"], "right")
    _arrow(ax, boxes["converters"], boxes["artifacts"], "right")
    _arrow(ax, boxes["artifacts"], boxes["models"], "right")
    _arrow(ax, boxes["models"], boxes["evaluation"], "down")
    _arrow(ax, boxes["evaluation"], boxes["outputs"], "left")
    _arrow(ax, boxes["artifacts"], boxes["future"], "down_left", dashed=True)
    _arrow(ax, boxes["outputs"], boxes["future"], "left", dashed=True)

    ax.text(
        6,
        6.62,
        "OpenEW-SA Paper 1 Workflow",
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
    )
    ax.text(
        6,
        0.55,
        "Unified metadata links datasets, domains, models, evaluations, and paper-ready evidence.",
        ha="center",
        va="center",
        fontsize=9,
        color="#4A4A4A",
    )
    return fig


def _box(
    ax: plt.Axes,
    *,
    xy: tuple[float, float],
    text: str,
    color: str,
    width: float = 2.05,
    height: float = 1.25,
) -> tuple[float, float, float, float]:
    x, y = xy
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.045,rounding_size=0.08",
        facecolor=color,
        edgecolor="#2E2E2E",
        linewidth=1.0,
    )
    ax.add_patch(patch)
    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=8.8,
        linespacing=1.22,
    )
    return x, y, width, height


def _arrow(
    ax: plt.Axes,
    start_box: tuple[float, float, float, float],
    end_box: tuple[float, float, float, float],
    direction: str,
    *,
    dashed: bool = False,
) -> None:
    sx, sy, sw, sh = start_box
    ex, ey, ew, eh = end_box
    if direction == "right":
        start = (sx + sw, sy + sh / 2)
        end = (ex, ey + eh / 2)
    elif direction == "left":
        start = (sx, sy + sh / 2)
        end = (ex + ew, ey + eh / 2)
    elif direction == "down":
        start = (sx + sw / 2, sy)
        end = (ex + ew / 2, ey + eh)
    elif direction == "down_left":
        start = (sx + sw * 0.25, sy)
        end = (ex + ew, ey + eh)
    else:
        raise ValueError(f"Unsupported arrow direction: {direction}")

    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=13,
        linewidth=1.2,
        color="#3A3A3A",
        linestyle="--" if dashed else "-",
        shrinkA=7,
        shrinkB=7,
        connectionstyle="arc3,rad=0.0",
    )
    ax.add_patch(arrow)


if __name__ == "__main__":
    main()
