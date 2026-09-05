"""Deterministic manuscript evidence, citation, language-inventory and PDF checks."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
import numpy as np,pandas as pd

def audit(root,pdf_root=None):
    root=Path(root);e=root/"evidence";latex=root/"ieee_latex"
    source=json.loads((e/"source_manifest.json").read_text())
    for name,row in source["sources"].items():
        assert hashlib.sha256((e/name).read_bytes()).hexdigest()==row["export_sha256"],name
    frame=pd.read_csv(e/"benchmark_receiver_seed_results.csv",dtype={"receiver_id":str})
    assert len(frame)==2240 and not frame.duplicated(["model","receiver_id","seed"]).any()
    assert frame.receiver_id.nunique()==32 and set(frame.seed)=={829,1829,2829,3829,4829}
    assert np.isfinite(frame[["macro_f1","accuracy","ece"]]).all().all()
    means=frame.groupby(["receiver_id","model"]).macro_f1.mean().unstack()
    delta=means.T3A-means.P0
    infer=json.loads((e/"receiver_level_inference.json").read_text())["T3A_MINUS_P0"]
    assert abs(delta.mean()-infer["receiver_delta_summary"]["mean"])<1e-12
    assert (delta>0).sum()==31
    macros=json.loads((e/"manuscript_number_macros.json").read_text())
    tex=(latex/"numbers.tex").read_text()
    for key,value in macros["values"].items():
        assert r"\newcommand{\%s}{%s}"%(key,value) in tex
        info=macros["sources"][key]
        if isinstance(info["key"],dict):
            v=pd.read_csv(e/info["file"])
            for col,wanted in info["key"].items():v=v[v[col]==wanted]
            assert len(v)==1 and f'{v[info["column"]].item():.6f}'==value
    bib=(latex/"references.bib").read_text()
    assert bib==(root/"references_verified.bib").read_text()
    keys=re.findall(r"@\w+\{\s*([^,]+),",bib)
    assert len(keys)==len(set(keys))==13
    sources=sorted((latex/"sections").glob("*.tex"))+[latex/"main.tex",latex/"supplementary.tex"]
    citations=set()
    language=[];literals=[]
    terms=r"\b(?:state.of.the.art|general\w*|robust\w*|real.world|calibrat\w*|adapt\w*|dynamic|hypergraph|neuro.symbolic|temporal)\b"
    for path in sources:
        text=path.read_text()
        for group in re.findall(r"\\cite\{([^}]+)\}",text):citations.update(group.split(","))
        for index,line in enumerate(text.splitlines(),1):
            if re.search(terms,line,re.I):language.append({"file":str(path.relative_to(root)),"line":index,"text":line})
            if re.search(r"\d",line):literals.append({"file":str(path.relative_to(root)),"line":index,"text":line})
    assert citations<=set(keys) and citations==set(keys)
    assert len(list((latex/"figures").glob("fig*.pdf")))==8
    assert len(list((latex/"tables").glob("*.tex")))==6
    # Full receiver-seed lookup has exactly 160 data rows, all numeric cells generated.
    lookup=(latex/"supplementary"/"receiver_seed_table.tex").read_text()
    assert len(re.findall(r"^\d+-\d+ & \d+ &",lookup,re.M))==160
    papers={}
    if pdf_root:
        pdf_root=Path(pdf_root)
        for name,expected in [("main",9),("supplementary",6),("collection_checklist",1)]:
            path=pdf_root/(name+".pdf")
            info=subprocess.check_output(["pdfinfo",str(path)],text=True)
            fonts=subprocess.check_output(["pdffonts",str(path)],text=True)
            pages=int(re.search(r"Pages:\s+(\d+)",info).group(1));assert pages==expected
            assert "Type 3" not in fonts
            rows=[re.search(r"\s(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$",l) for l in fonts.splitlines()[2:]]
            assert rows and all(r and r.group(1)=="yes" for r in rows)
            log=(pdf_root/(name+".log")).read_text()
            assert not re.search(r"undefined|Overfull|^!",log,re.I|re.M)
            papers[name]={"pages":pages,"page_size":re.search(r"Page size:\s+(.+)",info).group(1),
                "all_fonts_embedded":True,"type3_fonts":0,"overfull":0,"undefined":0,
                "underfull":len(re.findall("Underfull",log)),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    return {"status":"PASS","receivers":32,"seed_rows":2240,"methods":14,"number_macros":len(macros["values"]),
        "references":len(keys),"figures":8,"main_tables":6,"supplement_data_rows":160,"pdfs":papers,
        "language_inventory":language,"numeric_literal_inventory":literals,
        "human_review_required":"Context/negation and structural literals reviewed in claim ledger and structural trace; regex is not semantic proof."}
def main():
    p=argparse.ArgumentParser();p.add_argument("--manuscript",type=Path,required=True);p.add_argument("--pdf-root",type=Path)
    p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    result=audit(a.manuscript,a.pdf_root);a.output.parent.mkdir(parents=True,exist_ok=True)
    if a.output.exists():raise FileExistsError("audit report already exists")
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("language_inventory","numeric_literal_inventory")},indent=2))
if __name__=="__main__":main()
