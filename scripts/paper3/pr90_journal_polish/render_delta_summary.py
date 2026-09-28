#!/usr/bin/env python3
"""Render a compact journal figure from already-frozen receiver bootstrap results.

This is a representation change only: no receiver resampling, new confidence
interval, p-value, Holm procedure, model run, or result selection occurs here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

PR90_PRIOR_SHA = "9192d0bf6bbac352bf8eccf6b8e61776df897615f21915da8b1136072ce0e8ce"
PR90_POSTHOC_SHA = "63933d1947e0f132259023df495df65a003d52df74bb0b5b986a52a3d3308792"
P2_SNAPSHOT_SHA = "a5d21be336afc3db304866c8cd3c0dc02f3b1928c7d6cb5059d85202075a24ec"
SNAPSHOT_RELATIVE = Path("configs/paper3/pr90_journal_polish/frozen_p2_receiver_delta.json")
FIXED_ORDER = ("T3A", "P2", "EMB-STD", "SAR-GN")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_checked(path: Path, expected_sha: str) -> dict:
    actual = sha256_file(path)
    if actual != expected_sha:
        raise ValueError(f"Frozen evidence hash mismatch: {path}: {actual} != {expected_sha}")
    return json.loads(path.read_text(encoding="utf-8"))


def _bootstrap(record: dict, method: str) -> dict:
    item = record["bootstrap"]
    if item["receiver_count"] != 32 or item["replicates"] != 10000:
        raise ValueError(f"Unexpected receiver/bootstrap contract for {method}")
    lower, mean, upper = (
        float(item["ci95_lower"]),
        float(item["mean_difference"]),
        float(item["ci95_upper"]),
    )
    if not lower <= mean <= upper:
        raise ValueError(f"Invalid interval for {method}")
    return {
        "method": method,
        "mean": mean,
        "lower": lower,
        "upper": upper,
        "receivers": 32,
        "replicates": 10000,
        "origin": "earlier frozen analysis" if method in {"T3A", "P2"} else "post-hoc addendum",
    }


def load_frozen_rows(repository: Path, external_data_root: Path | None = None) -> tuple[list[dict], dict]:
    evidence = repository / "papers/paper3_reviewer_remediation/evidence"
    prior_path = evidence / "prior_receiver_inference.json"
    posthoc_path = evidence / "receiver_inference.json"
    snapshot_path = repository / SNAPSHOT_RELATIVE
    prior = read_checked(prior_path, PR90_PRIOR_SHA)
    posthoc = read_checked(posthoc_path, PR90_POSTHOC_SHA)
    snapshot = read_checked(snapshot_path, P2_SNAPSHOT_SHA)
    if snapshot["comparison"] != "P2_MINUS_P0" or snapshot["kind"] != "frozen_v2_receiver_bootstrap_snapshot":
        raise ValueError("Wrong frozen P2 snapshot")
    source_relative = Path(snapshot["source_relative_to_external_data_root"])
    if source_relative.is_absolute() or ".." in source_relative.parts:
        raise ValueError("Unsafe P2 source path")
    verified_external = False
    if external_data_root is not None:
        origin = read_checked(external_data_root / source_relative, snapshot["source_sha256"])
        if origin["comparisons"]["P2_MINUS_P0"]["bootstrap"] != snapshot["bootstrap"]:
            raise ValueError("Frozen P2 snapshot differs from the external original")
        verified_external = True
    records = {
        "T3A": prior["T3A_MINUS_P0"],
        "P2": snapshot,
        "EMB-STD": posthoc["EMB_STD_MINUS_P0"],
        "SAR-GN": posthoc["SAR_GN_MINUS_P0"],
    }
    rows = [_bootstrap(records[method], method) for method in FIXED_ORDER]
    provenance = {
        "figure_status": "publication-layout-only; no new inferential computation",
        "fixed_method_order": list(FIXED_ORDER),
        "inference_unit": "receiver; five seeds averaged within receiver in original analyses",
        "interval": "original 95% receiver bootstrap interval, 10,000 replicates",
        "source_sha256": {
            "PR90_prior_receiver_inference.json": PR90_PRIOR_SHA,
            "PR90_receiver_inference.json": PR90_POSTHOC_SHA,
            "V2_receiver_level_inference.json": snapshot["source_sha256"],
            "frozen_p2_receiver_delta.json": sha256_file(snapshot_path),
        },
        "external_v2_original_verified": verified_external,
        "rows": rows,
    }
    return rows, provenance


def _format_row(row: dict) -> str:
    digits = 6 if row["method"] == "SAR-GN" else 4
    return (
        f'{row["mean"]:+.{digits}f} '
        f'[{row["lower"]:+.{digits}f}, {row["upper"]:+.{digits}f}]'
    )


def render(rows: list[dict], output_pdf: Path, output_png: Path) -> None:
    if tuple(row["method"] for row in rows) != FIXED_ORDER:
        raise ValueError("The method order must remain the prespecified source/provenance order")
    for path in (output_pdf, output_png):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite an existing figure: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })
    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    fig.subplots_adjust(left=0.14, right=0.66, top=0.77, bottom=0.28)
    fig.text(0.14, 0.95, "Paired receiver-level macro-F1 differences from P0",
             ha="left", va="top", fontsize=11, fontweight="bold")
    fig.text(0.14, 0.865, "Equal-weight receiver means; 95% receiver bootstrap intervals",
             ha="left", va="top", fontsize=8.5)
    fig.text(0.68, 0.795, "Mean [95% interval]", ha="left", va="bottom", fontsize=8.5)

    ys = (3, 2, 1, 0)
    for y, row in zip(ys, rows, strict=True):
        earlier = row["origin"] == "earlier frozen analysis"
        color = "#385C83" if earlier else "#765A44"
        ax.hlines(y, row["lower"], row["upper"], color=color, linewidth=2.2, zorder=3)
        ax.plot(
            row["mean"], y, marker="o" if earlier else "D", markersize=6.5,
            markerfacecolor=color if earlier else "white", markeredgecolor=color,
            markeredgewidth=1.3, linestyle="none", zorder=4,
        )
        ax.text(1.04, y, _format_row(row), transform=ax.get_yaxis_transform(),
                ha="left", va="center", fontsize=8.3, clip_on=False)

    ax.axvline(0, color="#555555", linewidth=0.8, linestyle="--", zorder=0)
    ax.axhline(1.5, color="#C7C7C7", linewidth=0.7, zorder=0)
    ax.set_yticks(ys, [row["method"] for row in rows])
    ax.set_xlim(-0.012, 0.040)
    ax.set_ylim(-0.55, 3.55)
    ax.set_xticks((-0.01, 0, 0.01, 0.02, 0.03, 0.04))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: "0" if abs(value) < 1e-12 else f"{value:+.2f}"))
    ax.set_xlabel("Macro-F1 difference (method minus P0)", labelpad=4)
    ax.tick_params(axis="both", labelsize=9)
    fig.text(
        0.14, 0.075,
        "Filled circles: earlier frozen results (T3A, P2). Open diamonds: post-hoc (EMB-STD, SAR-GN).",
        ha="left", va="center", fontsize=8.1,
    )
    fig.savefig(
        output_pdf, metadata={
            "Creator": "OpenEW-SA frozen-inference journal renderer",
            "CreationDate": None, "ModDate": None,
        },
    )
    fig.savefig(output_png, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--external-data-root", type=Path)
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--png", type=Path)
    args = parser.parse_args()
    repository = args.repository.resolve()
    figure_dir = repository / "papers/paper3_reviewer_remediation/manuscript/figures"
    output_pdf = args.pdf or figure_dir / "receiver_delta_summary.pdf"
    output_png = args.png or figure_dir / "receiver_delta_summary.png"
    manifest = output_pdf.with_suffix(".provenance.json")
    if manifest.exists():
        raise FileExistsError(f"Refusing to overwrite provenance: {manifest}")
    rows, provenance = load_frozen_rows(repository, args.external_data_root)
    render(rows, output_pdf, output_png)
    provenance["output_sha256"] = {
        "pdf": sha256_file(output_pdf),
        "png": sha256_file(output_png),
    }
    manifest.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pdf_path": str(output_pdf), "png_path": str(output_png), **provenance["output_sha256"]}))


if __name__ == "__main__":
    main()
