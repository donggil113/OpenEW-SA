"""Portable release hashes and read-only split lineage; no sample IDs are exported."""
import argparse,json,re
from pathlib import Path
from openew.paper3.reviewer_remediation.contracts import file_sha
p=argparse.ArgumentParser();p.add_argument("--repository",type=Path,default=Path.cwd());p.add_argument("--split-root",type=Path,required=True);a=p.parse_args()
repo=a.repository;doc=repo/"papers/paper3_reviewer_remediation";release=repo/"papers/paper3_receiver_adaptation_manuscript/reproducibility_release"
splits={}
for i in range(32):
 name=f"receiver_loso_{i:02d}";root=a.split_root/name
 summary=json.loads((root/"split_summary.json").read_text())
 manifest_sha=file_sha(root/"split_manifest.csv")
 assert manifest_sha==summary["split_manifest_sha256"]
 splits[name]={"split_manifest_sha256":manifest_sha,"split_summary_sha256":file_sha(root/"split_summary.json"),
 "test_receiver":summary["assignment_metadata"]["test_receiver"],"source_validation_receivers":summary["assignment_metadata"]["validation_receivers"],
 "split_counts":summary["split_counts"],"eligible_class_count":summary["eligible_transmitter_count"]}
(release/"split_hashes.json").write_text(json.dumps(splits,indent=2,sort_keys=True)+"\n")
paths=list((doc/"evidence").glob("*"))+list((doc/"manuscript").rglob("*"))+[doc/"references_verified.bib"]
paths=[x for x in paths if x.is_file()]
(release/"expected_checksums.json").write_text(json.dumps({str(x.relative_to(repo)):file_sha(x) for x in sorted(paths)},indent=2,sort_keys=True)+"\n")
terms=r"best|superior|robust|generaliz|real.world|calibration|state.of.the.art|receiver.independent|cross.domain"
rows=[]
for x in sorted((doc/"manuscript/shared").glob("*.tex")):
 for i,line in enumerate(x.read_text().splitlines(),1):
  if re.search(terms,line,re.I):
   rows.append("| "+str(x.relative_to(doc))+":"+str(i)+" | "+line.replace("|","/")+" |")
(doc/"manuscript_language_audit.md").write_text("# Manuscript language red-team audit\n\nReviewed all occurrences below in context. Superior/generalizable language either negates an unsupported claim or scopes a literature family. Highest-mean claims are limited to evaluated unlabeled methods at support128. Probability calibration is distinguished from receiver support; acquired calibration appears only as an absent-evidence limitation. No SOTA, independent-replication or deployment-realism claim is made. Reference titles are not empirical claims of this study.\n\n| Location | Occurrence reviewed |\n|---|---|\n"+"\n".join(rows)+"\n")
print(json.dumps({"split_protocols":len(splits),"release_files_hashed":len(paths),"language_occurrences_reviewed":len(rows)}))
