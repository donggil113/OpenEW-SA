"""Build reviewed BibTeX from prior verified records and publisher-deposited DOI metadata."""
import argparse,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("--literature",type=Path,required=True);p.add_argument("--repository",type=Path,default=Path.cwd());a=p.parse_args()
doc=a.repository/"papers/paper3_reviewer_remediation"
base=(a.repository/"papers/paper3_receiver_adaptation_manuscript/references_verified.bib").read_text()
extra=(doc/"references_additional_verified.bib").read_text()
records=json.loads((a.literature/"bibliography/reference_metadata_manifest.json").read_text())["rows"]
entries=[]
for r in records:
 fields={"author":" and ".join(x["family"]+", "+x.get("given","") for x in r["authors"]),
 "title":r["title"][0],"year":str(r["year"]["date-parts"][0][0]),"doi":r["doi"]}
 kind="inproceedings" if r["key"] in ("oracle","rfchallenges") else "article"
 fields["booktitle" if kind=="inproceedings" else "journal"]=r["container"][0]
 for old,new in (("volume","volume"),("issue","number"),("pages","pages")):
  if r[old]:fields[new]=str(r[old]).replace("-","--") if old=="pages" else str(r[old])
 # Crossref uppercase Brier metadata is normalized in case only, not content.
 if r["key"]=="brier":
  fields["author"]="Brier, Glenn W.";fields["title"]="Verification of Forecasts Expressed in Terms of Probability"
 entries.append("@"+kind+"{"+r["key"]+","+",".join(k+"={"+v+"}" for k,v in fields.items())+"}\n")
bib=base+extra+"".join(entries)
keys=re.findall(r"@\w+\{([^,]+),",bib)
if len(keys)!=31 or len(set(keys))!=31:raise RuntimeError("reference coverage mismatch")
(doc/"references_verified.bib").write_text(bib)
rows=["# Reference verification and requirements","",
"Thirty-one relevant references, not a comprehensive systematic literature review. Original thirteen retain PR89 provenance. Eleven additions use publisher/author proceedings records; seven DOI records are cross-checked with primary publisher/institutional sources and publisher-deposited Crossref metadata. No absent DOI is invented.",
"","| Citation key | Evidence/source | Supports |","|---|---|---|"]
for entry in re.split(r"(?=@\w+\{)",bib):
 if not entry.strip():continue
 key=re.search(r"@\w+\{([^,]+),",entry)[1]
 source=(re.search(r"doi=\{([^}]+)",entry) or re.search(r"url=\{([^}]+)",entry))
 url=("https://doi.org/" if "doi={" in entry else "")+source[1] if source else "Prior PR89 verified publisher record"
 if key in ("rffsurvey","rfmethodology","oracle","ganrxa","rfchallenges","wisig","orbit","shen","shenlora"):purpose="RF task, receiver/channel dependence, dataset or representation scope; not replication of every cited method"
 elif key in ("calibration","evalcal","ovadia","verifiedcal","dirichlet","brier","gneiting"):purpose="Probability-quality definitions, proper scores, calibration limitations; no claim of target-fitted correction"
 elif key=="holm":purpose="Historical multiplicity policy, not a new post-hoc corrected family"
 else:purpose="Method definition, source-only/TTA distinction or evaluation risk; applicability audited separately"
 rows.append("| "+key+" | "+url+" | "+purpose+" |")
rows+=["","SAR author PDF and official commit verify GN support; OpenReview intermittently presents browser verification. No access control was bypassed. SHOT source-training contract was read before exclusion. GAN-RXA is discussed as prior RF work, not implemented from its title. EATA and Dirichlet calibration contextualize the boundary, not additions to the method grid.",
"","Reference selection is not evidence that the bibliography is exhaustive or that all retraction databases were queried. Human authors should complete their final reference/retraction screening at submission."]
(doc/"reference_requirements.md").write_text("\n".join(rows)+"\n")
print(json.dumps({"references":len(keys)}))
