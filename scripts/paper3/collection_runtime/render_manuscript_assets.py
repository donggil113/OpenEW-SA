"""Generate IEEE assets only from committed, hash-verified small frozen summaries."""
from pathlib import Path
import argparse,hashlib,json,textwrap
from matplotlib.ticker import NullLocator
import numpy as np,pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({"font.family":"DejaVu Serif","font.size":10,"pdf.fonttype":42,"ps.fonttype":42,
                     "axes.spines.top":False,"axes.spines.right":False,"axes.labelcolor":"#20242a",
                     "text.color":"#20242a","axes.edgecolor":"#555555","savefig.facecolor":"white"})
BLUE="#245b78";GOLD="#aa7620";GREY="#666666"
METHODS=["P0","P0_WIDE","DG_CORAL","DG_DANN","DG_GROUPDRO","RX_NORM","T3A","P1","P2","SUP_FT_128"]
LABELS={"P0":"P0 (ERM)","P0_WIDE":"P0-WIDE","DG_CORAL":"CORAL","DG_DANN":"DANN","DG_GROUPDRO":"GroupDRO",
        "RX_NORM":"RX-NORM","T3A":"T3A","P1":"Mean context (P1)","P2":"Attentive context (P2)",
        "SUP_FT_128":"Supervised oracle","P2_SHUFFLED":"P2-SHUFFLED","P2_NULL":"P2-NULL","P2_MISMATCHED_RX":"P2-MISMATCHED"}
def tex(s):return str(s).replace("_",r"\_").replace("&",r"\&")
def table(path,caption,label,columns,rows):
    lines=[r"\begin{table}[t]",r"\centering",r"\caption{"+caption+"}",r"\label{"+label+"}",
           r"\small",r"\begin{tabular}{"+("l"+"r"*(len(columns)-1))+"}",r"\toprule",
           " & ".join(columns)+r"\\",r"\midrule"]
    lines+=[" & ".join(map(str,row))+r"\\" for row in rows]
    lines += [r"\bottomrule",r"\end{tabular}",r"\end{table}"]
    path.write_text("\n".join(lines)+"\n")
def main():
    p=argparse.ArgumentParser();p.add_argument("--manuscript",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();e=a.manuscript/"evidence";latex=a.manuscript/"ieee_latex";fig=latex/"figures";tab=latex/"tables"
    for folder in (fig,tab,a.output):folder.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((e/"source_manifest.json").read_text())
    for name,source in manifest["sources"].items():
        assert hashlib.sha256((e/name).read_bytes()).hexdigest()==source["export_sha256"],name
    read=lambda name:pd.read_csv(e/name,keep_default_na=False)
    summary=read("benchmark_summary.csv")
    avg=read("benchmark_receiver_averaged_results.csv")
    budget=read("support_budget_summary.csv").rename(columns={"method":"model"})
    comp=read("compute_fairness_summary.csv")
    cal=read("calibration_quality_summary.csv")
    family=read("hardware_family_summary.csv")
    inference=json.loads((e/"receiver_level_inference.json").read_text())
    def metric(model,name="macro_f1",stat="mean"):
        return float(summary[(summary.model==model)&(summary.metric==name)][stat].item())
    macros={};mapping={}
    for model in METHODS+["P2_SHUFFLED","P2_NULL","P2_MISMATCHED_RX"]:
        for name in ["macro_f1","ece","accuracy"]:
            key="N"+model.replace("_","")+"".join(s.title() for s in name.split("_"))
            key=key.replace("0","Zero").replace("1","One").replace("2","Two").replace("3","Three").replace("8","Eight")
            # SUP_FT_128 contains digits; strip all remaining digits from command names.
            key="".join(c for c in key if c.isalpha())
            macros[key]=f"{metric(model,name):.6f}"
            mapping[key]={"file":"benchmark_summary.csv","key":{"model":model,"metric":name},"column":"mean"}
    special={"TGain":inference["T3A_MINUS_P0"]["receiver_delta_summary"]["mean"],
             "TLower":inference["T3A_MINUS_P0"]["bootstrap"]["ci95_lower"],
             "TUpper":inference["T3A_MINUS_P0"]["bootstrap"]["ci95_upper"],
             "PGain":metric("P2")-metric("P0"),"PvsT":metric("P2")-metric("T3A")}
    for key,value in special.items():
        macros[key]=f"{value:.6f}";mapping[key]={"file":"receiver_level_inference.json" if key.startswith("T") else "benchmark_summary.csv","key":key,"calculation":"frozen value or difference of receiver means"}
    (latex/"numbers.tex").write_text("\n".join(r"\newcommand{\%s}{%s}"%(key,value) for key,value in macros.items())+"\n")
    (e/"manuscript_number_macros.json").write_text(json.dumps({"values":macros,"sources":mapping},indent=2,sort_keys=True)+"\n")
    table(tab/"protocol.tex","Dataset and primary evaluation protocol.","tab:protocol",["Property","Frozen setting"],
          [["Dataset","WiSig ManyRx, non-equalized"],["Task","6 transmitter classes"],["Physical receivers","32 (7 B210, 16 N210, 9 X310)"],
           ["Receiver split","28 train / 3 validation / 1 test"],["Support / query","128 / remaining disjoint packets"],
           ["P2 peer count","32 from fixed support bank"],["Seeds","829, 1829, 2829, 3829, 4829"]])
    table(tab/"information.tex","Target information regimes. Query features are used only for their own prediction.","tab:info",
          ["Method","Regime","Support","Target labels"],[
              ["ERM / source DG","R0","0","No"],["RX-NORM / T3A","R1","128","No"],["P1 / P2","R1","128","No"],
              ["Supervised FT","R2 oracle","128","Yes"]])
    table(tab/"benchmark.tex","Primary receiver-equal macro-F1. SD is across receivers after seed averaging, not a confidence interval.","tab:bench",
          ["Method","Mean","Receiver SD","ECE"],
          [[tex(m.replace("DG_","").replace("SUP_FT_128","SUP-FT oracle")),f"{metric(m):.6f}",f"{metric(m,stat='std'):.4f}",f"{metric(m,'ece'):.4f}"] for m in METHODS])
    wide=avg.pivot(index="receiver_id",columns="model",values="macro_f1")
    comparisons=[("T3A","P0"),("P2","P0"),("P2","T3A"),("P2","P0_WIDE"),("P2","P2_SHUFFLED"),("P2","P2_MISMATCHED_RX")]
    table(tab/"paired.tex","Paired receiver differences after five-seed averaging. Only T3A--P0 belongs to the later benchmark's one-test family; other entries are descriptive.","tab:paired",
          ["Comparison","Mean delta","Positive / 32"],
          [[tex(x+" - "+y),f"{(wide[x]-wide[y]).mean():+.6f}",str(int(((wide[x]-wide[y])>0).sum()))] for x,y in comparisons])
    table(tab/"budget.tex","Post-hoc common-query support-budget diagnostic. The pool reserves 256 packets; these means are not the primary query-set means.","tab:budget",
          ["Support","T3A","P2","RX-NORM"],[[str(b)]+[f"{float(budget[(budget.model==m)&(budget.support_budget==b)].macro_f1_mean.item()):.4f}" for m in ["T3A","P2","RX_NORM"]] for b in [16,32,64,128,256]])
    rows=[]
    for m,scope in [("P0","Source train"),("P2","Source train"),("T3A","Adapt/eval"),("RX_NORM","Adapt/eval"),("SUP_FT_128","Adapt/eval")]:
        row=comp[comp.model==m].iloc[0]
        rows.append([tex(m.replace("_","-").replace("SUP-FT-128","SUP-FT")),str(int(float(row.parameter_count))),f"{float(row.wall_seconds_mean):.3f}",scope])
    table(tab/"compute.tex","Logged cost boundaries differ. Adapt/eval records reuse source checkpoints; timings are not isolated per-packet latency.","tab:compute",
          ["Method","Parameters","Seconds","Scope"],rows)
    def save(f,name):
        f.savefig(fig/(name+".pdf"),bbox_inches="tight",metadata={"CreationDate":None,"ModDate":None})
        f.savefig(a.output/(name+".png"),dpi=180,bbox_inches="tight")
        plt.close(f)
    def boxes(name,title,texts):
        f,ax=plt.subplots(figsize=(7.1,2.8));ax.set(xlim=(0,1),ylim=(0,1));ax.axis("off");ax.set_title(title,pad=12)
        n=len(texts)
        for i,text in enumerate(texts):
            x=.01+i/n
            ax.add_patch(FancyBboxPatch((x,.13),.88/n,.72,boxstyle="round,pad=0.006",facecolor="white",edgecolor=BLUE,linewidth=1.1))
            wrapped="\n".join(textwrap.fill(line,width=19) for line in text.split("\n"))
            ax.text(x+.44/n,.49,wrapped,ha="center",va="center",fontsize=8)
            if i<n-1:ax.annotate("",xy=(x+1/n-.006,.5),xytext=(x+.88/n+.006,.5),arrowprops={"arrowstyle":"->","color":GREY})
        save(f,name)
    boxes("fig01_design","Disjoint receiver support / query protocol",
          ["Source receivers\nTrain + validation\nNo held-out labels","Held-out receiver\nStable ID hashing\n128 unlabeled support","Separate query pool\nNo query-to-query use\nP0 / T3A / P2","Receiver-level outcome\nFive-seed mean\nEqual receiver weight"])
    f,ax=plt.subplots(figsize=(7.1,4.0));ys=np.arange(len(METHODS))
    ax.errorbar([metric(m) for m in METHODS],ys,xerr=[metric(m,stat="std") for m in METHODS],fmt="o",color=BLUE,capsize=3)
    ax.set(yticks=ys,yticklabels=[LABELS[m] for m in METHODS],xlim=(0,1),xlabel="Macro-F1 (mean ± receiver SD)",title="Receiver-level benchmark")
    ax.invert_yaxis();ax.grid(axis="x",alpha=.2);save(f,"fig02_benchmark")
    f,ax=plt.subplots(figsize=(7.1,3.4));d=wide.T3A-wide.P0;xs=np.arange(len(d))
    ax.bar(xs,d,color=BLUE,edgecolor="#222222",linewidth=.4);ax.axhline(0,color="#222222",linewidth=.8)
    ax.set(xticks=xs,xticklabels=d.index,xlabel="Physical receiver (all 32; fixed identifier order)",ylabel="T3A − P0 macro-F1",title="Paired receiver differences",ylim=(-.10,.10))
    ax.tick_params(axis="x",rotation=90,labelsize=8);save(f,"fig03_receivers")
    f,ax=plt.subplots(figsize=(7.1,3.4))
    for m,color,marker,style in [("T3A",BLUE,"o","-"),("P2",GOLD,"s","--"),("RX_NORM",GREY,"^",":")]:
        v=budget[(budget.model==m)&(budget.support_budget>0)].sort_values("support_budget")
        ax.plot(v.support_budget,v.macro_f1_mean,label=LABELS[m],color=color,marker=marker,linestyle=style)
    ax.axhline(float(budget[(budget.model=="SOURCE_NORM")&(budget.support_budget==0)].macro_f1_mean.item()),color=GREY,linestyle="-.",label="Source norm, no support")
    ax.set(xscale="log",xticks=[16,32,64,128,256],xticklabels=["16","32","64","128","256"],ylim=(0,1),
           xlabel="Unlabeled support packets (fixed measured budgets)",ylabel="Receiver-equal macro-F1",title="Support-budget diagnostic (common query pool)")
    ax.xaxis.set_minor_locator(NullLocator())
    ax.legend(loc="lower right",fontsize=9);save(f,"fig04_budget")
    f,axes=plt.subplots(1,2,figsize=(7.1,3.4))
    for m,color,marker in [("P0",GREY,"o"),("T3A",BLUE,"^"),("P2",GOLD,"s")]:
        v=avg[avg.model==m];axes[0].scatter(v.accuracy,v.ece,label=m,s=15,facecolors="none",edgecolors=color,marker=marker)
    axes[0].set(xlim=(0,1),ylim=(0,.4),xlabel="Receiver accuracy",ylabel="ECE (lower is better)",title="All receivers");axes[0].legend(fontsize=8)
    x=np.arange(len(cal));axes[1].bar(x-.16,cal.ece_mean,width=.32,color=BLUE,label="ECE")
    axes[1].bar(x+.16,cal.nll_mean,width=.32,color="white",edgecolor=GOLD,hatch="//",label="NLL")
    axes[1].set(xticks=x,xticklabels=[LABELS[m] for m in cal.model],ylim=(0,1),title="Mean scores (distinct scales)")
    axes[1].tick_params(axis="x",rotation=60,labelsize=8);axes[1].legend(fontsize=8)
    f.suptitle("Classification and probability calibration");f.tight_layout();save(f,"fig05_calibration")
    f,axes=plt.subplots(1,2,figsize=(7.1,3.2))
    for ax,ms,title in [(axes[0],["P0","P2"],"Source training records"),(axes[1],["T3A","RX_NORM","SUP_FT_128"],"Reused-checkpoint\nadapt/eval records")]:
        vals=[float(comp[comp.model==m].wall_seconds_mean.item()) for m in ms]
        ax.bar(np.arange(len(ms)),vals,color=BLUE,edgecolor="#222222",linewidth=.4)
        ax.set(xticks=np.arange(len(ms)),xticklabels=[LABELS[m] for m in ms],ylabel="Mean recorded seconds",title=title)
        ax.tick_params(axis="x",rotation=25,labelsize=8);ax.set_ylim(0,max(vals)*1.25)
    f.suptitle("Compute accounting: different timing scopes");f.tight_layout();save(f,"fig06_compute")
    f,ax=plt.subplots(figsize=(7.1,3.2));families=["B210","N210","X310"];x=np.arange(3)
    for off,m,color,hatch in [(-.18,"T3A",BLUE,None),(.18,"P2","white","//")]:
        vals=[float(family[(family.model==m)&(family.hardware_family==h)].delta_from_p0.item()) for h in families]
        ax.bar(x+off,vals,.36,label=m,color=color,edgecolor=GREY,hatch=hatch)
    ax.axhline(0,color=GREY,lw=.8);ax.set(xticks=x,xticklabels=["B210 (7)","N210 (16)","X310 (9)"],ylim=(-.04,.04),
        ylabel="Method − P0 macro-F1",title="Hardware-family descriptions (not family-level inference)")
    ax.legend();save(f,"fig07_hardware")
    boxes("fig08_progression","Evidence progression: no independent replication yet",
          ["PR84: initial context study\nGrouped receiver holdouts\nDifferent class set","PR85: methods remediation\nDisjoint support / query\nP2 neutral; T3A stronger","PR87–88: diagnostics\nReuse frozen V2 evidence\nBudget / oracle / costs","Next required evidence\nIndependent lawful data\nAcquired support episodes"])
    # Full receiver × seed lookup: compact rows, all methods, no packet data.
    seeds=read("benchmark_receiver_seed_results.csv")
    pivot=seeds.pivot(index=["receiver_id","seed"],columns="model",values="macro_f1")
    cols=["P0","T3A","P2","P0_WIDE","P1","RX_NORM","DG_CORAL","DG_DANN","DG_GROUPDRO","SUP_FT_128"]
    lines=[r"\small",r"\begin{longtable}{ll"+"r"*len(cols)+"}",r"\caption{All primary receiver--seed macro-F1 values (six decimals).}\\",
           "Receiver & Seed & "+" & ".join(tex(x) for x in cols)+r"\\ \hline \endfirsthead",
           "Receiver & Seed & "+" & ".join(tex(x) for x in cols)+r"\\ \hline \endhead"]
    for (rx,seed),row in pivot.iterrows():
        lines.append(tex(rx)+" & "+str(seed)+" & "+" & ".join(f"{row[m]:.6f}" for m in cols)+r"\\")
    lines.append(r"\end{longtable}")
    (latex/"supplementary"/"receiver_seed_table.tex").parent.mkdir(parents=True,exist_ok=True)
    (latex/"supplementary"/"receiver_seed_table.tex").write_text("\n".join(lines)+"\n")
    print(json.dumps({"figures":8,"tables":6,"macro_count":len(macros),"source_rows":len(seeds)}))
if __name__=="__main__":main()
