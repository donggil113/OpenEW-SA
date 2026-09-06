"""Deterministic, payload-absent publication figures/tables and numerical lineage."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openew.paper3.reviewer_remediation.contracts import file_sha
p=argparse.ArgumentParser();p.add_argument("--repository",type=Path,default=Path.cwd());p.add_argument("--png-output",type=Path,required=True);a=p.parse_args()
doc=a.repository/"papers/paper3_reviewer_remediation";e=doc/"evidence";m=doc/"manuscript"
for d in (m/"figures",m/"tables",a.png_output):d.mkdir(parents=True,exist_ok=True)
lineage=json.loads((e/"source_manifest.json").read_text())
for name,sha in lineage["exports"].items():
 if file_sha(e/name)!=sha:raise RuntimeError("release evidence changed: "+name)
s=pd.read_csv(e/"primary_summary.csv");rx=pd.read_csv(e/"receiver_averages.csv")
raw=s[s.probability_variant=="raw"].set_index("method")
rr=rx[(rx.scope=="primary")&(rx.probability_variant=="raw")]
palette=["#4267A1","#B58618","#D56B37","#667846","#B65A87"]
methods=["P0","T3A","P2","SAR_GN","EMB_STD"];labels={"P0":"P0","T3A":"T3A","P2":"P2","SAR_GN":"SAR-GN","EMB_STD":"EMB-STD","SUP_FT_FULL_128":"Full FT oracle"}
plt.rcParams.update({"font.size":9,"font.family":"DejaVu Sans","pdf.fonttype":42,"ps.fonttype":42,
 "axes.spines.top":False,"axes.spines.right":False,"axes.titleweight":"bold","savefig.dpi":180})
figures=[]
def save(fig,name):
 fig.savefig(m/"figures"/(name+".pdf"),bbox_inches="tight",metadata={"CreationDate":None,"ModDate":None,"Creator":"OpenEW-SA frozen-summary renderer"})
 fig.savefig(a.png_output/(name+".png"),bbox_inches="tight")
 plt.close(fig);figures.append(name)
def title(ax,text):ax.set_title(text+"\nPost-hoc addendum; frozen references retained",fontsize=9)
def esc(x):return str(x).replace("_",r"\_").replace("%",r"\%")
def table(name,headers,rows):
 text=r"\begin{tabular}{l"+"r"*(len(headers)-1)+"}\n"+r"\toprule"+"\n"+" & ".join(headers)+r" \\"+"\n"+r"\midrule"+"\n"
 text+="\n".join(" & ".join(esc(x) for x in row)+r" \\" for row in rows)+"\n"+r"\bottomrule\end{tabular}"+"\n"
 (m/"tables"/(name+".tex")).write_text(text)
# Exact numerical macros; every numeric summary cell has a source/key.
numbers=[r"\newcommand{\val}[3]{\csname v#1#2#3\endcsname}",r"\newcommand{\dval}[2]{\csname d#1#2\endcsname}"]
trace=["# Numerical traceability — revised manuscript","",
"Every result cell below is generated, never manually transcribed. Unit: equal-weight receiver after five-seed averaging. Source identifiers are portable relative evidence files. Analysis package: "+lineage["analysis_sha256"]+"; analysis Git: "+lineage["analysis_git_sha"]+". New results and probability diagnostics are POST-HOC; prior rows retain their historical provenance.","",
"| Source | Row/key | Value | Evidence |","|---|---|---|---|"]
for _,row in s.iterrows():
 for metric in s.columns[2:]:
  value=float(row[metric]);numbers.append(r"\expandafter\def\csname v"+row.method+metric+row.probability_variant+r"\endcsname{"+f"{value:.6f}"+"}")
  trace.append(f"| primary_summary.csv | {row.method}/{row.probability_variant}/{metric} | {value:.12g} | "+("POST-HOC" if row.method in ["SAR_GN","EMB_STD","SUP_FT_FULL_128"] or row.probability_variant!="raw" else "FROZEN REFERENCE")+" |")
inference=json.loads((e/"receiver_inference.json").read_text())
inference["T3A_MINUS_P0"]=json.loads((e/"prior_receiver_inference.json").read_text())["T3A_MINUS_P0"]
for key,r in inference.items():
 vals={**r["bootstrap"],"p_value":r["sign_flip"]["p_value"],"positive":r.get("positive",r.get("positive_receivers"))}
 for field,value in vals.items():
  numbers.append(r"\expandafter\def\csname d"+key+field+r"\endcsname{"+(str(value) if isinstance(value,int) else f"{value:.6f}")+"}")
  trace.append(f"| {'prior_' if key=='T3A_MINUS_P0' else ''}receiver_inference.json | {key}/{field} | {value} | {'PR88 retrospective family' if key=='T3A_MINUS_P0' else 'POST-HOC exploratory'} |")
(m/"numbers.tex").write_text("\n".join(numbers)+"\n")
# Main benchmark, neutral fixed order, explicit oracle separator.
order=["P0","P0_WIDE","SOURCE_NORM","DG_CORAL","DG_DANN","DG_GROUPDRO","RX_NORM","T3A","P1","P2","SAR_GN","EMB_STD"]
table("benchmark",["Method","F1","Accuracy","ECE","NLL","Brier"],
 [[x.replace("_","-")]+[f"{raw.loc[x,k]:.4f}" for k in ["macro_f1","accuracy","ece","nll","brier"]] for x in order])
table("oracle",["Labeled diagnostic","F1","ECE","NLL"],
 [[x]+[f"{raw.loc[meth,k]:.4f}" for k in ["macro_f1","ece","nll"]] for x,meth in [("Head FT","SUP_FT_HEAD_128"),("Full FT","SUP_FT_FULL_128")]])
table("paired",["Post-hoc comparison","Delta","95\\% interval","+rx","p"],
 [[key.replace("_MINUS_"," - ").replace("_","-"),f'{r["bootstrap"]["mean_difference"]:.5f}',
 f'[{r["bootstrap"]["ci95_lower"]:.5f}, {r["bootstrap"]["ci95_upper"]:.5f}]',r["positive"],f'{r["sign_flip"]["p_value"]:.5f}']
 for key,r in inference.items() if key!="T3A_MINUS_P0"])
table("probability",["Method","ECE raw","ECE TS","NLL raw","NLL TS","Gap raw"],
 [[labels[x]]+[f"{s[(s.method==x)&(s.probability_variant==v)].iloc[0][k]:.4f}" for k,v in [("ece","raw"),("ece","source_temperature"),("nll","raw"),("nll","source_temperature"),("confidence_accuracy_gap","raw")]] for x in methods])
new=pd.read_csv(e/"new_budget_summary.csv")
prior=pd.read_csv(e/"prior_support_budget_summary.csv").rename(columns={"support_budget":"budget","macro_f1_mean":"macro_f1"})
budget=pd.concat([new[["method","budget","macro_f1"]],prior[["method","budget","macro_f1"]]],ignore_index=True)
table("budget",["Packets","T3A","P2","SAR-GN","EMB-STD"],
 [[b]+[f'{budget[(budget.method==x)&(budget.budget==b)].iloc[0].macro_f1:.4f}' for x in ["T3A","P2","SAR_GN","EMB_STD"]] for b in [16,32,64,128,256]])
for _,r in budget.iterrows():trace.append(f"| {'new' if r.method in ['SAR_GN','EMB_STD'] else 'prior_support'}_budget_summary.csv | {r.method}/{r.budget}/macro_f1 | {r.macro_f1:.12g} | Common-reserve query; descriptive |")
cost=pd.read_csv(e/"timing_summary.csv").set_index("method")
table("compute",["Method","Total ms","Total query/s","Peak MiB"],
 [[labels[x],f'{cost.loc[x,"total_seconds"]*1000:.2f}',f'{cost.loc[x,"total_samples_per_second"]:.0f}',f'{cost.loc[x,"peak_gpu_memory_bytes"]/2**20:.1f}'] for x in methods])
for method,r in cost.iterrows():
 for metric in ["total_seconds","total_samples_per_second","peak_gpu_memory_bytes"]:
  trace.append(f"| timing_summary.csv | {method}/{metric} | {r[metric]:.12g} | TIMING ONLY; seed 829; 3 repeats; 32 receivers |")
(doc/"numerical_traceability_matrix.md").write_text("\n".join(trace)+"\n")
fig,ax=plt.subplots(figsize=(7.2,3.8));x=np.arange(len(methods))
for i,method in enumerate(methods):
 values=rr[rr.method==method].macro_f1.to_numpy()
 ax.scatter(np.full(len(values),i)+np.linspace(-.12,.12,len(values)),values,s=10,alpha=.5,color=palette[i])
 ax.plot(i,values.mean(),marker="_",markersize=23,color="black",mew=2)
ax.set_xticks(x,[labels[x] for x in methods]);ax.set_ylim(0,1);ax.set_ylabel("Receiver macro-F1");title(ax,"Unlabeled benchmark: all receiver means and grand means");save(fig,"benchmark")
pivot=rr.pivot(index="receiver",columns="method",values="macro_f1").sort_index()
fig,ax=plt.subplots(figsize=(7.2,3.8))
for i,meth in enumerate(["T3A","P2","SAR_GN","EMB_STD"]):
 ax.plot(np.arange(32),pivot[meth]-pivot.P0,label=labels[meth],marker=["o","s","^","D"][i],ms=3,lw=.8,color=palette[i+1])
ax.axhline(0,color="black",lw=.8);ax.set_xticks(np.arange(32),pivot.index,rotation=90,fontsize=7)
ax.set_ylabel("Receiver macro-F1 difference from P0");title(ax,"Receiver heterogeneity; fixed receiver order");ax.legend(ncol=4,fontsize=8);save(fig,"receiver_deltas")
fig,ax=plt.subplots(figsize=(7.2,3.8))
for i,meth in enumerate(["T3A","P2","SAR_GN","EMB_STD"]):
 b=budget[budget.method==meth].sort_values("budget");ax.plot(b.budget,b.macro_f1,label=labels[meth],marker=["o","s","^","D"][i],color=palette[i+1])
ax.set_ylim(0,1);ax.set_xticks([0,16,32,64,128,256]);ax.set_xlabel("Unlabeled support packets");ax.set_ylabel("Receiver-equal macro-F1");ax.legend(ncol=4,fontsize=8);title(ax,"Support budgets: common 256-reserve query set");save(fig,"support_budget")
fig,axes=plt.subplots(1,3,figsize=(7.2,3))
for ax,metric in zip(axes,["ece","nll","brier"]):
 for i,method in enumerate(methods):
  v=s[s.method==method].set_index("probability_variant")
  ax.plot([i-.12,i+.12],[v.loc["raw",metric],v.loc["source_temperature",metric]],color=palette[i],lw=1)
  ax.scatter(i-.12,v.loc["raw",metric],marker="o",color=palette[i],s=20)
  ax.scatter(i+.12,v.loc["source_temperature",metric],marker="s",facecolor="white",edgecolor=palette[i],s=20)
 ax.set_xticks(range(5),[labels[x] for x in methods],rotation=65,fontsize=7);ax.set_ylim(bottom=0);ax.set_title(metric.upper()+" (lower is better)",fontsize=9)
fig.suptitle("Post-hoc probability quality: filled = raw; hollow = source temperature",fontsize=9);fig.tight_layout();save(fig,"probability_quality")
bins=pd.read_csv(e/"reliability_receiver_bins.csv")
fig,(ax,mass)=plt.subplots(2,1,figsize=(7.2,4.5),gridspec_kw={"height_ratios":[3,1]},sharex=True)
for i,meth in enumerate(methods):
 b=bins[(bins.method==meth)&(bins.probability_variant=="raw")].groupby("bin")[["count","confidence_sum","correct_sum"]].sum()
 b=b[b["count"]>0];ax.plot(b.confidence_sum/b["count"],b.correct_sum/b["count"],marker=["o","s","^","D","v"][i],ms=3,label=labels[meth],color=palette[i])
 mass.plot((b.index+.5)/15,b["count"]/b["count"].sum(),color=palette[i],marker=["o","s","^","D","v"][i],ms=3)
ax.plot([0,1],[0,1],"k--",lw=.7);ax.set_ylim(0,1);ax.set_xlim(0,1);ax.set_ylabel("Empirical accuracy");ax.legend(ncol=5,fontsize=7)
title(ax,"Raw reliability: pooled descriptive bin counts (not packet inference)")
mass.set_xlabel("Confidence");mass.set_ylabel("Mass");mass.set_ylim(0,1);fig.tight_layout();save(fig,"reliability_aggregate")
fig,ax=plt.subplots(figsize=(3.5,2.8))
for i,meth in enumerate(methods):
 ax.bar(i,cost.loc[meth,"total_seconds"]*1000,color=palette[i],hatch=["","//","..","xx","++"][i],edgecolor="black",lw=.4)
ax.set_xticks(range(5),[labels[x] for x in methods],fontsize=8);ax.set_ylim(bottom=0);ax.set_ylabel("Total wall time (ms)");ax.set_title("Post-hoc timing replay\n32 receivers; seed 829; three repeats",fontsize=8);save(fig,"compute")
# Full receiver reliability coverage, with no selected receiver panels.
receivers=sorted(bins.receiver.unique())
for variant in ["raw","source_temperature"]:
 for page in range(4):
  fig,axes=plt.subplots(4,2,figsize=(7.5,9.5),sharex=True,sharey=True)
  for ax,receiver in zip(axes.flat,receivers[page*8:(page+1)*8]):
   for i,meth in enumerate(methods):
    b=bins[(bins.receiver==receiver)&(bins.method==meth)&(bins.probability_variant==variant)]
    b=b[b["count"]>0];ax.plot(b.confidence_sum/b["count"],b.correct_sum/b["count"],color=palette[i],marker=["o","s","^","D","v"][i],ms=2,lw=.7,label=labels[meth])
   ax.plot([0,1],[0,1],"k--",lw=.5);ax.set(xlim=(0,1),ylim=(0,1),title="Receiver "+receiver)
  handles,ls=axes.flat[0].get_legend_handles_labels();fig.legend(handles,ls,ncol=5,loc="lower center",bbox_to_anchor=(.5,.005),fontsize=8)
  fig.suptitle("Post-hoc reliability — "+variant.replace("_"," ")+" — all receivers",fontsize=10)
  fig.supxlabel("Confidence",y=.052);fig.supylabel("Empirical accuracy");fig.tight_layout(rect=[.02,.10,1,.96]);save(fig,f"reliability_{variant}_{page+1}")
# Supplementary receiver means, keeps all methods rather than selected receivers.
table("receiver_means",["Receiver"]+[labels[x] for x in methods],
 [[r]+[f"{pivot.loc[r,x]:.4f}" for x in methods] for r in pivot.index])
(m/"figure_manifest.json").write_text(json.dumps({"figures":figures,"pdf_sha256":{x:file_sha(m/"figures"/(x+".pdf")) for x in figures},
 "analysis_sha256":lineage["analysis_sha256"],"receiver_count":32,"evidence":"POST_HOC"},indent=2,sort_keys=True)+"\n")
print(json.dumps({"figures":len(figures),"tables":8,"traceability_rows":len(trace)-7}))
