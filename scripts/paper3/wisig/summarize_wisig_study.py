#!/usr/bin/env python3
"""Create preregistered WiSig tables, descriptive bootstrap, and figures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from openew.paper3.wisig.analysis import (
    audit_run_completeness,
    collect_class_support_performance,
    collect_diagnostics,
    collect_runs,
    descriptive_summary,
    go_no_go,
    hierarchical_fold_bootstrap,
    paired_differences,
    postfreeze_error_diagnostics,
    select_primary,
)
from openew.paper3.wisig.checkpoint import atomic_json


matplotlib.rcParams.update(
    {
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "font.size": 10,
        "axes.labelsize": 10,
        "legend.fontsize": 9,
    }
)


def save_figure(figure: plt.Figure, root: Path, name: str) -> None:
    figure.tight_layout()
    figure.savefig(root / f"{name}.png", dpi=300, bbox_inches="tight")
    figure.savefig(root / f"{name}.pdf", bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--converted-root", type=Path, required=True)
    parser.add_argument("--split-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(); args.output_root.mkdir(parents=True, exist_ok=True)
    qualification_summary_path = args.qualification_root / "audit_summary.json"
    if not qualification_summary_path.is_file():
        raise FileNotFoundError(
            f"frozen qualification audit is missing: {qualification_summary_path}"
        )
    qualification_summary = json.loads(qualification_summary_path.read_text(encoding="utf-8"))
    leakage_gate_passed = (
        qualification_summary.get("status") == "PASS"
        and qualification_summary.get("sample_level_qa") == "PASS"
        and qualification_summary.get("target_proxy_audit") == "PASS"
    )
    completeness = audit_run_completeness(args.run_root)
    atomic_json(completeness, args.output_root / "run_completeness_audit.json")
    pd.DataFrame(completeness["checkpoint_inventory"]).to_csv(
        args.output_root / "checkpoint_inventory.csv", index=False, lineterminator="\n"
    )
    frame, failures = collect_runs(args.run_root)
    group_metrics, relation_metrics = collect_diagnostics(args.run_root)
    class_support = collect_class_support_performance(args.run_root)
    error_diagnostics, error_summary = postfreeze_error_diagnostics(args.run_root, args.converted_root)
    frame.to_csv(args.output_root / "run_registry.csv", index=False, lineterminator="\n")
    failures.to_csv(args.output_root / "failed_runs.csv", index=False, lineterminator="\n")
    group_metrics.to_csv(args.output_root / "per_domain_generalization.csv", index=False, lineterminator="\n")
    relation_metrics.to_csv(args.output_root / "context_mechanism_diagnostics.csv", index=False, lineterminator="\n")
    class_support.to_csv(args.output_root / "class_support_performance.csv", index=False, lineterminator="\n")
    error_diagnostics.to_csv(args.output_root / "target_proxy_postaudit.csv", index=False, lineterminator="\n")
    atomic_json(error_summary, args.output_root / "target_proxy_postaudit_summary.json")
    receiver = select_primary(frame, "receiver_holdout")
    day = select_primary(frame, "day_holdout")
    stress = select_primary(frame, "receiver_day_stress")
    receiver.to_csv(args.output_root / "primary_results_per_seed.csv", index=False, lineterminator="\n")
    mechanism_runs = receiver[receiver.model_stage.isin(["P2","P2_SHUFFLED"])].groupby("model_stage",as_index=False).agg(
        attention_entropy_mean=("attention_entropy_mean","mean"),
        attention_entropy_std=("attention_entropy_mean","std"),
        effective_peer_count_mean=("effective_peer_count_mean","mean"),
        effective_peer_count_std=("effective_peer_count_mean","std"),
    )
    mechanism_relations = relation_metrics[
        (relation_metrics.protocol_type=="receiver_holdout")
        & relation_metrics.model_stage.isin(["P2","P2_SHUFFLED"])
        & (relation_metrics.context_size==32)
        & (relation_metrics.relation_retention==1.0)
        & (relation_metrics.partition=="test")
    ].drop_duplicates(["run_id","partition"]).groupby("model_stage",as_index=False).agg(
        relation_coverage_mean=("relation_coverage","mean"),
        isolated_anchor_fraction_mean=("isolated_anchor_fraction","mean"),
        episode_count_mean=("episode_count","mean"),
        episode_size_mean=("episode_size_mean","mean"),
        episode_size_median_mean=("episode_size_median","mean"),
        episode_size_max=("episode_size_max","max"),
    )
    mechanism_runs.merge(mechanism_relations,on="model_stage",how="outer",validate="one_to_one").to_csv(args.output_root/"context_mechanism_summary.csv",index=False,lineterminator="\n")
    summary = descriptive_summary(receiver, ["model_stage"])
    summary.to_csv(args.output_root / "primary_results_summary.csv", index=False, lineterminator="\n")
    descriptive_summary(receiver,["model_stage","fold_index"]).to_csv(args.output_root/"receiver_results_by_fold.csv",index=False,lineterminator="\n")
    descriptive_summary(receiver,["model_stage","seed"]).to_csv(args.output_root/"receiver_results_by_seed.csv",index=False,lineterminator="\n")
    day_summary = descriptive_summary(day, ["model_stage"])
    day_summary.to_csv(args.output_root / "day_results_summary.csv", index=False, lineterminator="\n")
    descriptive_summary(day,["model_stage","fold_index"]).to_csv(args.output_root/"day_results_by_fold.csv",index=False,lineterminator="\n")
    descriptive_summary(day,["model_stage","seed"]).to_csv(args.output_root/"day_results_by_seed.csv",index=False,lineterminator="\n")
    stress_summary = descriptive_summary(stress, ["model_stage"])
    stress_summary.to_csv(args.output_root / "stress_results_summary.csv", index=False, lineterminator="\n")
    paired = paired_differences(receiver)
    paired.to_csv(args.output_root / "paired_fold_seed_differences.csv", index=False, lineterminator="\n")
    bootstrap = hierarchical_fold_bootstrap(paired, replicates=2000)
    bootstrap.to_csv(args.output_root / "hierarchical_fold_bootstrap.csv", index=False, lineterminator="\n")
    retention = frame[(frame.protocol_type == "receiver_holdout") & (frame.model_stage == "P2") & (frame.context_size == 32)].drop_duplicates(["protocol_id","seed","relation_retention"])
    retention.to_csv(args.output_root / "context_retention_results.csv", index=False, lineterminator="\n")
    sizes = frame[(frame.protocol_type == "receiver_holdout") & (frame.model_stage == "P2") & (frame.relation_retention == 1.0)].drop_duplicates(["protocol_id","seed","context_size"])
    sizes.to_csv(args.output_root / "context_size_results.csv", index=False, lineterminator="\n")
    complexity = descriptive_summary(receiver, ["model_stage"])[["model_stage","run_count"]].merge(
        receiver.groupby("model_stage",as_index=False).agg(parameter_count=("parameter_count","first"),run_wall_seconds_mean=("wall_seconds","mean"),training_selection_seconds_mean=("training_selection_seconds","mean"),inference_seconds_mean=("inference_seconds","mean"),inference_samples_per_second_mean=("inference_samples_per_second","mean"),peak_gpu_memory_bytes_mean=("peak_gpu_memory_bytes","mean"),peak_cpu_rss_kib_mean=("peak_cpu_rss_kib","mean")),on="model_stage")
    complexity.to_csv(args.output_root / "compute_cost.csv", index=False, lineterminator="\n")
    decision = go_no_go(
        receiver,
        paired,
        leakage_gate_passed=leakage_gate_passed,
    )
    atomic_json(decision, args.output_root / "static_receiver_context_decision.json")
    _figures(receiver, day, paired, retention, sizes, complexity, group_metrics, class_support, args.output_root)
    _tables(summary, day_summary, stress_summary, paired, retention, sizes, complexity, args.split_root, args.output_root)
    compact_completeness = {
        key: completeness[key]
        for key in (
            "status",
            "expected_unique_runs",
            "actual_unique_config_hashes",
            "checks",
            "training_git_shas",
            "data_manifest_shas",
        )
    }
    result={"status":"PASS" if len(failures)==0 and completeness["status"]=="PASS" else "COMPLETE_WITH_FAILURES","run_count":len(frame),"failed_run_count":len(failures),"completeness":compact_completeness,"decision":decision}
    atomic_json(result,args.output_root/"analysis_summary.json"); print(json.dumps(result,indent=2,sort_keys=True)); return 0


def _figures(receiver, day, paired, retention, sizes, complexity, group_metrics, class_support, root):
    order=["P0","P0_WIDE","DG_CORAL","DG_GROUPDRO","P1","P2","P2_SHUFFLED","P2_NULL"]
    fig,ax=plt.subplots(figsize=(10,5)); data=[receiver[receiver.model_stage==m].held_out_macro_f1 for m in order]; ax.boxplot(data,tick_labels=order,showmeans=True); ax.set_ylim(0,1); ax.set_ylabel("Held-out macro-F1"); ax.tick_params(axis="x",rotation=35); save_figure(fig,root,"receiver_holdout_macro_f1")
    delta=paired[paired.comparison=="P2-P0"]; fig,ax=plt.subplots(figsize=(7,4)); means=delta.groupby("fold_index").held_out_macro_f1_delta.mean(); ax.bar(means.index.astype(str),means.values); ax.axhline(0,color="black",linewidth=.8); ax.set_xlabel("Receiver fold"); ax.set_ylabel("P2 − P0 macro-F1"); save_figure(fig,root,"paired_p2_minus_p0_by_fold")
    piv=receiver[receiver.model_stage.isin(["P2","P2_SHUFFLED"])].pivot(index=["protocol_id","seed"],columns="model_stage",values="held_out_macro_f1"); fig,ax=plt.subplots(figsize=(5,5)); ax.scatter(piv.P2_SHUFFLED,piv.P2,alpha=.7); ax.plot([0,1],[0,1],color="black",linewidth=.8); ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_xlabel("P2-SHUFFLED macro-F1"); ax.set_ylabel("P2 macro-F1"); save_figure(fig,root,"p2_vs_shuffled_context")
    agg=retention.groupby("relation_retention").held_out_macro_f1.agg(["mean","std"]).sort_index(); fig,ax=plt.subplots(figsize=(6,4)); ax.errorbar(agg.index*100,agg["mean"],yerr=agg["std"],marker="o",capsize=3); ax.set_xlim(0,100); ax.set_ylim(0,1); ax.set_xlabel("Receiver-context retention (%)"); ax.set_ylabel("Held-out macro-F1"); save_figure(fig,root,"context_retention_curve")
    fig,ax=plt.subplots(figsize=(10,5)); data=[day[day.model_stage==m].held_out_macro_f1 for m in order]; ax.boxplot(data,tick_labels=order,showmeans=True); ax.set_ylim(0,1); ax.set_ylabel("Day-holdout macro-F1"); ax.tick_params(axis="x",rotation=35); save_figure(fig,root,"day_holdout_results")
    per_receiver=group_metrics[
        (group_metrics.protocol_type=="receiver_holdout")
        & (group_metrics.group_type=="receiver")
        & group_metrics.model_stage.isin(["P0","P2"])
        & (group_metrics.context_size==32)
        & (group_metrics.relation_retention==1.0)
    ].drop_duplicates(["protocol_id","model_stage","seed","group_type","group_id"])
    agg_receiver=per_receiver.groupby(["model_stage","group_id"],as_index=False).macro_f1.mean(); fig,ax=plt.subplots(figsize=(12,4));
    receivers=sorted(agg_receiver.group_id.unique()); x=np.arange(len(receivers)); width=.4
    for offset,model in ((-.2,"P0"),(.2,"P2")):
        values=agg_receiver[agg_receiver.model_stage==model].set_index("group_id").reindex(receivers).macro_f1
        ax.bar(x+offset,values,width,label=model)
    ax.set_ylim(0,1); ax.set_xticks(x,receivers,rotation=70); ax.set_ylabel("Mean macro-F1"); ax.legend(); save_figure(fig,root,"per_receiver_generalization")
    fig,ax=plt.subplots(figsize=(7,4)); ax.bar(complexity.model_stage,complexity.training_selection_seconds_mean); ax.set_ylabel("Mean training/selection wall time (s)"); ax.tick_params(axis="x",rotation=35); save_figure(fig,root,"compute_cost")
    agg=sizes.groupby("context_size").held_out_macro_f1.agg(["mean","std"]); fig,ax=plt.subplots(figsize=(6,4)); ax.errorbar(agg.index,agg["mean"],yerr=agg["std"],marker="o",capsize=3); ax.set_ylim(0,1); ax.set_xlabel("Context size"); ax.set_ylabel("Held-out macro-F1"); save_figure(fig,root,"context_size_sensitivity")
    fig,ax=plt.subplots(figsize=(7,4))
    for model,part in class_support.groupby("model_stage"):
        agg=part.groupby("transmitter_index",as_index=False).agg(test_support=("test_support","mean"),f1=("f1","mean")); ax.scatter(agg.test_support,agg.f1,label=model,alpha=.8)
    ax.set_ylim(0,1); ax.set_xlabel("Mean held-out packets per transmitter"); ax.set_ylabel("One-vs-rest F1"); ax.legend(); save_figure(fig,root,"per_transmitter_support_vs_performance")


def _tables(summary,day_summary,stress_summary,paired,retention,sizes,complexity,split_root,root):
    split_rows=[]
    for p in sorted(Path(split_root).glob("*/split_summary.json")):
        d=json.load(open(p)); split_rows.append({"protocol":d["protocol_id"],**d["split_counts"],"eligible_transmitters":d["eligible_transmitter_count"],"sha256":d["split_manifest_sha256"]})
    pd.DataFrame(split_rows).to_csv(root/"table1_dataset_split_summary.csv",index=False,lineterminator="\n")
    summary[summary.model_stage.isin(["P0","P1","P2"])].to_csv(root/"table2_primary_receiver_results.csv",index=False,lineterminator="\n")
    summary.to_csv(root/"table3_dg_relational_baselines.csv",index=False,lineterminator="\n")
    paired.groupby("comparison").held_out_macro_f1_delta.agg(["count","mean","std","median","min","max"]).to_csv(root/"table4_paired_context_comparisons.csv",lineterminator="\n")
    retention_table = descriptive_summary(retention, ["relation_retention"]).rename(
        columns={"relation_retention": "level"}
    ).assign(control="retention")
    size_table = descriptive_summary(sizes, ["context_size"]).rename(
        columns={"context_size": "level"}
    ).assign(control="context_size")
    pd.concat([retention_table, size_table], ignore_index=True).to_csv(
        root / "table5_context_controls.csv", index=False, lineterminator="\n"
    )
    day_summary.to_csv(root/"supplement_day_results.csv",index=False,lineterminator="\n")
    stress_summary.to_csv(root/"supplement_receiver_day_stress_results.csv",index=False,lineterminator="\n")


if __name__ == "__main__": raise SystemExit(main())
