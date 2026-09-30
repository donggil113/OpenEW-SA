"""Retrieve DOI registry metadata for manually primary-source-verified references."""
import argparse,json,urllib.request,urllib.parse
from datetime import datetime,timezone
from pathlib import Path
from openew.paper3.reviewer_remediation.contracts import create_once,file_sha
DOIS={
"rffsurvey":"10.1016/j.comnet.2022.109455",
"rfmethodology":"10.1109/MCOM.001.2200695",
"oracle":"10.1109/INFOCOM.2019.8737463",
"ganrxa":"10.1109/TCCN.2023.3329012",
"rfchallenges":"10.1109/IWCMC61514.2024.10592579",
"gneiting":"10.1198/016214506000001437",
"brier":"10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2"}
p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
rows=[]
for key,doi in DOIS.items():
    url="https://api.crossref.org/works/"+urllib.parse.quote(doi,safe="")
    req=urllib.request.Request(url,headers={"User-Agent":"OpenEW-SA-bibliography-audit/1.0"})
    with urllib.request.urlopen(req,timeout=30) as response:body=json.loads(response.read())
    message=body["message"];destination=a.output/(key+".json")
    create_once(destination,body)
    row={"key":key,"doi":doi,"title":message.get("title"),"authors":message.get("author"),
         "publisher":message.get("publisher"),"container":message.get("container-title"),
         "year":message.get("published"),"volume":message.get("volume"),"issue":message.get("issue"),
         "pages":message.get("page"),"source_url":url,"sha256":file_sha(destination)}
    rows.append(row)
create_once(a.output/"reference_metadata_manifest.json",{"utc":datetime.now(timezone.utc).isoformat(),"rows":rows})
print(json.dumps(rows,indent=2))
