"""Static manuscript/release checks plus optional PDF technical and rendering audit."""
import argparse,json,re,subprocess
from pathlib import Path
from openew.paper3.reviewer_remediation.contracts import file_sha
p=argparse.ArgumentParser();p.add_argument("--repository",type=Path,default=Path.cwd());p.add_argument("--pdf-root",type=Path);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
repo=a.repository;doc=repo/"papers/paper3_reviewer_remediation";release=repo/"papers/paper3_receiver_adaptation_manuscript/reproducibility_release"
bib=(doc/"references_verified.bib").read_text();keys=set(re.findall(r"@\w+\{([^,]+),",bib))
text="\n".join(x.read_text() for x in (doc/"manuscript").rglob("*.tex"))
cited={k for group in re.findall(r"\\cite\{([^}]+)\}",text) for k in group.split(",")}
assert not cited-keys,(cited-keys)
assert len(keys)==31
bad=[]
for path in release.rglob("*"):
 if not path.is_file():continue
 content=path.read_text()
 for pattern in [r"/mnt/[a-z]/",r"/home/[^/]+/",r"[A-Z]:\\Users\\",r"ghp_[A-Za-z0-9]{20,}",r"sk-[A-Za-z0-9]{30,}",r"BEGIN.*PRIVATE KEY"]:
  if re.search(pattern,content):bad.append(str(path.relative_to(repo))+":"+pattern)
assert not bad,bad
report={"status":"PASS","references":len(keys),"cited_references":len(cited),"undefined_citations":list(cited-keys),
 "private_path_or_secret_matches":bad,"manuscript_figures":14,"manuscript_tables":8,"pdfs":{}}
a.output.mkdir(parents=True,exist_ok=False)
if a.pdf_root:
 render=a.output/"pages";render.mkdir()
 for name in ["main_tmlcn","supplementary","main_access"]:
  pdf=a.pdf_root/(name+".pdf")
  if not pdf.exists():continue
  info=subprocess.check_output(["pdfinfo",str(pdf)],text=True)
  fonts=subprocess.check_output(["pdffonts",str(pdf)],text=True)
  log=(a.pdf_root/"source"/(name+".log")).read_text(errors="replace")
  rows=fonts.splitlines()[2:];emb=[]
  for row in rows:
   match=re.search(r"\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$",row)
   if match:emb.append(match[1]=="yes")
  result={"pages":int(re.search(r"Pages:\s+(\d+)",info)[1]),"paper_size":re.search(r"Page size:\s+([^\n]+)",info)[1],
   "all_fonts_embedded":bool(emb) and all(emb),"type3_fonts":len(re.findall(r"Type 3",fonts)),
   "overfull_boxes":len(re.findall("Overfull",log)),"underfull_boxes":len(re.findall("Underfull",log)),
   "undefined_references":len(re.findall(r"Reference .* undefined",log)),
   "undefined_citations":len(re.findall(r"Citation .* undefined",log)),"sha256":file_sha(pdf)}
  assert result["all_fonts_embedded"] and result["type3_fonts"]==0,result
  assert result["undefined_references"]==result["undefined_citations"]==0,result
  subprocess.run(["pdftoppm","-r","85","-png",str(pdf),str(render/name)],check=True,capture_output=True)
  report["pdfs"][name]=result
(a.output/"audit.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
print(json.dumps(report,indent=2))
