"""Automatic tabulation, exploratory figures, and frozen verdict calculations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from statistics import median
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


PROTOCOL_LABELS = {
    "jamshield_scenario": "JamShield scenario",
    "jamshield_reactive": "JamShield reactive",
    "electrosense_sensor": "ElectroSense sensor",
    "deepsense_cross_day": "DeepSense cross-day",
}
STAGE_ORDER = ["m0", "m1", "m2"]
COLORS = {"m0": "#4C78A8", "m1": "#F2B134", "m2": "#E36C3D"}


def summarize_run_root(
    run_root: str | Path,
    analysis_root: str | Path,
    config: dict[str, Any],
) -> dict[str, Any]:
    root = Path(run_root)
    output = Path(analysis_root)
    output.mkdir(parents=True, exist_ok=True)
    records = _read_run_metadata(root / "metadata")
    registry = pd.DataFrame([_registry_row(item) for item in records])
    _write(registry, output / "run_registry.csv")
    failed = registry.loc[registry.get("status", pd.Series(dtype=str)).eq("FAILED")].copy()
    _write(failed, output / "failed_runs.csv")

    completed = [item for item in records if item.get("status") == "COMPLETED" and item.get("heldout_metrics")]
    per_seed = pd.DataFrame([_result_row(item) for item in completed if item.get("variant") in {None, "primary"}])
    if "variant" in per_seed and per_seed["variant"].isna().all():
        per_seed["variant"] = "primary"
    _write(per_seed, output / "primary_results_per_seed.csv")
    primary = per_seed.loc[per_seed["variant"].eq("primary")].copy() if not per_seed.empty else per_seed
    primary_summary = _aggregate_metrics(primary, ["dataset", "protocol", "model_stage"])
    _write(primary_summary, output / "primary_results_summary.csv")
    paired = _paired_differences(primary)
    _write(paired, output / "paired_seed_differences.csv")

    corruption = pd.DataFrame(
        [
            _result_row(item)
            for item in completed
            if item.get("model_stage") == "m2"
            and not item.get("shuffled_relations", False)
            and (
                item.get("variant") == "primary"
                or str(item.get("variant", "")).startswith("retention_")
            )
        ]
    )
    _write(corruption, output / "relation_corruption_results.csv")
    ablation = pd.DataFrame(
        [
            _result_row(item)
            for item in completed
            if item.get("model_stage") == "m2"
            and not item.get("shuffled_relations", False)
            and item.get("variant")
            in {"primary", "receiver_only", "date_only", "receiver_date_only", "retention_0"}
        ]
    )
    _write(ablation, output / "relation_ablation_results.csv")

    relation_rows: list[dict[str, Any]] = []
    for item in completed:
        coverage = item.get("relation_coverage", {}).get("heldout") or {}
        for relation_type, stats in coverage.get("per_relation_type", {}).items():
            relation_rows.append(
                {
                    "run_id": item["run_id"],
                    "dataset": item["dataset"],
                    "protocol": item["protocol"],
                    "model_stage": item["model_stage"],
                    "seed": item["seed"],
                    "variant": item.get("variant", "primary"),
                    "relation_retention": item.get("relation_retention", 1.0),
                    "shuffled_relations": item.get("shuffled_relations", False),
                    "relation_type": relation_type,
                    **stats,
                    "overall_relation_coverage": coverage.get("relation_coverage"),
                    "isolated_node_count": coverage.get("isolated_node_count"),
                    "isolated_node_fraction": coverage.get("isolated_node_fraction"),
                }
            )
    relation_frame = pd.DataFrame(relation_rows)
    _write(relation_frame, output / "relation_coverage_summary.csv")

    complexity = _aggregate_metrics(
        primary,
        ["dataset", "protocol", "model_stage"],
        metric_columns=[
            "parameter_count",
            "wall_time_seconds",
            "training_wall_time_seconds",
            "inference_wall_time_seconds",
            "peak_gpu_memory_bytes",
            "peak_cpu_rss_kib",
            "training_samples_per_second",
            "inference_samples_per_second",
            "context_construction_overhead_seconds",
        ],
    )
    _write(complexity, output / "complexity_summary.csv")
    _write_group_diagnostics(config, output)

    verdicts = compute_verdicts(completed, config)
    (output / "m2_go_no_go.json").write_text(
        json.dumps(verdicts, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _make_figures(primary, paired, corruption, ablation, relation_frame, completed, output)
    summary = {
        "run_root": str(root),
        "analysis_root": str(output),
        "total_metadata_records": len(records),
        "completed_with_heldout": len(completed),
        "failed": int(len(failed)),
        "verdicts": verdicts,
    }
    (output / "analysis_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def _read_run_metadata(directory: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(directory.glob("*.json")):
        if path.name == "suite_summary.json":
            continue
        item = json.loads(path.read_text(encoding="utf-8"))
        item.setdefault("variant", _variant_from_run_id(item.get("run_id", "")))
        item.setdefault("shuffled_relations", "__shuffled__" in item.get("run_id", ""))
        records.append(item)
    return records


def _variant_from_run_id(run_id: str) -> str:
    parts = run_id.split("__")
    return parts[4] if len(parts) > 4 else "primary"


def _registry_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": item.get("run_id"),
        "dataset": item.get("dataset"),
        "protocol": item.get("protocol"),
        "model_stage": item.get("model_stage"),
        "seed": item.get("seed"),
        "variant": item.get("variant", _variant_from_run_id(item.get("run_id", ""))),
        "relation_types": ";".join(item.get("relation_types", [])),
        "relation_retention": item.get("relation_retention"),
        "shuffled_relations": item.get("shuffled_relations", False),
        "context_size": item.get("context_size"),
        "git_sha": item.get("git_sha"),
        "config_hash": item.get("config_hash"),
        "source_hash": item.get("source_hash"),
        "start_time": item.get("start_time"),
        "end_time": item.get("end_time"),
        "device": item.get("device"),
        "parameter_count": item.get("parameter_count"),
        "status": item.get("status"),
        "failure_reason": item.get("failure_reason", ""),
        "wall_time_seconds": item.get("wall_time_seconds"),
    }


def _result_row(item: dict[str, Any]) -> dict[str, Any]:
    source = item["source_validation_metrics"]
    heldout = item["heldout_metrics"]
    return {
        **_registry_row(item),
        "source_validation_macro_f1": source["macro_f1"],
        "source_validation_balanced_accuracy": source["balanced_accuracy"],
        "source_validation_accuracy": source["accuracy"],
        "source_validation_ece": source["ece"],
        "heldout_macro_f1": heldout["macro_f1"],
        "heldout_balanced_accuracy": heldout["balanced_accuracy"],
        "heldout_accuracy": heldout["accuracy"],
        "heldout_ece": heldout["ece"],
        "training_wall_time_seconds": item.get("training_wall_time_seconds"),
        "inference_wall_time_seconds": item.get("inference_wall_time_seconds"),
        "peak_gpu_memory_bytes": item.get("peak_gpu_memory_bytes"),
        "peak_cpu_rss_kib": item.get("peak_cpu_rss_kib"),
        "training_samples_per_second": item.get("training_samples_per_second"),
        "inference_samples_per_second": item.get("inference_samples_per_second"),
        "context_construction_overhead_seconds": item.get("context_construction_overhead_seconds"),
    }


def _aggregate_metrics(
    frame: pd.DataFrame,
    group_columns: list[str],
    metric_columns: list[str] | None = None,
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    metrics = metric_columns or [
        "source_validation_macro_f1",
        "source_validation_balanced_accuracy",
        "source_validation_accuracy",
        "source_validation_ece",
        "heldout_macro_f1",
        "heldout_balanced_accuracy",
        "heldout_accuracy",
        "heldout_ece",
    ]
    rows: list[dict[str, Any]] = []
    for keys, group in frame.groupby(group_columns, sort=True):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_columns, keys))
        row["n_runs"] = len(group)
        row["seeds"] = ";".join(str(value) for value in sorted(group["seed"].astype(int).tolist())) if "seed" in group else ""
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy(dtype=float)
            row[f"{metric}_mean"] = float(np.mean(values)) if len(values) else np.nan
            row[f"{metric}_std"] = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0 if len(values) else np.nan
            row[f"{metric}_median"] = float(median(values)) if len(values) else np.nan
            row[f"{metric}_min"] = float(np.min(values)) if len(values) else np.nan
            row[f"{metric}_max"] = float(np.max(values)) if len(values) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def _paired_differences(primary: pd.DataFrame) -> pd.DataFrame:
    if primary.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for protocol, group in primary.groupby("protocol"):
        pivot = group.pivot_table(
            index="seed",
            columns="model_stage",
            values=["source_validation_macro_f1", "heldout_macro_f1"],
            aggfunc="first",
        )
        for seed in pivot.index:
            for left, right, label in (("m1", "m0", "M1-M0"), ("m2", "m0", "M2-M0"), ("m2", "m1", "M2-M1")):
                if ("heldout_macro_f1", left) not in pivot or ("heldout_macro_f1", right) not in pivot:
                    continue
                rows.append(
                    {
                        "protocol": protocol,
                        "seed": int(seed),
                        "comparison": label,
                        "source_validation_macro_f1_delta": float(
                            pivot.loc[seed, ("source_validation_macro_f1", left)]
                            - pivot.loc[seed, ("source_validation_macro_f1", right)]
                        ),
                        "heldout_macro_f1_delta": float(
                            pivot.loc[seed, ("heldout_macro_f1", left)]
                            - pivot.loc[seed, ("heldout_macro_f1", right)]
                        ),
                    }
                )
    return pd.DataFrame(rows)


def compute_verdicts(completed: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    records = pd.DataFrame([_result_row(item) for item in completed])
    thresholds = config["go_no_go"]
    protocol_results: dict[str, Any] = {}
    for protocol in ("jamshield_scenario", "jamshield_reactive", "electrosense_sensor"):
        primary = records.loc[(records["protocol"] == protocol) & (records["variant"] == "primary")]
        m0 = primary.loc[primary["model_stage"] == "m0"].set_index("seed")
        m2 = primary.loc[primary["model_stage"] == "m2"].set_index("seed")
        shared = sorted(set(m0.index) & set(m2.index))
        source_delta = m2.loc[shared, "source_validation_macro_f1"] - m0.loc[shared, "source_validation_macro_f1"]
        target_delta = m2.loc[shared, "heldout_macro_f1"] - m0.loc[shared, "heldout_macro_f1"]
        a_pass = len(shared) == 5 and float(source_delta.mean()) > 0 and int((source_delta > 0).sum()) >= 3
        b_pass = len(shared) == 5 and float(target_delta.mean()) >= float(
            thresholds["heldout_non_degradation_tolerance"]
        )
        shuffled = records.loc[
            (records["protocol"] == protocol)
            & (records["model_stage"] == "m2")
            & (records["variant"] == "shuffled_control")
        ].set_index("seed")
        shuffled_shared = sorted(set(m2.index) & set(shuffled.index))
        actual_source_gap = float(
            (
                m2.loc[shuffled_shared, "source_validation_macro_f1"]
                - shuffled.loc[shuffled_shared, "source_validation_macro_f1"]
            ).mean()
        ) if shuffled_shared else float("nan")
        actual_target_gap = float(
            (
                m2.loc[shuffled_shared, "heldout_macro_f1"]
                - shuffled.loc[shuffled_shared, "heldout_macro_f1"]
            ).mean()
        ) if shuffled_shared else float("nan")
        gap_threshold = float(thresholds["actual_minus_shuffled_threshold"])
        c_pass = (
            len(shuffled_shared) == 5
            and actual_source_gap >= gap_threshold
            and actual_target_gap >= gap_threshold
        )
        c_heterogeneous = (
            len(shuffled_shared) == 5
            and max(abs(actual_source_gap), abs(actual_target_gap)) >= gap_threshold
            and np.sign(actual_source_gap) != np.sign(actual_target_gap)
        )
        corruption = records.loc[
            (records["protocol"] == protocol)
            & (records["model_stage"] == "m2")
            & (~records["shuffled_relations"].astype(bool))
            & (records["variant"].astype(str).str.startswith("retention_") | records["variant"].eq("primary"))
        ]
        retention_means = (
            corruption.groupby("relation_retention")["source_validation_macro_f1"].mean().sort_index()
        )
        expected_levels = {0.0, 0.25, 0.5, 0.75, 1.0}
        complete_retention = set(round(float(value), 2) for value in retention_means.index) == expected_levels
        rho = float(spearmanr(retention_means.index, retention_means.values).statistic) if complete_retention else float("nan")
        differences = np.diff(retention_means.values) if complete_retention else np.asarray([])
        endpoint = float(retention_means.loc[1.0] - retention_means.loc[0.0]) if complete_retention else float("nan")
        d_pass = complete_retention and (
            rho >= float(thresholds["retention_spearman_threshold"])
            or (
                endpoint >= float(thresholds["retention_endpoint_threshold"])
                and int((differences >= 0).sum()) >= 3
            )
        )
        passed_aux = sum((a_pass, c_pass, d_pass))
        if a_pass and b_pass and c_pass and d_pass:
            verdict = "GO"
        elif b_pass and (passed_aux >= 2 or (c_heterogeneous and a_pass and passed_aux >= 1)):
            verdict = "CONDITIONAL GO"
        else:
            verdict = "NO-GO"
        protocol_results[protocol] = {
            "verdict": verdict,
            "A_validation_support": bool(a_pass),
            "B_heldout_non_degradation": bool(b_pass),
            "C_actual_over_shuffled": bool(c_pass),
            "C_heterogeneous": bool(c_heterogeneous),
            "D_retention_interpretable": bool(d_pass),
            "m2_minus_m0_source_validation_mean": float(source_delta.mean()) if len(source_delta) else None,
            "m2_minus_m0_heldout_mean": float(target_delta.mean()) if len(target_delta) else None,
            "actual_minus_shuffled_source_validation_mean": actual_source_gap,
            "actual_minus_shuffled_heldout_mean": actual_target_gap,
            "retention_spearman_source_validation": rho,
            "retention_full_minus_zero_source_validation": endpoint,
        }
    verdict_values = [item["verdict"] for item in protocol_results.values()]
    if verdict_values and all(value == "GO" for value in verdict_values):
        overall = "GO"
    elif verdict_values.count("GO") >= 1 or verdict_values.count("CONDITIONAL GO") >= 2:
        overall = "CONDITIONAL GO"
    else:
        overall = "NO-GO"
    return {"protocols": protocol_results, "overall": overall}


def _write_group_diagnostics(config: dict[str, Any], output: Path) -> None:
    jam = pd.read_csv(Path(config["artifacts"]["jamshield"]) / "metadata.csv", dtype=str, keep_default_na=False)
    target = "abnormal_event_label"
    rows = []
    for value, group in jam.groupby("rx_id", sort=True):
        counts = group[target].value_counts().to_dict()
        rows.append(
            {
                "station_id_sha256_8": hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:8],
                "n_samples": len(group),
                "target_class_count": len(counts),
                "audit_only_target_purity": max(counts.values()) / len(group),
                "audit_only_target_counts": json.dumps(counts, sort_keys=True),
            }
        )
    _write(pd.DataFrame(rows), output / "jamshield_station_group_diagnostics.csv")

    es_root = Path(config["artifacts"]["electrosense"])
    es = pd.read_csv(es_root / "metadata.csv", dtype=str, keep_default_na=False)
    labels = json.loads((es_root / "labels.json").read_text(encoding="utf-8"))
    dates: list[str] = []
    for item in labels["source_files"]:
        dates.extend([str(item["date_id"])] * int(item["row_count"]))
    es["source_date_id"] = dates
    es_rows = []
    for relation_type, fields in (
        ("receiver", ["rx_id"]),
        ("date", ["source_date_id"]),
        ("receiver_date", ["rx_id", "source_date_id"]),
    ):
        grouped = es.groupby(fields, sort=True, dropna=False).size()
        for key, count in grouped.items():
            text = key if isinstance(key, str) else "|".join(str(value) for value in key)
            es_rows.append(
                {
                    "relation_type": relation_type,
                    "group_id_sha256_8": hashlib.sha256(text.encode("utf-8")).hexdigest()[:8],
                    "n_samples": int(count),
                }
            )
    _write(pd.DataFrame(es_rows), output / "electrosense_group_diagnostics.csv")


def _make_figures(
    primary: pd.DataFrame,
    paired: pd.DataFrame,
    corruption: pd.DataFrame,
    ablation: pd.DataFrame,
    relation: pd.DataFrame,
    completed: list[dict[str, Any]],
    output: Path,
) -> None:
    if primary.empty:
        return
    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9})
    _figure_primary(primary, output)
    _figure_paired(paired, output)
    _figure_retention(corruption, output)
    _figure_ablation(ablation, output)
    _figure_domains(completed, output)
    _figure_relation_stats(relation, output)


def _save_figure(fig: plt.Figure, output: Path, name: str) -> None:
    fig.tight_layout()
    fig.savefig(output / f"{name}.png", dpi=220, bbox_inches="tight")
    fig.savefig(output / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def _figure_primary(primary: pd.DataFrame, output: Path) -> None:
    protocols = list(PROTOCOL_LABELS)
    fig, ax = plt.subplots(figsize=(9.0, 4.5))
    width = 0.23
    positions = np.arange(len(protocols))
    for offset, stage in enumerate(STAGE_ORDER):
        means, stds = [], []
        for protocol in protocols:
            values = primary.loc[(primary.protocol == protocol) & (primary.model_stage == stage), "heldout_macro_f1"].to_numpy(float)
            means.append(np.mean(values) if len(values) else np.nan)
            stds.append(np.std(values, ddof=1) if len(values) > 1 else 0.0)
        ax.bar(positions + (offset - 1) * width, means, width, yerr=stds, label=stage.upper(), color=COLORS[stage], edgecolor="#333333", linewidth=0.5, capsize=3)
    ax.set_xticks(positions, [PROTOCOL_LABELS[value] for value in protocols], rotation=15, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Held-out macro-F1")
    ax.set_title("Paper 3 primary held-out macro-F1 by frozen protocol")
    ax.legend(frameon=False, ncol=3)
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.6)
    _save_figure(fig, output, "paper3_primary_macro_f1_by_dataset")


def _figure_paired(paired: pd.DataFrame, output: Path) -> None:
    data = paired.loc[paired.comparison == "M2-M0"]
    protocols = sorted(data.protocol.unique())
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    for index, protocol in enumerate(protocols):
        values = data.loc[data.protocol == protocol, "heldout_macro_f1_delta"].to_numpy(float)
        ax.scatter(np.full(len(values), index), values, color="#4C78A8", edgecolor="#222222", linewidth=0.5, zorder=3)
        ax.plot([index - 0.22, index + 0.22], [np.mean(values), np.mean(values)], color="#E36C3D", linewidth=2)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xticks(range(len(protocols)), [PROTOCOL_LABELS[value] for value in protocols], rotation=12, ha="right")
    ax.set_ylabel("Seed-matched held-out macro-F1 change")
    ax.set_title("Descriptive M2 minus M0 paired differences")
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.6)
    _save_figure(fig, output, "paper3_paired_m2_minus_m0")


def _figure_retention(corruption: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    for protocol in sorted(corruption.protocol.unique()):
        group = corruption.loc[corruption.protocol == protocol]
        summary = group.groupby("relation_retention")["heldout_macro_f1"].agg(["mean", "std"]).sort_index()
        x = summary.index.to_numpy(float) * 100
        ax.errorbar(x, summary["mean"], yerr=summary["std"].fillna(0), marker="o", linewidth=1.6, capsize=3, label=PROTOCOL_LABELS[protocol])
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("Retained relation incidences (%)")
    ax.set_ylabel("Held-out macro-F1")
    ax.set_title("Relation-retention curves under frozen incidence corruption")
    ax.legend(frameon=False)
    ax.grid(color="#DDDDDD", linewidth=0.6)
    _save_figure(fig, output, "paper3_relation_retention_curves")


def _figure_ablation(ablation: pd.DataFrame, output: Path) -> None:
    frame = ablation.copy()
    frame["display_variant"] = frame["variant"].replace({"primary": "full", "retention_0": "no relations"})
    summary = frame.groupby(["protocol", "display_variant"])["heldout_macro_f1"].agg(["mean", "std"]).reset_index()
    labels = [f"{PROTOCOL_LABELS[row.protocol]}\n{row.display_variant}" for row in summary.itertuples()]
    fig, ax = plt.subplots(figsize=(10.0, 4.8))
    ax.bar(np.arange(len(summary)), summary["mean"], yerr=summary["std"].fillna(0), color="#4C78A8", edgecolor="#333333", linewidth=0.5, capsize=3)
    ax.set_xticks(np.arange(len(summary)), labels, rotation=28, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Held-out macro-F1")
    ax.set_title("Predeclared M2 relation-component ablations")
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.6)
    _save_figure(fig, output, "paper3_relation_ablation")


def _figure_domains(completed: list[dict[str, Any]], output: Path) -> None:
    rows = []
    for item in completed:
        if item.get("variant", _variant_from_run_id(item.get("run_id", ""))) != "primary":
            continue
        for domain, metrics in item["heldout_metrics"]["per_domain"].items():
            rows.append({"protocol": item["protocol"], "stage": item["model_stage"], "domain": domain, "macro_f1": metrics["macro_f1"]})
    frame = pd.DataFrame(rows)
    summary = frame.groupby(["protocol", "domain", "stage"])["macro_f1"].mean().reset_index()
    summary["label"] = summary["protocol"].map(PROTOCOL_LABELS) + " / " + summary["domain"]
    matrix = summary.pivot(index="label", columns="stage", values="macro_f1").reindex(columns=STAGE_ORDER)
    fig, ax = plt.subplots(figsize=(7.0, max(4.0, 0.35 * len(matrix))))
    image = ax.imshow(matrix.to_numpy(float), aspect="auto", vmin=0, vmax=1, cmap="Blues")
    ax.set_yticks(range(len(matrix)), matrix.index)
    ax.set_xticks(range(len(matrix.columns)), [value.upper() for value in matrix.columns])
    ax.set_title("Mean per-domain held-out macro-F1")
    for row in range(len(matrix)):
        for column in range(len(matrix.columns)):
            value = matrix.iloc[row, column]
            if pd.notna(value):
                ax.text(column, row, f"{value:.3f}", ha="center", va="center", color="white" if value > 0.55 else "#222222", fontsize=7)
    fig.colorbar(image, ax=ax, label="Macro-F1", fraction=0.03, pad=0.02)
    _save_figure(fig, output, "paper3_per_domain_generalization")


def _figure_relation_stats(relation: pd.DataFrame, output: Path) -> None:
    frame = relation.loc[(relation.variant == "primary") & (relation.model_stage == "m2")]
    summary = frame.groupby(["protocol", "relation_type"]).agg(
        coverage=("relation_coverage", "mean"),
        mean_group_size=("context_group_size_mean", "mean"),
        max_group_size=("context_group_size_max", "max"),
    ).reset_index()
    labels = [f"{PROTOCOL_LABELS[row.protocol]}\n{row.relation_type}" for row in summary.itertuples()]
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6))
    axes[0].barh(np.arange(len(summary)), summary.coverage, color="#4C78A8", edgecolor="#333333", linewidth=0.5)
    axes[0].set_yticks(np.arange(len(summary)), labels)
    axes[0].set_xlim(0, 1)
    axes[0].set_xlabel("Held-out relation coverage")
    axes[0].set_title("Coverage")
    axes[1].barh(np.arange(len(summary)), summary.mean_group_size, color="#F2B134", edgecolor="#333333", linewidth=0.5, label="Mean")
    axes[1].scatter(summary.max_group_size, np.arange(len(summary)), color="#E36C3D", marker="|", s=100, label="Maximum")
    axes[1].set_yticks(np.arange(len(summary)), [])
    axes[1].set_xlabel("Bounded context-group size")
    axes[1].set_title("Group sizes")
    axes[1].legend(frameon=False)
    for axis in axes:
        axis.grid(axis="x", color="#DDDDDD", linewidth=0.6)
    fig.suptitle("Relation coverage and bounded context sizes")
    _save_figure(fig, output, "paper3_relation_coverage_and_group_sizes")


def _write(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, float_format="%.9f")
