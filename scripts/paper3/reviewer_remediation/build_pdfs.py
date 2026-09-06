"""Build two venue variants from shared scientific source; third-party template stays external."""
import argparse,hashlib,json,shutil,subprocess,zipfile
from pathlib import Path,PurePosixPath
p=argparse.ArgumentParser();p.add_argument("--repository",type=Path,default=Path.cwd());p.add_argument("--output",type=Path,required=True);p.add_argument("--access-template",type=Path);a=p.parse_args()
doc=a.repository/"papers/paper3_reviewer_remediation";stage=a.output/"source"
a.output.mkdir(parents=True,exist_ok=False);shutil.copytree(doc/"manuscript",stage)
shutil.copyfile(doc/"references_verified.bib",stage/"references.bib")
targets=["main_tmlcn","supplementary"]
if a.access_template:
 expected="60c7efc9db8ac9e8bdb31c550ad4e03cb6f258a878ececc0bc690b6203e45a67"
 if hashlib.sha256(a.access_template.read_bytes()).hexdigest()!=expected:raise RuntimeError("unverified IEEE template")
 with zipfile.ZipFile(a.access_template) as archive:
  for info in archive.infolist():
   path=PurePosixPath(info.filename)
   if path.is_absolute() or ".." in path.parts or (info.external_attr>>16)&0o170000==0o120000:raise RuntimeError("unsafe template member")
   if path.suffix in (".cls",".sty",".map",".fd",".pfb",".tfm") or path.name in ("logo.png","notaglinelogo.png","bullet.png"):
    (stage/path.name).write_bytes(archive.read(info))
 targets.append("main_access")
for target in targets:
 result=subprocess.run(["latexmk","-pdf","-interaction=nonstopmode","-halt-on-error",target+".tex"],cwd=stage,capture_output=True,text=True)
 (a.output/(target+"_build.log")).write_text(result.stdout+result.stderr)
 if result.returncode:raise RuntimeError("LaTeX failed: "+target+"; inspect build log")
 shutil.copyfile(stage/(target+".pdf"),a.output/(target+".pdf"))
print(json.dumps({"status":"BUILT","targets":targets,"access_template_vendored":False}))
